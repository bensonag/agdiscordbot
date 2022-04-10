# bot.py
from dis import disco
from multiprocessing.dummy import current_process
import os

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
whitelist_channel = None

def print_all_member(guild):
    members = '\n - '.join([member.name for member in guild.members])
    print(f'Guild Members:\n - {members}')


@client.event
async def on_ready():
    global whitelist_channel
    print(f'{client.user} has connected to Discord!')
    guild = discord.utils.find(lambda g: g.name == GUILD_NAME, client.guilds)
    whitelist_channel = discord.utils.find(lambda c: c.name == WHITELIST_CHANNEL_NAME, guild.channels)
    # print_all_member(guild)


@client.event
async def on_member_update(before, after):
    print('on_member_udate')
    print(f'name: {before.name}')
    print(f'old roles: {before.roles}, new roles: {after.roles}')
    if is_adding_whitelist_role_event(before, after):
        await whitelist_channel.send(f'welcome to the channel, {before.name}, now leave your address')
        # dm_channel = before.dm_channel
        # if dm_channel == None:
        #     print('channel == None, creating a new dm channel')
        #     dm_channel = await before.create_dm()
        # await dm_channel.send('hello, send me your address')


def is_adding_whitelist_role_event(before, after):
    print('is_add_whitelist_role_event')
    roles = set(after.roles) - set(before.roles)
    print(roles)
    return len(roles) == 1 and roles.pop().name == WHITELIST_ROLE_NAME

@client.event
async def on_member_join(member):
    await member.create_dm()
    await member.dm_channel.send(
        f'Hi {member.name}, welcome to my Discord server!'
    )

@client.event
async def on_message(message):
    print('on_message')    
    if message.author == client.user:
        return
    if message.content.lower() == 'ping!':
        await message.channel.send('pong!')
    if isinstance(message.channel, discord.DMChannel):
        try_collect_address(message)

def try_collect_address(message):
    if has_whitelist_role(message.author.roles) and is_giving_valid_address(message.content):
        write_to_sheet(message.author, message.content)

def is_giving_valid_address(msg):
    return len(msg.split()) == 1

def write_to_sheet(user, address):
    print(f'id: {user.id}, name: {user.name}, address: {address}')
    # TODO: implement this

def has_whitelist_role(roles):
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
