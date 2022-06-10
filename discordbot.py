import asyncio
import discord
from discord.ext import commands
from discord.ext import tasks
import os
import traceback
import random
from datetime import datetime
from zoneinfo import ZoneInfo

client = commands.Bot(command_prefix="/")
voicevox_key = os.getenv("VOICEVOX_KEY")
token = os.getenv("DISCORD_BOT_TOKEN")


def find(arr, cond):
    return next((el for el in arr if cond(el)), None)


class BotInfo:

    def text_channel(name):
        guild = find(
            client.guilds, (lambda guild: guild.name == BotInfo.GUILD_NAME))
        return find(guild.text_channels, (lambda channel: channel.name == name))

    GUILD_NAME = "inokuchi-gaming"
    member = None


def load_words():
    with open("./goroku.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()
    return [line.strip() for line in lines]


def remove_mention(content):
    strs = content.split(" ")
    mention_removed = strs[1:]
    return " ".join(mention_removed)


words = load_words()


async def member_voice_play(member, text, speaker=14, intonation=1, speed=0.9):

    if member.guild.voice_client is None:
        return

    mp3url = f"https://api.su-shiki.com/v2/voicevox/audio/?text={text}&key={voicevox_key}&speaker={speaker}&intonationScale={intonation}&speed={speed}"
    while member.guild.voice_client.is_playing():
        await asyncio.sleep(0.5)
    source = await discord.FFmpegOpusAudio.from_probe(mp3url)
    member.guild.voice_client.play(source)


@client.event
async def on_voice_state_update(member, before, after):
    if before.channel is None:
        if member.id == client.user.id:
            BotInfo.member = member
            await client.change_presence(activity=discord.Activity(name=f"{after.channel.name}で通話中", type=discord.ActivityType.listening))
            await member_voice_play(member, text="ヴェックスが入室しました")
        else:
            if member.guild.voice_client is None:
                await asyncio.sleep(0.5)
                await after.channel.connect()
            else:
                if member.guild.voice_client.channel is after.channel:
                    await member_voice_play(member, f"{member.name}が入室しました")
    elif after.channel is None:
        if member.guild.voice_client:
            if member.guild.voice_client.channel is before.channel:
                if len(member.guild.voice_client.channel.members) == 1:
                    await asyncio.sleep(0.5)
                    await member.guild.voice_client.disconnect()
                else:
                    member_voice_play(member, f"{member.name}が退室しました")
                    await client.change_presence(activity=discord.Game("League of Legends"))
    elif before.channel != after.channel:
        if member.guild.voice_client:
            if member.guild.voice_client.channel is before.channel:
                if (
                    len(member.guild.voice_client.channel.members) == 1 or member.voice.self_mute
                ):
                    await asyncio.sleep(0.5)
                    await member.guild.voice_client.disconnect()
                    await asyncio.sleep(0.5)
                    await after.channel.connect()


@ client.event
async def on_command_error(ctx, error):
    orig_error = getattr(error, "original", error)
    error_msg = "".join(
        traceback.TracebackException.from_exception(orig_error).format()
    )
    await ctx.send(error_msg)


@ client.listen()
async def on_message(message: discord.Message):

    if message.author.bot:
        return

    if client.user in message.mentions:
        content = remove_mention(message.clean_content)
        await member_voice_play(BotInfo.member, content)
        return


@ client.command()
async def inmu(ctx):
    text = random.choice(words)
    await member_voice_play(BotInfo.member, text)
    return


@ tasks.loop(minutes=1.0)
async def times_loop():
    now = datetime.now(ZoneInfo("Asia/Tokyo")).strftime('%H:%M')
    if now.endswith(':00'):
        hour = now[:2]
        await member_voice_play(BotInfo.member, f"{hour}時です", speaker=19, intonation=1, speed=0.9)
        return


@ client.command()
async def times(ctx):
    now = datetime.now(ZoneInfo("Asia/Tokyo")).strftime('%H:%M')
    hour = now[:2]
    minutes = now[-2:]
    await member_voice_play(BotInfo.member, f"{hour}時{minutes}分です", speaker=19, intonation=1, speed=0.9)
    return


times_loop.start()

client.run(token)
