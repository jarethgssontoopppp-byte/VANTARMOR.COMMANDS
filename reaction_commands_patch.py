from pathlib import Path

MARKER = "# VANTARMOR_REACTION_COMMANDS_PATCH_V1"
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
    # The message_reactions_patch generator recreates the reaction handler every
    # startup. Ensure the spank action uses its own random anime GIF category.
    spank_description = 'description=f"🍑 {message.author.mention} le da una palmadita traviesa a {target.mention}."'
    if spank_description not in source:
        raise RuntimeError("No encontré el embed de ?spank.")
    description_at = source.index(spank_description)
    gif_call = 'random_anime_gif("spank")'
    gif_at = source.find(gif_call, description_at)
    next_handler = source.find('    if command not in ("?kiss", "?slap"):', description_at)
    if next_handler >= 0 and (gif_at < 0 or gif_at > next_handler):
        raise RuntimeError("No encontré el GIF aleatorio dedicado de ?spank.")

    if '    if command not in ("?kiss", "?slap"):' not in source:
        insertion = '    if command not in ("?kiss", "?slap"):\n'
        raise RuntimeError("No encontré el punto de inserción para ?kill.")
    if KILL_HANDLER.strip() not in source:
        source = source.replace('    if command not in ("?kiss", "?slap"):\n', KILL_HANDLER + '    if command not in ("?kiss", "?slap"):\n', 1)
    app_file.write_text(source, encoding="utf-8")


__all__ = ["patch_app_file"]
