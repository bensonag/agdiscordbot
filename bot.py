# bot.py
from dis import disco
from multiprocessing.dummy import current_process
import os
from typing import Sequence
import sheet
import log
import traceback

import discord
from dotenv import load_dotenv

intents = discord.Intents.default()
intents.members = True
intents.presences = True

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_NAME = os.getenv('GUILD_NAME')

WHITELIST_ROLE_NAME = set(['OG Galactic', 'Planet WL'])
WHITELIST_CHANNEL_NAME = 'whitelistmembers'

client = discord.Client(intents=intents)
logger = log.Logger()
sheet = sheet.Sheet(logger)
guild: discord.Guild = None # Instace of the guild we care about
whitelist_channel: discord.TextChannel = None  # Instance of the whitelist channel


def update_wl_list_to_sheet():
    wl_members = list(filter(lambda m: has_whitelist_role(m), guild.members))
    try:
        sheet.update_wl_list(wl_members)
    except Exception as e:
        logger.error(traceback.format_exc())


@client.event
async def on_ready():
    logger.info(f'{client.user} has connected to Discord!')
    global guild, whitelist_channel
    guild = discord.utils.find(lambda g: g.name == GUILD_NAME, client.guilds)
    whitelist_channel = discord.utils.find(lambda c: c.name == WHITELIST_CHANNEL_NAME, guild.channels)
    update_wl_list_to_sheet()


@client.event
async def on_member_update(before: discord.Member, after: discord.Member):
    if is_adding_whitelist_role_event(before, after):
        try:
            sheet.add_one_entry(after)
        except Exception as e:
            logger.error(traceback.format_exc())
        await whitelist_channel.send(
                f'Welcome Captain <@{before.id}>, we\'re excited to have you on'
                ' our whitelist! You may now enter your wallet address...')
        return
    if is_removing_whitelist_role_event(before, after):
        try:
            sheet.remove_one_entry(after)
        except Exception as e:
            logger.error(traceback.format_exc())
        return


def is_adding_whitelist_role_event(before: discord.Member, after: discord.Member) -> bool:
    return not has_whitelist_role(before) and has_whitelist_role(after)


def is_removing_whitelist_role_event(before: discord.Member, after: discord.Member):
    return has_whitelist_role(before) and not has_whitelist_role(after)


@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return
    if message.content.lower() == 'ping!':
        await message.channel.send('pong!')
    if message.channel is not whitelist_channel:
        return
    if not has_whitelist_role(message.author):
        return
    if is_valid_address(message.content):
        try:
            sheet.record_address(message.author, message.content)
        except Exception as e:
            logger.error(traceback.format_exc())
        await whitelist_channel.send(
                f'Congratulations <@{message.author.id}>, your address ending '
                f'with \'{message.content[-3:]}\' has been recorded into the '
                'Arcade Galaxy database. Our mint is live on May 20th 11AM UTC, '
                'and you can find live information on our website here '
                '(http://arcadegalaxy.space/) Please stay up-to-date with our '
                'Twitter (http://twitter.com/arcadegalaxy_) and interact with '
                'us for giveaway opportunities! If you would like to update '
                'the address, simply type it in again!')
        await message.delete()


def is_valid_address(msg: str):
    if len(msg.split()) != 1:
        return False
    if len(msg) != 42:
        return False
    return msg[:2] == '0x'


def has_whitelist_role(member: discord.Member):
    return any((role.name in WHITELIST_ROLE_NAME for role in member.roles))


client.run(TOKEN)
