import discord
from discord.ext import commands
from discord import app_commands

CHANNEL_ID = 1391884753694752908
REPORT_CHANNEL_ID = 1406007807647551641

class DMRequest(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="demande-mp", description="Demander à un membre en MP avec raison.")
    @app_commands.describe(membre="Membre à contacter", raison="Raison de la demande")
    async def demande_mp(self, interaction: discord.Interaction, membre: discord.Member, raison: str):
        # 1. Vérifie si la commande est utilisée dans le salon autorisé.
        if interaction.channel_id != CHANNEL_ID:
            await interaction.response.send_message("Cette commande ne peut être utilisée que dans le salon autorisé.", ephemeral=True)
            return

        # 2. Envoie le message privé en premier.
        dm_embed = discord.Embed(
            title="Demande de MP",
            description=f"{interaction.user.mention} souhaite vous contacter en MP pour la raison suivante : {raison}.",
            color=discord.Color.blue()
        )
        try:
            await membre.send(embed=dm_embed)
        except discord.Forbidden:
            # Si le membre a désactivé les MPs, le bot en informe l'utilisateur.
            await interaction.response.send_message(f"Impossible d'envoyer un message privé à {membre.mention}. Il a probablement désactivé les MPs.", ephemeral=True)
            return
        
        # 3. Répond à l'interaction pour confirmer que le message a été envoyé.
        await interaction.response.send_message("Demande envoyée !", ephemeral=True)

        # 4. Envoie le message public dans le salon pour le signalement.
        embed = discord.Embed(
            title="Demande de MP",
            description=f"{interaction.user.mention} a demandé à {membre.mention} un MP pour {raison}.\n\n"
                        "Si vous recevez des demandes abusives, n'hésitez pas à réagir avec 🚨 ou à ouvrir un ticket.",
            color=discord.Color.blue()
        )
        msg = await interaction.channel.send(embed=embed)
        await msg.add_reaction("🚨")

        # 5. Définit la fonction de vérification pour la réaction.
        def check(reaction, user):
            return (
                reaction.message.id == msg.id and
                str(reaction.emoji) == "🚨" and
                user.id == membre.id
            )

        # 6. Attend la réaction du membre mentionné pour le signalement.
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=3600, check=check)
        except Exception:
            # Gère l'expiration du temps d'attente.
            pass
        else:
            # 7. Si une réaction est détectée, envoie un message au canal de rapport.
            report_channel = self.bot.get_channel(REPORT_CHANNEL_ID)
            if report_channel:
                await report_channel.send(
                    f"🚨 Signalement de demande abusive par {membre.mention}.\n"
                    f"Demande initiale de {interaction.user.mention} pour la raison : {raison}."
                )

async def setup(bot):
    await bot.add_cog(DMRequest(bot))