import discord
class DeleteButton(discord.ui.View):
    def __init__(self, author_id, message_type, message_id):
        super().__init__(timeout=None)
        self.author_id = author_id
        self.message_type = message_type  # 'confession' ou 'reponse'
        self.message_id = message_id

    @discord.ui.button(label="Supprimer", style=discord.ButtonStyle.danger)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Vérification auteur ou modérateur
        is_mod = any(role.permissions.administrator for role in getattr(interaction.user, 'roles', []))
        if interaction.user.id != self.author_id and not is_mod:
            await interaction.response.send_message("Vous n'avez pas la permission de supprimer ce message.", ephemeral=True)
            return
        # Suppression du message
        try:
            msg = await interaction.channel.fetch_message(self.message_id)
            await msg.delete()
            # Log suppression
            import Files.Modules.Confessions.logs as logs
            await logs.log_suppression(self.message_type, self.message_id, interaction.user.id, bot=interaction.client)
            await interaction.response.send_message("Message supprimé et loggé.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Erreur lors de la suppression : {e}", ephemeral=True)
import discord
from discord.ext import commands
from discord import app_commands
import os
import json

CONFESSION_DATA_PATH = "Files/Data/Confessions/confession_counter.json"
LOG_CHANNEL_ID = 1409259784946978847

class Reponse(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Crée le dossier Data/Confessions si absent
        data_dir = os.path.dirname(CONFESSION_DATA_PATH)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
        # Crée le fichier de compteur si absent dès l'init
        if not os.path.exists(CONFESSION_DATA_PATH):
            with open(CONFESSION_DATA_PATH, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=4)
        self.load_counters()

    def load_counters(self):
        try:
            if os.path.exists(CONFESSION_DATA_PATH):
                with open(CONFESSION_DATA_PATH, 'r', encoding='utf-8') as f:
                    self.counters = json.load(f)
            else:
                # Crée le fichier si absent
                self.counters = {}
                with open(CONFESSION_DATA_PATH, 'w', encoding='utf-8') as f:
                    json.dump(self.counters, f, ensure_ascii=False, indent=4)
        except json.JSONDecodeError:
            # Si le fichier est corrompu ou vide, on le réinitialise
            self.counters = {}
            with open(CONFESSION_DATA_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.counters, f, ensure_ascii=False, indent=4)

    def save_counters(self):
        with open(CONFESSION_DATA_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.counters, f, ensure_ascii=False, indent=4)

    @app_commands.command(name="repondre", description="Répondre anonymement à une confession")
    @app_commands.describe(confession_num="Numéro de la confession à laquelle répondre", contenu="Contenu de la réponse", images="Image à joindre (optionnel)")
    async def repondre(self, interaction: discord.Interaction, confession_num: int, contenu: str, images: discord.Attachment = None):
        try:
            # Incrémentation du compteur de réponse pour cette confession
            confession_key = str(confession_num)
            if confession_key not in self.counters:
                self.counters[confession_key] = 1
            else:
                self.counters[confession_key] += 1
            reponse_num = self.counters[confession_key]
            self.save_counters()

            # Recherche du fil associé à la confession
            thread_name = f"Confession {confession_num}"
            thread = discord.utils.get(interaction.channel.threads, name=thread_name)
            if not thread:
                await interaction.response.send_message(f"Fil pour la confession {confession_num} introuvable.", ephemeral=True)
                return

            # Création de l'embed
            embed = discord.Embed(title=f"Réponse à la confession {confession_num} n°{reponse_num}", description=contenu, color=discord.Color.purple())
            if images:
                embed.set_image(url=images.url)

            # Envoi de la réponse dans le fil avec bouton Supprimer
            delete_view = DeleteButton(interaction.user.id, 'reponse', None)
            msg = await thread.send(embed=embed)
            delete_view.message_id = msg.id
            await msg.edit(view=delete_view)
            await interaction.response.send_message(f"Réponse envoyée anonymement dans le fil de la confession {confession_num}.", ephemeral=True)

            # Log dans le salon staff
            await self.log_reponse(interaction, confession_num, reponse_num, msg, contenu, images)
        except Exception as e:
            await interaction.response.send_message(f"Une erreur est survenue : {e}", ephemeral=True)

    async def log_reponse(self, interaction, confession_num, reponse_num, msg, contenu, images):
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if not log_channel:
            return
        embed = discord.Embed(title=f"Log Réponse à la confession {confession_num} n°{reponse_num}", description=contenu, color=discord.Color.orange())
        embed.add_field(name="Auteur", value=str(interaction.user.id), inline=False)
        embed.add_field(name="Lien du message", value=msg.jump_url, inline=False)
        if images:
            embed.set_image(url=images.url)
        await log_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Reponse(bot))
