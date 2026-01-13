import discord
from discord.ext import commands
from discord import app_commands
import os
import json

DATA_PATH = "Files/Data/Chan_lock/chan_lock_status.json"

def save_status(guild_id, channel_id, status):
	if not os.path.exists(os.path.dirname(DATA_PATH)):
		os.makedirs(os.path.dirname(DATA_PATH))
	try:
		with open(DATA_PATH, "r") as f:
			data = json.load(f)
	except (FileNotFoundError, json.JSONDecodeError):
		data = {}
	data.setdefault(str(guild_id), {})[str(channel_id)] = status
	with open(DATA_PATH, "w") as f:
		json.dump(data, f)

def load_status(guild_id, channel_id):
	try:
		with open(DATA_PATH, "r") as f:
			data = json.load(f)
		return data.get(str(guild_id), {}).get(str(channel_id), None)
	except (FileNotFoundError, json.JSONDecodeError):
		return None

class ChanLock(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@app_commands.command(name="lock", description="Verrouille le salon")
	async def lock(self, interaction: discord.Interaction):
		channel = interaction.channel
		everyone = interaction.guild.default_role
		overwrite = channel.overwrites_for(everyone)
		# Save current status
		prev_status = overwrite.send_messages if overwrite.send_messages is not None else "neutral"
		save_status(interaction.guild.id, channel.id, prev_status)
		# Set permission to False
		overwrite.send_messages = False
		await channel.set_permissions(everyone, overwrite=overwrite)
		await interaction.response.send_message("🔒 Le canal est maintenant verrouillé : @everyone ne peut plus envoyer de messages.", ephemeral=True)

	@app_commands.command(name="unlock", description="Déverrouille le salon")
	async def unlock(self, interaction: discord.Interaction):
		channel = interaction.channel
		everyone = interaction.guild.default_role
		overwrite = channel.overwrites_for(everyone)
		prev_status = load_status(interaction.guild.id, channel.id)
		if prev_status is None or prev_status == "neutral":
			overwrite.send_messages = None
		else:
			overwrite.send_messages = prev_status
		await channel.set_permissions(everyone, overwrite=overwrite)
		await interaction.response.send_message("🔓 Le canal est maintenant déverrouillé : @everyone peut envoyer des messages selon les permissions d'origine.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ChanLock(bot))