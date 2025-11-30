import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import csv

MINIMUM_AGE_FILE = "./Files/Data/Minimum_age/minimum_age.json"
CSV_LOG_FILE = "./Files/Data/Minimum_age/message_status.csv"

class Minimum_age(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.minimum_ages = self.load_minimum_ages()

    def load_minimum_ages(self):
        # Ensure the file exists before attempting to load
        if os.path.exists(MINIMUM_AGE_FILE):
            with open(MINIMUM_AGE_FILE, 'r') as file:
                return json.load(file)
        return {}

    def save_minimum_ages(self):
        # Ensure the directory exists before writing
        os.makedirs(os.path.dirname(MINIMUM_AGE_FILE), exist_ok=True)
        with open(MINIMUM_AGE_FILE, 'w') as file:
            json.dump(self.minimum_ages, file, indent=4)

    @app_commands.command(name="set_minimum_age", description="Définir l'âge minimum d'un compte pour accéder au serveur (admin seulement)")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_minimum_age(self, interaction: discord.Interaction, days: int):
        # Acknowledge the interaction immediately
        await interaction.response.defer()

        self.minimum_ages[str(interaction.guild.id)] = days
        self.save_minimum_ages()
        # Send a follow-up message to avoid indefinite thinking
        await interaction.followup.send(f"L'âge minimum d'un compte pour ce serveur a été défini à {days} jours.")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild_id = str(member.guild.id)
        if guild_id not in self.minimum_ages:
            return

        minimum_days = self.minimum_ages[guild_id]
        account_age = (discord.utils.utcnow() - member.created_at).days

        if account_age < minimum_days:
            try:
                await member.send(f"Votre compte doit avoir au moins {minimum_days} jours pour rejoindre ce serveur. Vous avez été exclu.")
                self.log_message_status(member.id, "OK")
            except discord.Forbidden:
                self.log_message_status(member.id, "FAIL")

            await member.kick(reason=f"Compte trop récent (moins de {minimum_days} jours).")

    def log_message_status(self, member_id, status):
        # Ensure the directory exists before writing
        os.makedirs(os.path.dirname(CSV_LOG_FILE), exist_ok=True)
        file_exists = os.path.exists(CSV_LOG_FILE)
        with open(CSV_LOG_FILE, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            if not file_exists:
                writer.writerow(["Member ID", "Status"])
            writer.writerow([member_id, status])

async def setup(bot):
    await bot.add_cog(Minimum_age(bot))