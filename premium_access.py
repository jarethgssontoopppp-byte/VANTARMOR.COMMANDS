"""Global Premium access gate for Discord application commands."""
from premium_store import is_premium_user

FREE_COMMANDS = frozenset({"lockdown", "filtro-cuentas"})


async def premium_access_check(interaction):
    command = interaction.command
    if command is not None and command.name in FREE_COMMANDS:
        return True
    if is_premium_user(interaction.user.id):
        return True
    await interaction.response.send_message(
        "🔒 Este comando requiere Premium. Activa Premium desde la web de Vantarmor o contacta al equipo.",
        ephemeral=True,
    )
    return False


def install_premium_access(tree):
    """Install the global gate once, so every other slash command requires Premium."""
    if getattr(tree, "premium_access_check_installed", False):
        return
    tree.add_check(premium_access_check)
    tree.premium_access_check_installed = True


__all__ = ["install_premium_access", "premium_access_check", "FREE_COMMANDS"]
