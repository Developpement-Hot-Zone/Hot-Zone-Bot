import discord
from discord.ext import commands
from discord import app_commands
import json
import os

class Infos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="infos", description="Affiche la configuration actuelle du serveur.")
    async def infos(self, interaction: discord.Interaction):
        guild = interaction.guild

        # Configuration du module "welcome"
        welcome_data_path = os.path.join(os.path.dirname(__file__), "../../Data/Welcome/welcome_data.json")
        if os.path.exists(welcome_data_path):
            with open(welcome_data_path, "r") as f:
                welcome_data = json.load(f)
            welcome_config = welcome_data.get(str(guild.id), {})
            welcome_status = "Activé" if welcome_config else "Désactivé"
            welcome_channel = f"<#{welcome_config.get('channel_id')}>" if welcome_config else "N/A"
        else:
            welcome_status = "Désactivé"
            welcome_channel = "N/A"

        # Configuration des modules d'intelligence artificielle
        ai_data_path = os.path.join(os.path.dirname(__file__), "../../Data/AI/statut.json")
        if os.path.exists(ai_data_path):
            with open(ai_data_path, "r") as f:
                ai_channels = json.load(f)
            ai_channels_list = [f"<#{channel_id}>" for channel_id in ai_channels]
        else:
            ai_channels_list = []

        # Configuration de l'âge minimum
        minimum_age_path = os.path.join(os.path.dirname(__file__), "../../Data/Minimum_age/minimum_age.json")
        if os.path.exists(minimum_age_path):
            with open(minimum_age_path, "r") as f:
                minimum_age_data = json.load(f)
            minimum_age = minimum_age_data.get(str(guild.id), "Non configuré")
        else:
            minimum_age = "Non configuré"

        # Salons bloqués
        chan_lock_path = os.path.join(os.path.dirname(__file__), "../../Data/Chan_lock/chan_lock_status.json")
        if os.path.exists(chan_lock_path):
            with open(chan_lock_path, "r") as f:
                chan_lock_data = json.load(f)
            locked_channels = [
                f"<#{channel_id}>"
                for channel_id, status in chan_lock_data.get(str(guild.id), {}).items()
                if status is False
            ]
        else:
            locked_channels = []

        # Serveur en lockdown
        lockdown_path = os.path.join(os.path.dirname(__file__), "../../Data/Lockdown/lockdown_perms_backup.json")
        is_lockdown = "Oui" if os.path.exists(lockdown_path) else "Non"

        # Configuration du système d'anniversaires
        birthday_config_path = os.path.join(os.path.dirname(__file__), f"../../Data/Birthday/server_{guild.id}.json")
        if os.path.exists(birthday_config_path):
            with open(birthday_config_path, "r") as f:
                birthday_config = json.load(f)
            birthday_status = "Activé" if birthday_config.get("enabled") else "Désactivé"
            birthday_channel = f"<#{birthday_config.get('channel_id')}>" if birthday_config.get("channel_id") else "N/A"
            birthday_time = birthday_config.get("time", "N/A")
        else:
            birthday_status = "Désactivé"
            birthday_channel = "N/A"
            birthday_time = "N/A"

        # Nombre de commandes disponibles
        total_commands = len(self.bot.tree.get_commands())

        # Nombre de joueurs actifs sur "Actions ou Vérité"
        aov_data_path = os.path.join(os.path.dirname(__file__), "../../Data/AOV/aov_players.json")
        if os.path.exists(aov_data_path):
            with open(aov_data_path, "r") as f:
                aov_data = json.load(f)
            aov_players = len(aov_data.get(str(guild.id), {}))
        else:
            aov_players = 0

        # Nombre de confessions
        confession_counter_path = os.path.join(os.path.dirname(__file__), "../../Data/Confessions/confession_counter.json")
        if os.path.exists(confession_counter_path):
            with open(confession_counter_path, "r") as f:
                confession_data = json.load(f)
            total_confessions = confession_data.get("count", 0)
        else:
            total_confessions = 0

        # Nombre de réponses aux confessions
        if os.path.exists(confession_counter_path):
            with open(confession_counter_path, "r") as f:
                confession_data = json.load(f)
            total_responses = sum(
                count for key, count in confession_data.items() if key.startswith("reponse_")
            )
        else:
            total_responses = 0

        # Nombre de convocations effectuées
        convocations_path = os.path.join(os.path.dirname(__file__), "../../Data/Convocations/convocations.json")
        if os.path.exists(convocations_path):
            with open(convocations_path, "r") as f:
                convocations_data = json.load(f)
            total_convocations = len(convocations_data)
        else:
            total_convocations = 0

        # Nombre de demandes de MP effectuées
        dm_requests_path = os.path.join(os.path.dirname(__file__), "../../Data/DM_request/dm_requests.json")
        if os.path.exists(dm_requests_path):
            with open(dm_requests_path, "r") as f:
                dm_requests_data = json.load(f)
            total_dm_requests = len(dm_requests_data)
        else:
            total_dm_requests = 0

        # Nombre de personnes bannies
        try:
            banned_users = await guild.bans()
            total_banned = len(banned_users)
        except discord.Forbidden:
            total_banned = "Permissions insuffisantes"

        # Création de l'embed
        embed = discord.Embed(
            title=f"Configuration actuelle du serveur : {guild.name}",
            color=discord.Color.blue(),
        )
        embed.add_field(name="Module Welcome", value=f"Statut: {welcome_status}\nSalon: {welcome_channel}", inline=False)
        embed.add_field(name="Modules AI", value=", ".join(ai_channels_list) or "Aucun salon activé", inline=False)
        embed.add_field(name="Âge minimum", value=f"{minimum_age} jours", inline=False)
        embed.add_field(name="Salons bloqués", value=", ".join(locked_channels) or "Aucun", inline=False)
        embed.add_field(name="Serveur en lockdown", value=is_lockdown, inline=False)
        embed.add_field(
            name="Système d'anniversaires",
            value=f"Statut: {birthday_status}\nSalon: {birthday_channel}\nHeure: {birthday_time}",
            inline=False,
        )
        embed.add_field(name="Commandes disponibles", value=str(total_commands), inline=False)
        embed.add_field(name="Joueurs actifs (AOV)", value=str(aov_players), inline=False)
        embed.add_field(name="Confessions", value=str(total_confessions), inline=False)
        embed.add_field(name="Réponses aux confessions", value=str(total_responses), inline=False)
        embed.add_field(name="Convocations", value=str(total_convocations), inline=False)
        embed.add_field(name="Demandes de MP", value=str(total_dm_requests), inline=False)
        embed.add_field(name="Personnes bannies", value=str(total_banned), inline=False)

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Infos(bot))