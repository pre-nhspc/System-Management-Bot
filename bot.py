from discord.ext import commands
import re
import sys
import traceback
import typing

from bot_utils import reply, update_admin_user, is_valid_sshkey
import config
from db import db
import user_management

bot = commands.Bot(command_prefix='!')


@bot.event
async def on_ready():
    print(f"Bot '{bot.user.name}' is up and running!")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        pass
    else:
        print('Ignoring exception in command {}:'.format(
            ctx.command), file=sys.stderr)
        traceback.print_exception(
            type(error), error, error.__traceback__, file=sys.stderr)


@bot.check
async def global_check_channel_id(ctx: commands.Context) -> bool:
    """Check that the message is coming from the current listening channel"""
    return ctx.message.channel.id == config.DISCORD_CHANNEL_ID


@bot.command(brief='Just a simple ping')
async def ping(ctx: commands.Context):
    return await reply(ctx, 'pong')


@bot.command(brief='Query binding status')
async def whoami(ctx: commands.Context):
    user = db.get_user_by_discord_id(ctx.author.id)
    if user is None:
        return await reply(ctx, f"You're not bound with a username yet. Use `!bind <username>` to bind it now.")
    else:
        return await reply(ctx, f"You're currently bound with username `{user['username']}`. You have {len(user['ssh_keys'])} ssh public key(s).")


@bot.command(brief='Bind discord account with username')
async def bind(ctx: commands.Context, *, username: typing.Union[str, None]):
    if username is None:
        return await reply(ctx, f"Usage: `!bind <username>`")
    USERNAME_REGEXP = '^[a-z][a-z0-9_-]{0,31}$'
    discord_id = ctx.author.id
    if (user := db.get_user_by_discord_id(discord_id)) is not None:
        current_username = user['username']
        return await reply(ctx, f"You're already bound with username `{current_username}`! Not binding again.")
    if not re.match(USERNAME_REGEXP, username):
        return await reply(ctx, f"Username should match `{USERNAME_REGEXP}`!")
    if user_management.unix_user_exists(username):
        return await reply(ctx, f"The username already exists (or maybe this is an invalid username)!")

    success = user_management.create_ldap_user(username)
    if not success:
        return await reply(ctx, f"Workstation user creation failed QQ")
    is_sysadm = any(
        [role.id in config.SYSADM_ROLE_IDS for role in ctx.author.roles])
    assert db.create_user({
        'discord_id': discord_id,
        'username': username,
        'is_sysadm': is_sysadm,
    })
    assert update_admin_user()
    return await reply(ctx, f"Successfully bound with username `{username}`! Use `!key-add <ssh-public-key>` to add an ssh public key for workstation login.")


@bot.command(brief='Unbind the current user. THIS WILL REMVOE THE HOME DIR!!!')
async def unbind(ctx: commands.Context):
    user = db.get_user_by_discord_id(ctx.author.id)
    if user is None:
        return await reply(ctx, f"You're not bound with any username yet!")
    success = user_management.delete_ldap_user(user['username'])
    if not success:
        return await reply(ctx, f"Unbind failed QQ")
    assert db.delete_user(user)
    assert update_admin_user()
    return await reply(ctx, f"Successfully unbind and removed username `{user['username']}`!")


@bot.command(name='key-add', brief='Add SSH public key')
async def addkey(ctx: commands.Context, *, key: typing.Union[str, None]):
    if key is None:
        return await reply(ctx, f"Usage: `!key-add <ssh-public-key>`")
    key = "".join([s.strip() for s in key.split('\n')])
    user = db.get_user_by_discord_id(ctx.author.id)
    if user is None:
        return await reply(ctx, f"Please first bind with a username using `!bind <username>`!")
    if key in user['ssh_keys']:
        return await reply(ctx, f"The exact same key already exists!")

    if not is_valid_sshkey(key):
        return await reply(ctx, f"This doesn't seem to be a valid public key. Can you try another one?")
    user['ssh_keys'].append(key)

    success = user_management.update_user_sshkey_list(
        user['username'], user['ssh_keys'])
    if not success:
        return await reply(ctx, f"SSH key addition failed QQ")

    assert db.update_user(user)
    return await reply(ctx, f"Successfully added SSH key! Now `ssh {user['username']}@ws.nhspc.cc -p 8822` to access the workstation!")


@bot.command(brief='Change Login Shell')
async def chsh(ctx: commands.Context, *, shell: typing.Union[str, None]):
    VALID_SHELL = ['sh', 'bash', 'zsh']
    if shell is None or shell not in VALID_SHELL:
        return await reply(ctx, f"Usage: `!chsh <shell>`, shell should be one of `{VALID_SHELL}`")
    user = db.get_user_by_discord_id(ctx.author.id)
    if user is None:
        return await reply(ctx, f"Please first bind with a username using `!bind <username>`!")
    success = user_management.update_user_login_shell(user['username'], f'/bin/{shell}')
    if not success:
        return await reply(ctx, f"Login Shell change failed QQ")
    return await reply(ctx, f"Successfully changed Login Shell for user `{user['username']}`. This might need up to a few minutes to take effect.")

if __name__ == '__main__':
    bot.run(config.DISCORD_TOKEN)
