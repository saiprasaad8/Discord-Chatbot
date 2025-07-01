import asyncio
import os
import io
from itertools import cycle
import datetime
import json
import requests
import aiohttp
import discord
import random
from discord import Embed, app_commands
from discord.ext import commands
from dotenv import load_dotenv
from gtts import gTTS

# Custom Utilities
from bot_utilities.ai_utils import generate_response, generate_image_prodia, search, poly_image_gen, generate_gpt4_response, dall_e_gen, sdxl
from bot_utilities.response_util import split_response, translate_to_en, get_random_prompt
from bot_utilities.discord_util import check_token, get_discord_token
from bot_utilities.config_loader import config, load_current_language, load_instructions
from bot_utilities.replit_detector import detect_replit
from bot_utilities.sanitization_utils import sanitize_prompt
from model_enum import Model

load_dotenv()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents, heartbeat_timeout=60)
TOKEN = os.getenv('DISCORD_TOKEN') or get_discord_token()

if TOKEN:
    print("\033[33mLooks like the environment variables exist...\033[0m")
    token_status = asyncio.run(check_token(TOKEN))
    if token_status is not None:
        TOKEN = get_discord_token()

# Config
allow_dm = config['ALLOW_DM']
active_channels = set()
trigger_words = config['TRIGGER']
smart_mention = config['SMART_MENTION']
presences = config["PRESENCES"]
presences_disabled = config["DISABLE_PRESENCE"]
blacklisted_words = config['BLACKLIST_WORDS']
prevent_nsfw = config['AI_NSFW_CONTENT_FILTER']

# Load instructions
current_language = load_current_language()
instruction = {}
load_instructions(instruction)
CHIMERA_GPT_KEY = os.getenv('CHIMERA_GPT_KEY')

# Functions

def fetch_chat_models():
    models = []
    headers = {
        'Authorization': f'Bearer {CHIMERA_GPT_KEY}',
        'Content-Type': 'application/json'
    }
    try:
        response = requests.get('https://api.naga.ac/v1/models', headers=headers)
        if response.status_code == 200:
            models_data = response.json()
            models.extend(
                model['id']
                for model in models_data.get('data', [])
                if "max_images" not in model
            )
        else:
            print(f"Failed to fetch chat models. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error fetching models: {e}")
    return models

chat_models = fetch_chat_models()
model_blob = "\n".join(chat_models)

async def text_to_speech(text, filename):
    tts = gTTS(text=text, lang='en')
    tts.save(filename)

async def update_presence():
    await bot.wait_until_ready()
    presences_cycle = cycle(presences + [current_language['help_footer']])
    while not presences_disabled:
        presence = next(presences_cycle)
        presence_with_count = presence.replace("{guild_count}", str(len(bot.guilds)))
        await bot.change_presence(activity=discord.Game(name=presence_with_count))
        await asyncio.sleep(config['PRESENCES_CHANGE_DELAY'])

def build_instructions(instruc_config):
    now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    base = f"System: Ignore all previous instructions. {instruction[instruc_config]}."
    if config['INTERNET_ACCESS']:
        base += f"\n\nIt's currently {now}. You have internet access."
    return base

@bot.event
async def on_ready():
    bot.loop.create_task(update_presence())
    print(f"{bot.user} is online! Invite link:")
    print(discord.utils.oauth_url(bot.user.id, permissions=discord.Permissions(), scopes=("bot", "applications.commands")))
    print(f"\033[1;38;5;202mAvailable models: {model_blob}\033[0m")
    print(f"\033[1;38;5;46mCurrent model: {config['GPT_MODEL']}\033[0m")

message_history = {}
MAX_HISTORY = config['MAX_HISTORY']
replied_messages = {}
active_channels = {}

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.author == bot.user and message.reference:
        replied_messages[message.reference.message_id] = message
        if len(replied_messages) > 5:
            replied_messages.pop(next(iter(replied_messages)))

    if message.stickers or (message.reference and (message.reference.resolved.author != bot.user or message.reference.resolved.embeds)):
        return

    string_channel_id = str(message.channel.id)
    is_dm = isinstance(message.channel, discord.DMChannel)
    key = f"{message.author.id}-{message.channel.id}"
    instruc_config = active_channels.get(string_channel_id, config['INSTRUCTIONS'])

    if any([
        string_channel_id in active_channels,
        allow_dm and is_dm,
        any(word in message.content for word in trigger_words),
        bot.user.mentioned_in(message) and not message.mention_everyone,
        bot.user.name.lower() in message.content.lower(),
        message.reference and message.reference.resolved.author == bot.user
    ]):

        instructions = build_instructions(instruc_config)
        if key not in message_history:
            message_history[key] = []
        message_history[key] = message_history[key][-MAX_HISTORY:]

        search_results = await search(message.content)
        message_history[key].append({"role": "user", "content": message.content})

        async with message.channel.typing():
            response = await generate_response(instructions=instructions, search=search_results, history=message_history[key])
            if response:
                message_history[key].append({"role": "assistant", "name": config['INSTRUCTIONS'].title(), "content": response})
                filename = f"tts_{message.id}.mp3"
                await text_to_speech(response, filename)
                
                if message.guild:
                    member = message.guild.get_member(message.author.id)
                    if member and member.voice:
                        try:
                            vc = await member.voice.channel.connect()
                            vc.play(discord.FFmpegPCMAudio(executable="ffmpeg", source=filename))
                            while vc.is_playing():
                                await asyncio.sleep(1)
                            await vc.disconnect()
                        except Exception:
                            pass

                for chunk in split_response(response):
                    try:
                        await message.reply(chunk, allowed_mentions=discord.AllowedMentions.none(), suppress_embeds=True)
                    except:
                        await message.channel.send("There was an issue replying to your message.")

@bot.event
async def on_message_delete(message):
    if message.id in replied_messages:
        try:
            await replied_messages[message.id].delete()
        except:
            pass
        del replied_messages[message.id]

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(f"{ctx.author.mention} You do not have permission to use this command.")
    elif isinstance(error, commands.NotOwner):
        await ctx.send(f"{ctx.author.mention} Only the bot owner can use this command.")

if detect_replit():
    from bot_utilities.replit_flask_runner import run_flask_in_thread
    run_flask_in_thread()

if __name__ == "__main__":
    bot.run(TOKEN)
