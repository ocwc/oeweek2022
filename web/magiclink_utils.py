from magiclink.management.commands.magiclink_clear_logins import Command


def delete_disabled_magic_links():
    cmd = Command()
    cmd.handle()
