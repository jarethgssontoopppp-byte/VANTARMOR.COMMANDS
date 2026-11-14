"""Premium command policy.

Premium is checked by the handlers of features that actually require it;
there is deliberately no blanket Premium gate for ordinary slash commands.
"""
from discord import app_commands

FREE_COMMANDS = frozenset({"lockdown", "filtro-cuentas"})


class PremiumCommandTree(app_commands.CommandTree):
    async def interaction_check(self, interaction):
        return True


__all__ = ["PremiumCommandTree", "FREE_COMMANDS"]
