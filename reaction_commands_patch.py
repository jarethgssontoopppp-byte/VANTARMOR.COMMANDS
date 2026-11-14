from pathlib import Path

MARKER = "# VANTARMOR_REACTION_COMMANDS_PATCH_V1"

HELPERS = r'''# VANTARMOR_REACTION_COMMANDS_PATCH_V1
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
            color=discord.Color.blurple(),
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
    handler = "async def handle_reaction_command(message, content):\n"
    if handler not in source:
        raise RuntimeError("No encontré el manejador de comandos de reacción en app.py.")

    if "class KillRoleplayView(" not in source:
        source = source.replace(handler, HELPERS + "\n\n" + handler, 1)

    # Keep ?kill free: only find its dispatch point and insert it once.
    if KILL_HANDLER.strip() not in source:
        insertion = '    if command not in ("?kiss", "?slap"):\n'
        if insertion not in source:
            raise RuntimeError("No encontré el punto de inserción para ?kill.")
        source = source.replace(insertion, KILL_HANDLER + insertion, 1)

    # Preserve the requested copy and specifically use the anime-spank category,
    # never the generic slap category.
    source = source.replace(
        'description=f"🍑 {message.author.mention} le dio una nalgada a {target.mention}."',
        'description=f"🍑 {message.author.mention} le da una palmadita traviesa a {target.mention}."',
    )
    source = source.replace('random_anime_gif("slap")', 'random_anime_gif("slap")')
    spank_text = 'description=f"🍑 {message.author.mention} le da una palmadita traviesa a {target.mention}."'
    spank_at = source.find(spank_text)
    if spank_at < 0:
        raise RuntimeError("No encontré el embed de ?spank.")
    gif_call = 'random_anime_gif("spank")'
    gif_at = source.find(gif_call, spank_at)
    reply_start = source.find("        await message.reply(\n", spank_at)
    reply_end = source.find("        return True", reply_start) if reply_start >= 0 else -1
    if gif_at < 0 or reply_start < 0 or reply_end < 0:
        raise RuntimeError("No encontré el GIF o la respuesta de ?spank.")
    block = source[reply_start:reply_end]
    if "view=SpankReturnView(message.author, target)" not in block:
        embed_line = "            embed=embed,\n"
        if embed_line not in block:
            raise RuntimeError("No encontré el embed en la respuesta de ?spank.")
        block = block.replace(embed_line, embed_line + "            view=SpankReturnView(message.author, target),\n", 1)
        source = source[:reply_start] + block + source[reply_end:]

    app_file.write_text(source, encoding="utf-8")


__all__ = ["patch_app_file"]
