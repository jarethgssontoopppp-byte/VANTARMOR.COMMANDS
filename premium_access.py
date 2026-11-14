"""Premium access policy for Discord application commands."""
from discord import app_commands

from premium_store import is_premium_user

FREE_COMMANDS = frozenset({"lockdown", "filtro-cuentas"})


class PremiumCommandTree(app_commands.CommandTree):
    """CommandTree that rejects non-Premium users before running commands."""

    async def interaction_check(self, interaction):
        command = interaction.command
        if command is not None and command.name in FREE_COMMANDS:
            return True
        if is_premium_user(interaction.user.id):
            return True
        message = "🔒 Este comando requiere Premium. Activa Premium desde la web de Vantarmor o contacta al equipo."
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)
        return False


__all__ = ["PremiumCommandTree", "FREE_COMMANDS"]
