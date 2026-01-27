import os
import json
import logging
from datetime import datetime, timedelta
import discord
from discord.ext import commands
from discord import app_commands

SANCTIONS_FILE = os.path.join(os.getcwd(), "Files/Data/Moderation/sanctions.json")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_sanctions():
    if not os.path.exists(SANCTIONS_FILE):
        return {}
    with open(SANCTIONS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return {}

def save_sanctions(data):
    with open(SANCTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# Ensure the sanctions file exists
os.makedirs(os.path.dirname(SANCTIONS_FILE), exist_ok=True)
if not os.path.exists(SANCTIONS_FILE):
    with open(SANCTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, indent=4)

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logging.info("Moderation module initialized.")

    async def add_sanction(self, guild_id, user_id, sanction_type, reason, moderator, duration=None):
        sanctions = load_sanctions()
        user_id = str(user_id)
        entry = {
            "guild_id": str(guild_id),
            "type": sanction_type,
            "reason": reason,
            "moderator": str(moderator.id) if hasattr(moderator, "id") else str(moderator),
            "date": datetime.utcnow().isoformat(),
        }
        if duration:
            entry["duration"] = duration
        if user_id not in sanctions:
            sanctions[user_id] = []
        sanctions[user_id].append(entry)
        save_sanctions(sanctions)

    @app_commands.command(name="warn", description="Avertir un membre")
    @app_commands.describe(member="Le membre à avertir", reason="Raison de l'avertissement")
    async def warn(self, interaction: discord.Interaction, member: discord.Member, *, reason: str = "Aucune raison fournie"):
        await self.add_sanction(interaction.guild.id, member.id, "warn", reason, interaction.user)
        await interaction.response.send_message(f"{member.mention} a été averti pour : {reason}", ephemeral=True)

    @app_commands.command(name="sanctions", description="Voir l'historique des sanctions")
    @app_commands.describe(utilisateur="Voir les sanctions d'un autre membre (admin uniquement)")
    async def sanctions(self, interaction: discord.Interaction, utilisateur: discord.Member = None):
        sanctions = load_sanctions()
        user_id = str(utilisateur.id) if utilisateur else str(interaction.user.id)
        if user_id not in sanctions:
            await interaction.response.send_message("Aucune sanction trouvée pour cet utilisateur.", ephemeral=True)
            return

        user_sanctions = sanctions[user_id]
        embed = discord.Embed(title=f"Sanctions pour {utilisateur or interaction.user}", color=discord.Color.red())
        for idx, sanction in enumerate(user_sanctions, start=1):
            embed.add_field(
                name=f"Sanction {idx}",
                value=(
                    f"Type : {sanction['type']}\n"
                    f"Raison : {sanction['reason']}\n"
                    f"Date : {sanction['date']}\n"
                    f"Modérateur : <@{sanction['moderator']}>"
                ),
                inline=False
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderation(bot))