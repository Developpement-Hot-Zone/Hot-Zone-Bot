import discord
from discord.ext import commands
from discord import app_commands
import json
import asyncio
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Welcome(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.data_file = os.path.join(os.getcwd(), "Files/Data/Welcome/welcome_data.json")
		os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
		if not os.path.exists(self.data_file):
			with open(self.data_file, "w") as f:
				json.dump({}, f)
		logging.info("Welcome module initialized.")

	def load_data(self):
		with open(self.data_file, "r") as f:
			return json.load(f)

	def save_data(self, data):
		with open(self.data_file, "w") as f:
			json.dump(data, f, indent=4)

	@app_commands.command(name="welcome-set", description="Configure le message de bienvenue et le salon.")
	async def welcome_set(self, interaction: discord.Interaction, message: str, channel: discord.TextChannel):
		data = self.load_data()
		data[str(interaction.guild.id)] = {"message": message, "channel_id": channel.id}
		self.save_data(data)
		await interaction.response.send_message("Message de bienvenue configuré avec succès !", ephemeral=True)
		logging.info(f"Welcome message set for guild {interaction.guild.id}")

	@commands.Cog.listener()
	async def on_member_join(self, member: discord.Member):
		await asyncio.sleep(30)  # Attend 30 secondes
		if member.guild.get_member(member.id):  # Vérifie si le membre est toujours dans le serveur
			data = self.load_data()
			guild_data = data.get(str(member.guild.id))
			if guild_data:
				channel = member.guild.get_channel(guild_data["channel_id"])
				if channel:
					welcome_message = guild_data["message"].replace("{user}", member.mention)
					await channel.send(welcome_message)
					logging.info(f"Sent welcome message to {member.name} in guild {member.guild.id}")

async def setup(bot):
	await bot.add_cog(Welcome(bot))