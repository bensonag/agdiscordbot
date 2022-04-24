# bot.py
from dis import disco
from multiprocessing.dummy import current_process
import os
from typing import Sequence
import sheet

import discord
from dotenv import load_dotenv

intents = discord.Intents.default()
intents.members = True
intents.presences = True

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_NAME = os.getenv('GUILD_NAME')

WHITELIST_ROLE_NAME = 'whitelistedd'
WHITELIST_CHANNEL_NAME = 'whitelistmembers'

client = discord.Client(intents=intents)
sheet = sheet.Sheet()
guild: discord.Guild = None # Instace of the guild we care about
whitelist_channel: discord.TextChannel = None  # Instance of the whitelist channel


def print_all_member(guild: discord.Guild):
    for member in guild.members:
        print(f'id: {member.id}, name: {member.name}, roles: {member.roles}')

def update_wl_list_to_sheet():
    print('OnReady: updating all WLed users to the sheet.')
    wl_members = list(filter(lambda m: has_whitelist_role(m.roles), guild.members))
    sheet.update_wl_list(wl_members)


@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    global guild, whitelist_channel
    guild = discord.utils.find(lambda g: g.name == GUILD_NAME, client.guilds)
    whitelist_channel = discord.utils.find(lambda c: c.name == WHITELIST_CHANNEL_NAME, guild.channels)
    update_wl_list_to_sheet()
    

@client.event
async def on_member_update(before: discord.Member, after: discord.Member):
    print('on_member_udate')
    print(f'name: {before.name}')
    print(f'old: {before}, new: {after}')
    if is_adding_whitelist_role_event(before, after):
        sheet.add_one_entry(after)
        await whitelist_channel.send(f'welcome to the channel, {before.name}! Now leave your address')
        return
    if is_removing_whitelist_role_event(before, after):
        sheet.remove_one_entry(after)
        return


def is_adding_whitelist_role_event(before: discord.Member, after: discord.Member) -> bool:
    if len(after.roles) - len(before.roles) != 1:
        return False
    role_difference = set(after.roles) - set(before.roles)
    return role_difference.pop().name == WHITELIST_ROLE_NAME


def is_removing_whitelist_role_event(before: discord.Member, after: discord.Member):
    if len(before.roles) - len(after.roles) != 1:
        return False
    role_difference = set(before.roles) - set(after.roles)
    return role_difference.pop().name == WHITELIST_ROLE_NAME


@client.event
async def on_message(message: discord.Message):
    print('on_message')
    if message.author == client.user:
        return
    if message.content.lower() == 'ping!':
        await message.channel.send('pong!')
    if message.channel is whitelist_channel:
        print('msg from whitelist_channel')
        await try_collect_address(message)


async def try_collect_address(message: discord.Message):
    if not has_whitelist_role(message.author.roles):
        return
    if not is_giving_valid_address(message.content):
        return

    result = write_to_sheet(message.author, message.content)
    if result:
        await whitelist_channel.send(f' Thanks {message.author.name}! Your address is recorded.')
        await message.delete()


def is_giving_valid_address(msg: str):
    return len(msg.split()) == 1

def write_to_sheet(user: discord.Member, address: str):
    print(f'id: {user.id}, name: {user.name}, address: {address}')
    return True
    # TODO: implement this

def has_whitelist_role(roles: Sequence[discord.Role]):
    for role in roles:
        if role.name == WHITELIST_ROLE_NAME:
            print('has_whitelist_role: True')
            return True
    print('has_whitelist_role: False')
    return False

client.run(TOKEN)

# TODO: Trigger when admin say 'something'
# TODO: List all members with role 'whitelisted'
# TODO: Write all new whitelisted members to google sheet
# TODO: Read google sheet to understand the list of members without address
# TODO: DM them to collect address
# TODO: Read address from message and write to google sheet
# TODO: Send thank you msg when collecting address

# TODO: Trigger DM when user is added for the role
