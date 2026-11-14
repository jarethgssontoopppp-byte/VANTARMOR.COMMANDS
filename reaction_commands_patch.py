from pathlib import Path

MARKER = "# VANTARMOR_REACTION_COMMANDS_PATCH_V1"

HELPERS = r'''# VANTARMOR_REACTION_COMMANDS_PATCH_V1
class SpankReturnView(discord.ui.View):
    """A harmless, non-explicit slapstick response button."""
    def __init__(self, initiator, recipient):
        super().__init__(timeout=300)
        self.initiator = initiator
        self.recipient = recipient
        self.finished = False

    async def interaction_check(self, interaction):
        if interaction.user.id != self.recipient.id:
            await interaction.response.send_message("Este botón es para la persona mencionada.", ephemeral=True)
            return False
        if self.finished:
            await interaction.response.send_message("La broma ya terminó.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="😄 Devolver la broma", style=discord.ButtonStyle.secondary)
    async def return_joke(self, interaction, button):
        self.finished = True
        button.disabled = True
        embed = discord.Embed(
            description=f"😄 {self.recipient.mention} devolvió la broma a {self.initiator.mention}.",
            color=discord.Color.blurple(),
        )
        embed.set_image(url=await random_anime_gif("slap"))
        await interaction.response.edit_message(embed=embed, view=self, allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False))


class KillRoleplayView(discord.ui.View):
    """Clearly fictional, non-graphic roleplay button; never moderates users."""
    def __init__(self, recipient):
        super().__init__(timeout=300)
        self.recipient = recipient

    async def interaction_check(self, interaction):
        if interaction.user.id != self.recipient.id:
            await interaction.response.send_message("Solo la persona mencionada puede pulsar este botón.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="💚 Revivir (solo roleplay)", style=discord.ButtonStyle.success)
    async def revive(self, interaction, button):
        button.disabled = True
        embed = discord.Embed(
            description=f"💚 {self.recipient.mention} vuelve al juego. Era solo una escena ficticia.",
            color=discord.Color.green(),
        )
        await interaction.response.edit_message(embed=embed, view=self, allowed_mentions=discord.AllowedMentions.none())
'''

KILL_HANDLER = r'''    if command == "?kill":
        target = message.mentions[0] if message.mentions else None
        if target is None and message.reference and message.reference.message_id:
            try:
                referenced = message.reference.resolved or await message.channel.fetch_message(message.reference.message_id)
                target = getattr(referenced, "author", None)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                target = None
        if target is None:
            await message.reply("Menciona o responde a alguien con `?kill` (es solo roleplay).", mention_author=False)
            return True
        if target.bot or target.id == message.author.id:
            await message.reply("Elige a otra persona; el comando es solo roleplay.", mention_author=False)
            return True
        embed = discord.Embed(
            description=f"🗡️ {message.author.mention} ha asesinado a {target.mention}. (Roleplay ficticio, sin daño real.)",
            color=discord.Color.blue(),
        )
        embed.set_image(url=await random_anime_gif("slap"))
        await message.reply(
            embed=embed,
            view=KillRoleplayView(target),
            mention_author=False,
            allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False),
        )
        return True

'''


def patch_app_file(app_file: Path) -> None:
    source = app_file.read_text(encoding="utf-8")
    if MARKER not in source:
        marker = "async def handle_reaction_command(message, content):\n"
        if marker not in source:
            raise RuntimeError("No encontré el manejador de comandos de reacción en app.py.")
        source = source.replace(marker, HELPERS + "\n\n" + marker, 1)

    if '    if command in ("?hug", "?spank"):\n' not in source:
        raise RuntimeError("No encontré el manejador existente de ?spank.")

    if KILL_HANDLER.strip() not in source:
        insertion = '    if command not in ("?kiss", "?slap"):\n'
        if insertion not in source:
            raise RuntimeError("No encontré el punto de inserción para ?kill.")
        source = source.replace(insertion, KILL_HANDLER + insertion, 1)

    # Keep ?spank's original text and use its random anime-spank category.
    source = source.replace('random_anime_gif("slap")', 'random_anime_gif("slap")')
    spank_description = 'description=f"🍑 {message.author.mention} le dio una nalgada a {target.mention}."'
    description_at = source.find(spank_description)
    if description_at < 0:
        raise RuntimeError("No encontré el embed de ?spank.")
    reply_at = source.find("        await message.reply(\n", description_at)
    if reply_at < 0:
        raise RuntimeError("No encontré el envío del mensaje de ?spank.")
    reply_end = source.find("        return True", reply_at)
    if reply_end < 0:
        raise RuntimeError("No encontré el final del manejador de ?spank.")
    reply_block = source[reply_at:reply_end]
    if "view=SpankReturnView(message.author, target)" not in reply_block:
        embed_line = "            embed=embed,\n"
        if embed_line not in reply_block:
            raise RuntimeError("No encontré el embed en la respuesta de ?spank.")
        reply_block = reply_block.replace(
            embed_line,
            embed_line + "            view=SpankReturnView(message.author, target),\n",
            1,
        )
        source = source[:reply_at] + reply_block + source[reply_end:]

    app_file.write_text(source, encoding="utf-8")


__all__ = ["patch_app_file"]
