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
        if not is_premium_user(message.author.id):
            await message.reply("🔒 `?kill` requiere Premium.", mention_author=False)
            return True
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
            description=f"🎭 {message.author.mention} derrotó dramáticamente a {target.mention} en una escena ficticia. ¡Sin daño real!",
            color=discord.Color.dark_teal(),
        )
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
        helpers = HELPERS.replace(
            "# VANTARMOR_REACTION_COMMANDS_PATCH_V1\n",
            "# VANTARMOR_REACTION_COMMANDS_PATCH_V1\nfrom premium_store import is_premium_user\n\n",
            1,
        )
        source = source.replace(marker, helpers + "\n" + marker, 1)

    handler_marker = '    if command in ("?hug", "?spank"):\n'
    if KILL_HANDLER.strip() not in source:
        insertion = '    if command not in ("?kiss", "?slap"):\n'
        if insertion not in source:
            raise RuntimeError("No encontré el punto de inserción para ?kill.")
        source = source.replace(insertion, KILL_HANDLER + insertion, 1)
    if handler_marker not in source:
        raise RuntimeError("No encontré el manejador existente de ?spank.")

    banana_marker = '    if command == "?banana":\n'
    premium_guard = (
        '    if command in ("?banana", "?spank") and not is_premium_user(message.author.id):\n'
        '        await message.reply("🔒 Este comando requiere Premium.", mention_author=False)\n'
        '        return True\n\n'
    )
    if premium_guard.strip() not in source:
        source = source.replace(banana_marker, premium_guard + banana_marker, 1)

    # Use a non-explicit anime slapstick GIF for spank, and add the recipient-only return button.
    source = source.replace('random_anime_gif("spank")', 'random_anime_gif("slap")')
    spank_reply = (
        '        await message.reply(\n'
        '            embed=embed,\n'
        '            mention_author=False,\n'
        '            allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False),\n'
        '        )\n'
        '        return True\n\n'
        '    if command not in ("?kiss", "?slap"): '
    )
    replacement = (
        '        await message.reply(\n'
        '            embed=embed,\n'
        '            view=SpankReturnView(message.author, target),\n'
        '            mention_author=False,\n'
        '            allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False),\n'
        '        )\n'
        '        return True\n\n'
        '    if command not in ("?kiss", "?slap"): '
    )
    if 'view=SpankReturnView(message.author, target)' not in source:
        if spank_reply not in source:
            raise RuntimeError("No encontré la respuesta de ?spank para añadir el botón.")
        source = source.replace(spank_reply, replacement, 1)
    app_file.write_text(source, encoding="utf-8")


__all__ = ["patch_app_file"]
