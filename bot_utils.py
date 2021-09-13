from discord.ext import commands
import subprocess

from db import db
import user_management


async def reply(ctx: commands.Context, msg: str):
    """Send message and mention the author"""
    return await ctx.send(f'{ctx.author.mention} {msg}')


def is_valid_sshkey(key: str) -> bool:
    """Return true if the key seems to be a valid one (using `ssh-keygen`)"""
    r = subprocess.run(['ssh-keygen', '-lf', '-'], input=key.encode('utf-8'),
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return r.returncode == 0


def update_admin_user() -> bool:
    """Get list of admin user from DB and update in LDAP, return True if success"""
    admin_users = db.get_all_sysadm_user()
    usernames = [user['username'] for user in admin_users]
    success = user_management.update_group_member_list(
        'nhspc-sysadm', usernames)
    return success
