"""Application command tree: retain only command-specific Premium checks.

Ordinary commands remain available to everyone. Premium-only features enforce
entitlement in their own handlers, so this tree must not impose a blanket gate.
"""
from discord import app_commands

FREE_COMMANDS = frozenset({"lockdown", "filtro-cuentas"})


class PremiumCommandTree(app_commands.CommandTree):
    """Allow commands through to their handlers' own authorization checks."""

    async def interaction_check(self, interaction):
        return True


__all__ = ["PremiumCommandTree", "FREE_COMMANDS"]
