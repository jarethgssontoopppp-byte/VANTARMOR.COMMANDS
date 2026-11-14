from pathlib import Path

IMPORT_LINE = "from premium_security_system import register_security_commands\n"
ACCESS_IMPORT_LINE = "from premium_access import PremiumCommandTree\n"
TREE_LINE = "tree = app_commands.CommandTree(client)\n"
PREMIUM_TREE_LINE = "tree = PremiumCommandTree(client)\n"
REGISTER_LINE = "register_security_commands(tree, client)\n"
OLD_ACCESS_IMPORT_LINE = "from premium_access import install_premium_access\n"
OLD_ACCESS_REGISTER_LINE = "install_premium_access(tree)\n"


def patch_app_file(app_file: Path) -> None:
    source = app_file.read_text(encoding="utf-8")
    import_anchor = "from discord import app_commands\n"
    if IMPORT_LINE not in source:
        if import_anchor not in source:
            raise RuntimeError("No encontré el punto de importación de app_commands en app.py.")
        source = source.replace(import_anchor, import_anchor + IMPORT_LINE, 1)
    if ACCESS_IMPORT_LINE not in source:
        source = source.replace(IMPORT_LINE, IMPORT_LINE + ACCESS_IMPORT_LINE, 1)
    source = source.replace(OLD_ACCESS_IMPORT_LINE, "")

    if PREMIUM_TREE_LINE not in source:
        if TREE_LINE not in source:
            raise RuntimeError("No encontré la creación del árbol de comandos en app.py.")
        source = source.replace(TREE_LINE, PREMIUM_TREE_LINE, 1)
    source = source.replace(OLD_ACCESS_REGISTER_LINE, "")
    if REGISTER_LINE not in source:
        if PREMIUM_TREE_LINE not in source:
            raise RuntimeError("No encontré la creación de PremiumCommandTree en app.py.")
        source = source.replace(PREMIUM_TREE_LINE, PREMIUM_TREE_LINE + REGISTER_LINE, 1)
    app_file.write_text(source, encoding="utf-8")

    # Lockdown and account-age filtering remain free; all other security commands
    # retain the Premium check in their individual handlers.
    security_file = app_file.with_name("premium_security_system.py")
    security_source = security_file.read_text(encoding="utf-8")
    old_guard = 'if not is_premium_user(interaction.user.id):'
    new_guard = (
        'if interaction.command and interaction.command.name not in {"lockdown", "filtro-cuentas"} '
        'and not is_premium_user(interaction.user.id):'
    )
    if old_guard in security_source:
        security_source = security_source.replace(old_guard, new_guard, 1)
    elif new_guard not in security_source:
        raise RuntimeError("No encontré la validación Premium esperada en premium_security_system.py.")
    security_file.write_text(security_source, encoding="utf-8")


__all__ = ["patch_app_file"]
