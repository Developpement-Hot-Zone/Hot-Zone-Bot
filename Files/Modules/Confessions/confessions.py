import discord
from discord import app_commands
from discord.ext import commands
import random
import os
import json
from typing import Optional
import re

from . import logs

CONFESSION_CHANNEL_ID = 1400001490134761514
CONFESSION_NSFW_CHANNEL_ID = 1412080759472132126
COUNTER_PATH = os.path.join(os.path.dirname(__file__), '../../Data/Confessions/confession_counter.json')

allowed_guilds = [1391083075424747660]

# Gestion du compteur de confessions
def get_confession_count():
    if not os.path.exists(COUNTER_PATH):
        return 1
    with open(COUNTER_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get('count', 1)

def increment_confession_count():
    count = get_confession_count() + 1
    with open(COUNTER_PATH, 'w', encoding='utf-8') as f:
        json.dump({'count': count}, f)
    return count

class ConfessionModal(discord.ui.Modal, title="Répondre à la confession"):
    response = discord.ui.TextInput(label="Réponse", style=discord.TextStyle.paragraph, required=True)

    def __init__(self, confession_message: discord.Message):
        super().__init__()
        self.confession_message = confession_message

    async def on_submit(self, interaction: discord.Interaction):
        COUNTER_PATH = os.path.join(os.path.dirname(__file__), '../../Data/Confessions/confession_counter.json')
        # Récupérer le numéro de confession depuis le titre de l'embed
        confession_embed = self.confession_message.embeds[0] if self.confession_message.embeds else None
        confession_num = None
        if confession_embed and confession_embed.title:
            match = re.search(r'n°(\d+)', confession_embed.title)
            if match:
                confession_num = match.group(1)
        if not confession_num:
            confession_num = "?"
        # Gestion du compteur de réponse Y
        if os.path.exists(COUNTER_PATH):
            with open(COUNTER_PATH, 'r', encoding='utf-8') as f:
                counters = json.load(f)
        else:
            counters = {}
        key = f"reponse_{confession_num}"
        y = counters.get(key, 0) + 1
        counters[key] = y
        with open(COUNTER_PATH, 'w', encoding='utf-8') as f:
            json.dump(counters, f)
        # Crée ou récupère le fil
        thread_name = f"Confession {confession_num}"
        thread = discord.utils.get(self.confession_message.channel.threads, name=thread_name)
        if not thread:
            thread = await self.confession_message.create_thread(name=thread_name)
        # Embed réponse
        embed = discord.Embed(title=f"Réponse à la confession {confession_num} n°{y}", description=self.response.value, color=discord.Color.purple())
        msg = await thread.send(embed=embed)
        view = ReponseView(msg, interaction.user.id, msg.id)
        await msg.edit(view=view)
        await interaction.response.send_message("Votre réponse a été envoyée dans le fil de discussion !", ephemeral=True)
        # Log
        await logs.log_reponse(confession_num, y, msg.jump_url, interaction.user.id, self.response.value, bot=interaction.client)

class DeleteButton(discord.ui.Button):
    def __init__(self, author_id, message_type, message_id):
        super().__init__(label="Supprimer", style=discord.ButtonStyle.danger)
        self.author_id = author_id
        self.message_type = message_type
        self.message_id = message_id

    async def callback(self, interaction: discord.Interaction):
        is_mod = any(role.permissions.administrator for role in interaction.user.roles)
        if interaction.user.id != self.author_id and not is_mod:
            await interaction.response.send_message("Vous n'avez pas la permission de supprimer ce message.", ephemeral=True)
            return
        try:
            msg = await interaction.channel.fetch_message(self.message_id)
            await msg.delete()
            from . import logs
            await logs.log_suppression(self.message_type, self.message_id, interaction.user.id, bot=interaction.client)
            await interaction.response.send_message("Message supprimé et loggé.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Erreur lors de la suppression : {e}", ephemeral=True)

class ReplyButton(discord.ui.Button):
    def __init__(self, confession_message: discord.Message):
        super().__init__(label="Répondre", style=discord.ButtonStyle.primary)
        self.confession_message = confession_message

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ConfessionModal(self.confession_message))

class ConfessionView(discord.ui.View):
    def __init__(self, confession_message: discord.Message, author_id, message_id):
        super().__init__(timeout=None)
        self.add_item(ReplyButton(confession_message))
        self.add_item(DeleteButton(author_id, 'confession', message_id))

class ReponseView(discord.ui.View):
    def __init__(self, response_message: discord.Message, author_id, message_id):
        super().__init__(timeout=None)
        self.add_item(DeleteButton(author_id, 'reponse', message_id))
        # Tu peux ajouter d'autres boutons ici si besoin

class Confessions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="confesser", description="Envoyer une confession anonyme.")
    @app_commands.describe(confession="Votre confession", medias="Images ou vidéos (optionnel)")
    async def confesser(self, interaction: discord.Interaction, confession: str, medias: Optional[discord.Attachment] = None):
        # Vérification serveur et salon
        if interaction.guild.id not in allowed_guilds:
            await interaction.response.send_message("Commande non autorisée sur ce serveur.", ephemeral=True)
            return
        if interaction.channel_id != CONFESSION_CHANNEL_ID and interaction.channel_id != CONFESSION_NSFW_CHANNEL_ID:
            await interaction.response.send_message("Cette commande ne peut être utilisée que dans le salon dédié aux confessions.", ephemeral=True)
            return
        # Génération du numéro de confession
        confession_number = get_confession_count()
        increment_confession_count()
        # Couleur aléatoire
        color = discord.Color(random.randint(0, 0xFFFFFF))
        embed = discord.Embed(title=f"Confession anonyme n°{confession_number}", description=confession, color=color)
        if medias:
            if medias.content_type and medias.content_type.startswith("image"):
                embed.set_image(url=medias.url)
            elif medias.content_type and medias.content_type.startswith("video"):
                embed.add_field(name="Vidéo", value=medias.url, inline=False)

        # Envoi du message avec bouton Supprimer
        msg = await interaction.channel.send(embed=embed)  # Envoie le message sans vue
        view = ConfessionView(msg, interaction.user.id, msg.id)
        await msg.edit(view=view)
        # Log de la confession
        image_url = medias.url if medias and medias.content_type and medias.content_type.startswith("image") else None
        await logs.log_confession(confession_number, msg.jump_url, interaction.user.id, confession, image_url=image_url, bot=self.bot)
        await interaction.response.send_message("Votre confession anonyme a été envoyée !", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Confessions(bot))
