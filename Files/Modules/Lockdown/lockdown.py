import discord
from discord import app_commands
from discord.ext import commands
import json
from datetime import datetime, timezone, timedelta
import os

PERMS_BACKUP_FILE = "Files/Data/Lockdown/lockdown_perms_backup.json"

class Lockdown(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def backup_permissions(self, guild: discord.Guild):
        backup = {"roles": {}, "channels": {}}
        for role in guild.roles:
            backup["roles"][str(role.id)] = role.permissions.send_messages
        for channel in guild.channels:
            if isinstance(channel, (discord.TextChannel, discord.CategoryChannel)):
                overwrites = {}
                for role, perm in channel.overwrites.items():
                    if perm.send_messages is not None:
                        overwrites[str(role.id)] = perm.send_messages
                if overwrites:
                    backup["channels"][str(channel.id)] = overwrites
        with open(PERMS_BACKUP_FILE, "w", encoding="utf-8") as f:
            json.dump(backup, f, indent=2)

    async def restore_permissions(self, guild: discord.Guild):
        if not os.path.exists(PERMS_BACKUP_FILE):
            return False
        with open(PERMS_BACKUP_FILE, "r", encoding="utf-8") as f:
            backup = json.load(f)
        for role in guild.roles:
            if str(role.id) in backup["roles"]:
                perms = role.permissions
                perms.update(send_messages=backup["roles"][str(role.id)])
                try:
                    await role.edit(permissions=perms, reason="Unlockdown restore")
                except Exception:
                    pass
        for channel in guild.channels:
            if isinstance(channel, (discord.TextChannel, discord.CategoryChannel)):
                if str(channel.id) in backup["channels"]:
                    overwrites = channel.overwrites
                    for role_id, value in backup["channels"][str(channel.id)].items():
                        role = guild.get_role(int(role_id))
                        if role:
                            ow = overwrites.get(role) or discord.PermissionOverwrite()
                            ow.send_messages = value
                            overwrites[role] = ow
                    try:
                        await channel.edit(overwrites=overwrites, reason="Unlockdown restore")
                    except Exception:
                        pass
        return True

    async def lockdown_guild(self, guild: discord.Guild):
        for channel in guild.text_channels:
            overwrites = channel.overwrites
            for role in guild.roles:
                if role.is_default():
                    continue
                ow = overwrites.get(role) or discord.PermissionOverwrite()
                ow.send_messages = False
                overwrites[role] = ow
            try:
                await channel.edit(overwrites=overwrites, reason="Lockdown")
            except Exception:
                pass
        try:
            await guild.edit(invites_disabled=True, reason="Lockdown")
        except Exception:
            pass

    async def unlock_guild(self, guild: discord.Guild):
        try:
            await guild.edit(invites_disabled=False, reason="Unlockdown")
        except Exception:
            pass

    async def list_recent_members(self, guild: discord.Guild, channel: discord.TextChannel):
        now = datetime.now(timezone.utc)
        recent = [m for m in guild.members if m.joined_at and (now - m.joined_at).total_seconds() < 3600]
        if not recent:
            await channel.send("Aucun membre récent à signaler.")
            return
        msg = "Membres ayant rejoint il y a moins d'une heure :\n"
        msg += "\n".join(f"- {m.mention} (rejoint à {m.joined_at.strftime('%H:%M:%S')})" for m in recent)
        await channel.send(msg)

    @app_commands.command(name="lockdown", description="Ferme tout le serveur (admin seulement)")
    @app_commands.describe(channel="Salon où la liste des membres récents sera envoyée")
    @app_commands.checks.has_permissions(administrator=True)
    async def lockdown(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        await self.backup_permissions(guild)
        await self.lockdown_guild(guild)
        await self.list_recent_members(guild, channel)
        await interaction.followup.send(f"Serveur verrouillé. Toutes les permissions d'envoi de messages ont été désactivées. La liste des membres récents a été envoyée dans {channel.mention}.", ephemeral=True)

    @app_commands.command(name="un-lockdown", description="Rouvre le serveur et restaure les permissions (admin seulement)")
    @app_commands.checks.has_permissions(administrator=True)
    async def unlock(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        ok = await self.restore_permissions(guild)
        await self.unlock_guild(guild)
        if ok:
            await interaction.followup.send("Serveur déverrouillé et permissions restaurées.", ephemeral=True)
        else:
            await interaction.followup.send("Aucune sauvegarde de permissions trouvée. Permissions non restaurées.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Lockdown(bot))
