import discord
from discord.ext import commands

class OnJoin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        # Récupérer le salon par défaut (premier salon textuel accessible)
        default_channel = next(
            (channel for channel in guild.text_channels if channel.permissions_for(guild.me).send_messages),
            None
        )

        if not default_channel:
            return  # Aucun salon accessible pour envoyer un message

        # Création de l'embed
        embed = discord.Embed(
            title="Salut salut !",
            description=(
                "Merci d'avoir ajouté le bot à votre serveur!\n\n"
				"Pour commencer, utilisez la commande `/help` pour voir toutes les commandes disponibles.\n"
				"La commande `/config` est visible mais n'est pas encore fonctionnelle.\n\n"
                "La commande `/infos` vous donnera des informations sur la configuration actuelle de votre serveur.\n\n"
                "Hot Zone Bot peut aider les membres ainsi que les modérateurs avec diverses fonctionnalités.\n\n"
                "Celà inclut :\n"
				"- Des commandes et fonctionnalités de modération.\n"
				"- Une commande de demande de MP.\n"
                "- Une fonctionnalité de convocations améliorée.\n"
				"- Un système de confessions anonymes et logguées\n"
                "- Des commandes pour vous aider dans vos parties d'Action ou Vérité.\n\n"
                "- Des commandes de configuration pour votre anniversaire.\n"
                "- Un message de bienvenue automatique pour accueillir les nouveaux membres.\n"
                "- Une API Gemini est incluse pour des réponses IA dans des salons dédiés.\n\n"
                "- Hot Zone Bot est un projet en constante évolution, et est dédié à Hot Zone. Dans un objectif de transparence"\
                "avec l'intégralité des membres, le code source est disponible sur [GitHub](https://github.com/Developpement-Hot-Zone/Hot-Zone-Bot.git)."\
                " N'hésitez pas à contribuer ou à suggérer des améliorations !\n\n"
            ),
            color=discord.Color.rvb(210, 25, 100)
        )

        # Envoi de l'embed dans le salon par défaut
        await default_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(OnJoin(bot))
