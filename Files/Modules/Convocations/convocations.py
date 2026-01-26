import os
import discord
from discord.ext import commands
from discord import app_commands
import json
from datetime import datetime

# ID du salon de tickets pour la convocation
TICKET_CHANNEL_ID = 1397869814218756167
CONVOCATION_CHANNEL_ID = 1416511009668989058

class Convocation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="convoquer", description="Convoquer un ou plusieurs membres pour une raison spécifiée.")
    @app_commands.describe(
        membre="Le premier membre à convoquer.",
        raison="La raison de la convocation.",
        membre2="Un second membre (optionnel).",
        membre3="Un troisième membre (optionnel).",
        membre4="Un quatrième membre (optionnel)."
    )
    # Vérifie si l'utilisateur a l'une des permissions de modération.
    @app_commands.default_permissions(kick_members=True, ban_members=True)
    async def convoquer(
        self,
        interaction: discord.Interaction,
        membre: discord.Member,
        raison: str,
        membre2: discord.Member = None,
        membre3: discord.Member = None,
        membre4: discord.Member = None
    ):
        
        # Création d'une liste des membres à mentionner.
        membres_a_convoquer = [membre]
        if membre2:
            membres_a_convoquer.append(membre2)
        if membre3:
            membres_a_convoquer.append(membre3)
        if membre4:
            membres_a_convoquer.append(membre4)

        # Construction de la chaîne de caractères pour les mentions.
        mentions = " ".join([m.mention for m in membres_a_convoquer])

        # Création du message d'embed.
        embed = discord.Embed(
            title="Convocation",
            description=(
                f"{mentions}, vous avez été convoqué(s) par {interaction.user.mention} pour la raison suivante : **{raison}**.\n\n"
                f"Merci d'ouvrir un ticket dans <#{TICKET_CHANNEL_ID}>."
            ),
            color=discord.Color.red()
        )
        
        dm_embed = discord.Embed(
            title="Convocation",
            description=(
                f"{interaction.user.mention} vous a convoqué pour la raison suivante : **{raison}**.\n\n"
                f"Merci d'ouvrir un ticket dans <#{TICKET_CHANNEL_ID}>."
            ),
            color=discord.Color.blue()
        )
        try:
            await membre.send(embed=dm_embed)
        except discord.Forbidden:
            # Si le membre a désactivé les MPs, le bot en informe l'utilisateur.
            await interaction.response.send_message(f"Impossible d'envoyer un message privé à {membre.mention}. Il a probablement désactivé les MPs.\n La convocation échouée a été ajoutée à la liste visible avec la commande \"/convocations-échouées\"", ephemeral=True)

            # Ajout de la convocation échouée dans le fichier JSON
            convocation_data = {
                "user_id": membre.id,
                "server_id": interaction.guild.id,
                "timestamp": datetime.now().strftime("%d/%m/%Y | %H:%M:%S")
            }

            convocations_file = os.path.join(os.getcwd(), "Files/Data/Convocations/convocations.json")
            os.makedirs(os.path.dirname(convocations_file), exist_ok=True)
            if not os.path.exists(convocations_file):
                with open(convocations_file, "w", encoding="utf-8") as file:
                    json.dump({}, file, indent=4)

            try:
                with open(convocations_file, "r", encoding="utf-8") as file:
                    convocations = json.load(file)
            except (FileNotFoundError, json.JSONDecodeError):
                convocations = []

            # Assurez-vous que 'convocations' est une liste
            if not isinstance(convocations, list):
                convocations = []

            convocations.append(convocation_data)

            with open(convocations_file, "w", encoding="utf-8") as file:
                json.dump(convocations, file, indent=4)

            return
        
        # 3. Répond à l'interaction pour confirmer que le message a été envoyé.
        await interaction.response.send_message("Demande envoyée !", ephemeral=True)

        # Récupère le salon de convocation
        convocation_channel = self.bot.get_channel(CONVOCATION_CHANNEL_ID)

        # Vérifie si le salon existe avant d'envoyer le message
        if convocation_channel:
            # Envoie l'embed dans le salon de convocation
            await convocation_channel.send(embed=embed)
            # Répond à l'interaction pour confirmer l'envoi
            await interaction.response.send_message("La convocation a été envoyée avec succès !", ephemeral=True)
        else:
            # Gère le cas où le salon de convocation n'est pas trouvé
            # Ensure interaction is not responded to twice
            if interaction.response.is_done():
                await interaction.followup.send("Le salon de convocation est introuvable. Veuillez vérifier l'ID.", ephemeral=True)
            else:
                await interaction.response.send_message("Le salon de convocation est introuvable. Veuillez vérifier l'ID.", ephemeral=True)

    @app_commands.command(name="convocations-échouées", description="Vérifie les convocations échouées (MP).")
    @app_commands.describe(
        membre="Vérifier les convocations échouées pour ce membre."
    )
    @app_commands.default_permissions(kick_members=True, ban_members=True)
    async def convocations_echouees(
        self,
        interaction: discord.Interaction,
        membre: discord.Member = None
    ):
        convocations_file = "Files/Data/Convocations/convocations.json"
        
        try:
            with open(convocations_file, "r", encoding="utf-8") as file:
                convocations = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            convocations = []

        # Filtrer les convocations pour le serveur actuel
        server_convocations = [c for c in convocations if c["server_id"] == interaction.guild.id]

        if membre:
            # Filtrer les convocations pour le membre spécifié dans le serveur actuel
            filtered_convocations = [c for c in server_convocations if c["user_id"] == membre.id]
            if not filtered_convocations:
                await interaction.response.send_message(f"Aucune convocation échouée trouvée pour {membre.mention} dans ce serveur.", ephemeral=True)
                return
            
            message_lines = [f"Convocations échouées pour {membre.mention} dans ce serveur:"]
            for convocation in filtered_convocations:
                timestamp = convocation["timestamp"]
                message_lines.append(f"- Date: {timestamp}")
            
            await interaction.response.send_message("\n".join(message_lines), ephemeral=True)
        else:
            if not server_convocations:
                await interaction.response.send_message("Aucune convocation échouée trouvée dans ce serveur.", ephemeral=True)
                return
            
            message_lines = ["Toutes les convocations échouées dans ce serveur:"]
            for convocation in server_convocations:
                user_id = convocation["user_id"]
                timestamp = convocation["timestamp"]
                message_lines.append(f"- Utilisateur ID: {user_id} | Date: {timestamp}")
            
            await interaction.response.send_message("\n".join(message_lines), ephemeral=True)

# La fonction setup est nécessaire pour que la cog soit chargée par le bot.
async def setup(bot):
    await bot.add_cog(Convocation(bot))