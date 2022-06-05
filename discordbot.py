import asyncio
import discord
from discord.ext import commands
import os
import traceback

client = commands.Bot(command_prefix="/")
voicevox_key = os.getenv("VOICEVOX_KEY")
voicevox_speaker = os.getenv("VOICEVOX_SPEAKER", default="14")
token = os.getenv("DISCORD_BOT_TOKEN")


@client.event
async def on_voice_state_update(member, before, after):
    if before.channel is None:
        if member.id == client.user.id:
            presence = f"ヘルプ | {len(client.voice_clients)}/{len(client.guilds)}サーバー"
            await client.change_presence(activity=discord.Game(name=presence))
        else:
            if member.guild.voice_client is None:
                await asyncio.sleep(0.5)
                await after.channel.connect()
            else:
                if member.guild.voice_client.channel is after.channel:
                    text = member.name + "さんが入室しました"
                    mp3url = f"https://api.su-shiki.com/v2/voicevox/audio/?text={text}&key={voicevox_key}&speaker={voicevox_speaker}&intonationScale=1"
                    while member.guild.voice_client.is_playing():
                        await asyncio.sleep(0.5)
                    source = await discord.FFmpegOpusAudio.from_probe(mp3url)
                    member.guild.voice_client.play(source)
    elif after.channel is None:
        if member.id == client.user.id:
            presence = f"ヘルプ | {len(client.voice_clients)}/{len(client.guilds)}サーバー"
            await client.change_presence(activity=discord.Game(name=presence))
        else:
            if member.guild.voice_client:
                if member.guild.voice_client.channel is before.channel:
                    if len(member.guild.voice_client.channel.members) == 1:
                        await asyncio.sleep(0.5)
                        await member.guild.voice_client.disconnect()
                    else:
                        text = member.name + "さんが退室しました"
                        mp3url = f"https://api.su-shiki.com/v2/voicevox/audio/?text={text}&key={voicevox_key}&speaker={voicevox_speaker}&intonationScale=1"
                        while member.guild.voice_client.is_playing():
                            await asyncio.sleep(0.5)
                        source = await discord.FFmpegOpusAudio.from_probe(mp3url)
                        member.guild.voice_client.play(source)
    elif before.channel != after.channel:
        if member.guild.voice_client:
            if member.guild.voice_client.channel is before.channel:
                if (
                    len(member.guild.voice_client.channel.members) == 1
                    or member.voice.self_mute
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


@client.command()
async def test(ctx):
    text = "てすと"
    mp3url = f"https://api.su-shiki.com/v2/voicevox/audio/?text={text}&key={voicevox_key}&speaker={voicevox_speaker}&intonationScale=1"
    source = await discord.FFmpegOpusAudio.from_probe(mp3url)
    discord.VoiceClient.play(source)


client.run(token)
