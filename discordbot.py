import asyncio
import discord
from discord.ext import commands
import os
import traceback
import random

client = commands.Bot(command_prefix="/")
voicevox_key = os.getenv("VOICEVOX_KEY")
voicevox_speaker = os.getenv("VOICEVOX_SPEAKER", default="14")
token = os.getenv("DISCORD_BOT_TOKEN")


def bot_voice_client():
    voices = client.voice_clients
    for vc in voices:
        if vc.user.id == client.user.id:
            return vc


def load_words():
    with open("./goroku.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()
    return [line.strip() for line in lines]


words = load_words()


async def member_voice_play(member, text, intonation=1, speed=0.9):
    mp3url = f"https://api.su-shiki.com/v2/voicevox/audio/?text={text}&key={voicevox_key}&speaker={voicevox_speaker}&intonationScale={intonation}&speed={speed}"
    while member.guild.voice_client.is_playing():
        await asyncio.sleep(0.5)
    source = await discord.FFmpegOpusAudio.from_probe(mp3url)
    member.guild.voice_client.play(source)


async def voice_client_play(vc, text, intonation=1, speed=0.9):
    mp3url = f"https://api.su-shiki.com/v2/voicevox/audio/?text={text}&key={voicevox_key}&speaker={voicevox_speaker}&intonationScale={intonation}&speed={speed}"
    while vc.is_playing():
        await asyncio.sleep(0.5)
    source = await discord.FFmpegOpusAudio.from_probe(mp3url)
    vc.play(source)


@client.event
async def on_voice_state_update(member, before, after):
    if before.channel is None:
        if member.id == client.user.id:
            await member_voice_play(member, text="ヴェックスが入室しました")
        else:
            if member.guild.voice_client is None:
                await asyncio.sleep(0.5)
                await after.channel.connect()
            else:
                if member.guild.voice_client.channel is after.channel:
                    await member_voice_play(member, text=f"{member.name}が入室しました")
    elif after.channel is None:
        if member.guild.voice_client:
            if member.guild.voice_client.channel is before.channel:
                if len(member.guild.voice_client.channel.members) == 1:
                    await asyncio.sleep(0.5)
                    await member.guild.voice_client.disconnect()
                else:
                    member_voice_play(member, text=f"{member.name}が退室しました")
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


@client.event
async def on_command_error(ctx, error):
    orig_error = getattr(error, "original", error)
    error_msg = "".join(
        traceback.TracebackException.from_exception(orig_error).format()
    )
    await ctx.send(error_msg)


async def reply(message):
    await member_voice_play(bot_voice_client(), message.content)


@client.listen
async def on_message(message):
    if client.user in message.mentions:
        await reply(message)


@client.command()
async def inmu(ctx):
    members = client.get_all_members()
    for member in members:
        if member.bot:
            text = random.choice(words)
            await member_voice_play(member, text)


client.run(token)
