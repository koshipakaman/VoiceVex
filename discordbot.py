import asyncio
import discord
from discord.ext import commands
from discord.ext import tasks
from discord import Colour
import os
import traceback
import random
import string
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo

client = commands.Bot(command_prefix="/")
voicevox_key = os.getenv("VOICEVOX_KEY")
token = os.getenv("DISCORD_BOT_TOKEN")


def find(arr, cond):
    return next((el for el in arr if cond(el)), None)


def index_list(length):

    if length < 11:
        return list(range(1, length + 1))

    return string.ascii_lowercase[:length]


def date_range(start, end):
    for n in range((end - start).days + 1):
        yield start + timedelta(n)


def str_to_date(str):
    year = datetime.now(ZoneInfo("Asia/Tokyo")).year
    month, day = tuple(str.split("/"))
    return date(year, int(month), int(day))


def date_to_str(date):
    return f"{date.month}/{date.day}"


def index_emoji(index):

    if isinstance(index, int):
        return f":{DISCORD_EMOJI_NAME[index]}:"

    else:
        return f":regional_indicator_{index}:"


def load_words():
    with open("./goroku.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()
    return [line.strip() for line in lines]


def remove_mention(content):
    strs = content.split(" ")
    mention_removed = strs[1:]
    return " ".join(mention_removed)


DISCORD_EMOJI_NAME = {
    1: "one",
    2: "two",
    3: "three",
    4: "four",
    5: "five",
    6: "six",
    7: "seven",
    8: "eight",
    9: "nine",
    10: "keycap_ten",
}


class BotInfo:

    def text_channel(name):
        guild = find(
            client.guilds, (lambda guild: guild.id == BotInfo.GUILD_ID))
        return find(guild.text_channels, (lambda channel: channel.name == name))

    GUILD_ID = "580377387968102431"
    member = None


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
            await client.change_presence(activity=discord.Activity(name=f"{after.channel.name}", type=discord.ActivityType.playing))
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
                    await client.change_presence(activity=discord.Game("League of Legends"))
                else:
                    member_voice_play(member, f"{member.name}が退室しました")
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


@client.command()
async def schedule(ctx, begin, end, description="日程調整"):

    begin_date = str_to_date(begin)
    end_date = str_to_date(end)

    if begin_date > end_date:
        await ctx.channel.send("schedule(): begin date > end date")
        return

    dates = list(date_range(begin_date, end_date))
    dates = [date_to_str(date) for date in dates]
    indexes = index_list(len(dates))

    embed = discord.Embed(
        title="Scheduler",
        description=description,
        color=Colour.blue()
    )
    for index, _date in zip(indexes, dates):
        # ゼロ幅スペースを入れないとHTTPExceptionになる
        embed.add_field(name=f"{index}. {_date}", value='\u200b', inline=False)

    embed.set_footer(text=f"created {datetime.now().date()}")

    await ctx.send(embed=embed)
    last_message = ctx.channel.last_message

    for index in indexes:
        await last_message.add_reaction(index_emoji(index))


@client.command()
async def indexEmoji(ctx):

    await ctx.channel.send(index_emoji(1))
    await ctx.channel.send(index_emoji("a"))
    await ctx.channel.last_message.add_reaction(index_emoji(1))

times_loop.start()

client.run(token)
