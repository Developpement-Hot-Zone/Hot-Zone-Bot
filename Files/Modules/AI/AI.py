import os
import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import json
from pathlib import Path
import asyncio

# Define the file path for channel persistence
FILE_PATH = Path("Bot NSFW/Files/Data/AI/statut.json")

class ChannelPersistence:
    def __init__(self, file_path):
        self.file_path = file_path
        self._lock = asyncio.Lock()
        self.channels = self._load_channels()

    def _load_channels(self):
        if self.file_path.exists():
            try:
                with self.file_path.open("r", encoding="utf-8") as f:
                    return set(int(x) for x in json.load(f))
            except (json.JSONDecodeError, ValueError):
                print("Erreur lors du chargement des salons activés.")
        return set()

    async def save_channels(self):
        async with self._lock:
            try:
                with self.file_path.open("w", encoding="utf-8") as f:
                    json.dump(list(self.channels), f)
            except Exception as e:
                print(f"Erreur lors de la sauvegarde des salons activés : {e}")

    def add_channel(self, channel_id):
        self.channels.add(int(channel_id))
        asyncio.create_task(self.save_channels())

    def remove_channel(self, channel_id):
        self.channels.discard(int(channel_id))
        asyncio.create_task(self.save_channels())

# Initialize channel persistence after defining the class
channel_persistence = ChannelPersistence(FILE_PATH)

class GeminiCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="gemini-enable", description="Active Gemini dans ce salon ou un salon spécifié")
    async def gemini_enable(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        channel_persistence.add_channel(channel.id)
        await ctx.send(f"Gemini activé dans {channel.mention}")

    @app_commands.command(name="gemini-disable", description="Désactive Gemini dans ce salon ou un salon spécifié")
    async def gemini_disable(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        if channel.id in channel_persistence.channels:
            channel_persistence.remove_channel(channel.id)
            await ctx.send(f"Gemini désactivé dans {channel.mention}")
        else:
            await ctx.send(f"Gemini n'est pas activé dans {channel.mention}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if (
            message.author.bot
            or message.channel.id not in channel_persistence.channels
            or not message.content
        ):
            return
        # Correction de l'URL et du modèle
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": message.content}
                    ]
                }
            ]
        }
        params = {"key": os.getenv("GEMINI_API_KEY")}  # Ensure the API key is loaded from environment variables

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, params=params, json=payload) as resp:
                print(f"Gemini API URL: {resp.url} | Status: {resp.status}")  # Debug
                if resp.status == 200:
                    data = await resp.json()
                    try:
                        gemini_reply = data["candidates"][0]["content"]["parts"][0]["text"]
                    except (KeyError, IndexError):
                        gemini_reply = "Erreur lors de la génération de la réponse."
                else:
                    try:
                        error_data = await resp.json()
                        error_message = error_data.get("error", {}).get("message", "")
                        gemini_reply = f"Erreur API Gemini: {resp.status} - {error_message}"
                    except Exception:
                        gemini_reply = f"Erreur API Gemini: {resp.status}"

        await message.channel.send(gemini_reply)
        # Important: permet aux autres cogs de traiter les commandes/messages
        await self.bot.process_commands(message)

async def setup(bot):
    await bot.add_cog(GeminiCog(bot))