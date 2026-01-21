import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime, timedelta
import pytz
import logging

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

    @app_commands.command(name="mute", description="Rend muet un membre pour une durée définie")
    @commands.has_permissions(moderate_members=True)
    @app_commands.describe(
        member="Le membre à rendre muet",
        duration="Durée du mute (en minutes)",
        reason="Raison du mute"
    )
    async def mute(self, ctx, member: discord.Member, duration: int, *, reason: str = "Aucune raison fournie"):
        until = datetime.utcnow() + timedelta(minutes=duration)
        try:
            await member.timeout(until, reason=reason)
            await self.add_sanction(ctx.guild.id, member.id, "mute", reason, ctx.author, duration=f"{duration}min")
            await ctx.send(f"{member.mention} a été mute pour {duration} minute(s) : {reason}")
        except Exception as e:
            await ctx.send(f"Impossible de mute {member.mention} : {e}")
            logging.error(f"Error muting {member.mention}: {e}")

    @app_commands.command(name="demute", description="Retirer le mute d'un membre")
    @commands.has_permissions(moderate_members=True)
    @app_commands.describe(
        member="Le membre à démute"
    )
    async def demute(self, ctx, member: discord.Member):
        try:
            await member.timeout(None, reason="Démute par commande")
            await ctx.send(f"{member.mention} a été démute avec succès.")
        except Exception as e:
            await ctx.send(f"Impossible de démute {member.mention} : {e}")
            logging.error(f"Error demuting {member.mention}: {e}")

    @app_commands.command(name="warn", description="Avertir un membre")
    @commands.has_permissions(moderate_members=True)
    async def warn(self, ctx, member: discord.Member, *, reason: str = "Aucune raison fournie"):
        await self.add_sanction(ctx.guild.id, member.id, "warn", reason, ctx.author)
        await ctx.send(f"{member.mention} a été averti pour : {reason}")

    @app_commands.command(name="kick", description="Expulser un membre")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = "Aucune raison fournie"):
        await self.add_sanction(ctx.guild.id, member.id, "kick", reason, ctx.author)
        await member.kick(reason=reason)
        await ctx.send(f"{member.mention} a été expulsé pour : {reason}")

    @app_commands.command(name="ban", description="Bannir un membre")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, time: int = None, *, reason: str = "Aucune raison fournie"):
        # time en jours (optionnel)
        duration_str = f"{time}j" if time else None
        await self.add_sanction(ctx.guild.id, member.id, "ban", reason, ctx.author, duration=duration_str)
        await member.ban(reason=reason if not time else f"{reason} (ban {time}j)")
        await ctx.send(
            f"{member.mention} a été banni{' temporairement pour ' + str(time) + ' jour(s)' if time else ''} : {reason}"
        )

        # Si un temps est donné, planifier le unban
        if time:
            async def unban_later():
                await discord.utils.sleep_until(datetime.utcnow() + timedelta(days=time))
                await ctx.guild.unban(member, reason="Fin du ban temporaire")
            self.bot.loop.create_task(unban_later())

    @app_commands.command(name="unban", description="Débannir un membre")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user: discord.User):
        guild = ctx.guild
        try:
            await guild.unban(user)
            await ctx.send(f"{user.name} a été débanni.")
        except discord.NotFound:
            await ctx.send(f"{user.name} n'est pas banni.")

    """
    - Ajouter la liste des convocations échouées par la commande /sanctions
    - Cette sanction peut être retirée avec la commande /sanction-remove
    """

    @app_commands.command(name="sanctions", description="Voir l'historique des sanctions")
    @app_commands.describe(utilisateur="Voir les sanctions d'un autre membre (admin uniquement)")
    async def sanctions(self, ctx, utilisateur: discord.Member = None):
        # Si un utilisateur est précisé, vérifier les permissions admin
        if utilisateur and not ctx.author.guild_permissions.administrator:
            await ctx.send("Seuls les administrateurs peuvent consulter les sanctions d'un autre membre.")
            return

        target = utilisateur or ctx.author
        sanctions = load_sanctions()
        user_id = str(target.id)
        user_sanctions = sanctions.get(user_id, [])

        # Filtrer pour ce serveur uniquement
        user_sanctions = [s for s in user_sanctions if s.get("guild_id") == str(ctx.guild.id)]

        if not user_sanctions:
            await ctx.send(f"Aucune sanction trouvée pour {target.mention}.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"Sanctions de {target.display_name}",
            color=discord.Color.orange()
        )
        for entry in user_sanctions:
            sanction_type = entry.get("type", "Inconnu")
            reason = entry.get("reason", "Aucune raison")
            moderator = entry.get("moderator", "Inconnu")
            date = entry.get("date", "Date inconnue")
            duration = entry.get("duration", None)
            # Convertir la date ISO en format "JJ/MM/AAAA hh:mm" (heure de Paris)
            try:
                dt = datetime.fromisoformat(date)
                paris_tz = pytz.timezone("Europe/Paris")
                dt = dt.replace(tzinfo=pytz.utc).astimezone(paris_tz)
                date_str = dt.strftime("%d/%m/%Y %H:%M")
            except Exception:
                date_str = date
            desc = f"**Type :** {sanction_type}\n**Raison :** {reason}\n**Modérateur :** <@{moderator}>\n**Date :** {date_str}"
            if duration:
                desc += f"\n**Durée :** {duration}"
            embed.add_field(name=f"Sanction", value=desc, inline=False)

        await ctx.send(embed=embed, ephemeral=True)

    @app_commands.command(name="sanction-remove", description="Retirer une sanction d'un membre sur ce serveur")
    @commands.has_permissions(administrator=True)
    @app_commands.describe(
        utilisateur="Le membre dont retirer une sanction",
        index="Numéro de la sanction à retirer (voir /sanctions)"
    )
    async def sanction_remove(self, ctx, utilisateur: discord.Member, index: int):
        sanctions = load_sanctions()
        user_id = str(utilisateur.id)
        guild_id = str(ctx.guild.id)
        user_sanctions = sanctions.get(user_id, [])

        # Filtrer pour ce serveur uniquement
        server_sanctions = [s for s in user_sanctions if s.get("guild_id") == guild_id]

        if not server_sanctions:
            await ctx.send(f"Aucune sanction trouvée pour {utilisateur.mention} sur ce serveur.")
            return

        if index < 1 or index > len(server_sanctions):
            await ctx.send(f"Numéro de sanction invalide. Utilisez /sanctions pour voir la liste et le numéro.")
            return

        # Trouver la sanction à retirer dans la liste complète (pas seulement filtrée)
        sanction_to_remove = server_sanctions[index - 1]
        user_sanctions.remove(sanction_to_remove)
        sanctions[user_id] = user_sanctions
        save_sanctions(sanctions)

        await ctx.send(
            f"La sanction n°{index} de {utilisateur.mention} a été retirée avec succès."
        )

async def setup(bot):
    await bot.add_cog(Moderation(bot))