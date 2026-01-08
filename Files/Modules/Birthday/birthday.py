import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
from datetime import datetime
import os

class Birthday(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.birthday_data_path = os.path.join(os.path.dirname(__file__), "../../Data/Birthday/birthday_data")
        self.check_birthdays.start()

    def load_server_config(self, guild_id):
        config_path = os.path.join(self.birthday_data_path, f"server_{guild_id}.json")
        if os.path.exists(config_path):
            with open(config_path, "r") as file:
                return json.load(file)
        return {}

    def save_server_config(self, guild_id, config):
        config_path = os.path.join(self.birthday_data_path, f"server_{guild_id}.json")
        with open(config_path, "w") as file:
            json.dump(config, file, indent=4)

    def load_user_birthdays(self):
        birthdays_path = os.path.join(self.birthday_data_path, "user_birthdays.json")
        if os.path.exists(birthdays_path):
            with open(birthdays_path, "r") as file:
                return json.load(file)
        return {}

    def save_user_birthdays(self, birthdays):
        birthdays_path = os.path.join(self.birthday_data_path, "user_birthdays.json")
        with open(birthdays_path, "w") as file:
            json.dump(birthdays, file, indent=4)

    @app_commands.command(name="birthday-config")
    async def birthday(self, ctx, option: bool):
        "Enable or disable the birthday system."
        if not ctx.author.guild_permissions.administrator:
            await ctx.respond("Vous avez besoin des droits administrateurs pour effectuer cette commande", ephemeral=True)
            return

        config = self.load_server_config(ctx.guild.id)
        if option:
            config["enabled"] = True
            await ctx.respond("Système d'anniversaires activé. Veuillez configurer le salon et l'heure d'envoie.")
        else:
            config.pop("enabled", None)
            config.pop("channel_id", None)
            config.pop("time", None)
            self.save_server_config(ctx.guild.id, config)
            await ctx.respond("Système d'anniversaires désactivé et configuration effacée.")
            return

        self.save_server_config(ctx.guild.id, config)

    @app_commands.command(name="birthday-config-channel")
    async def birthday_channel(self, ctx):
        "Set the channel for birthday messages."
        if not ctx.author.guild_permissions.administrator:
            await ctx.respond("Vous avez besoin des droits administrateurs pour effectuer cette commande", ephemeral=True)
            return

        await ctx.respond("Veuillez mentionner le salon ou fournir son ID.")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            message = await self.bot.wait_for("message", check=check, timeout=60)
            channel_id = int(message.content.strip("#"))
            config = self.load_server_config(ctx.guild.id)
            config["channel_id"] = channel_id
            self.save_server_config(ctx.guild.id, config)
            await ctx.send(f"Les messages d'anniversaire seront envoyés dans <#{channel_id}>.")
        except Exception as e:
            await ctx.send("Erreur lors de la configuration du salon. Veuillez réessayer.")

    @app_commands.command(name="birthday-config-time")
    async def birthday_time(self, ctx, time: str):
        "Set the time for birthday messages (HH:mm)."
        if not ctx.author.guild_permissions.administrator:
            await ctx.respond("Vous avez besoin des droits administrateurs pour effectuer cette commande", ephemeral=True)
            return

        try:
            datetime.strptime(time, "%H:%M")
            config = self.load_server_config(ctx.guild.id)
            config["time"] = time
            self.save_server_config(ctx.guild.id, config)
            await ctx.respond(f"Les messages d'anniversaire seront envoyés à {time}.")
        except ValueError:
            await ctx.respond("Format d'heure invalide. Veuillez utiliser avec le format `HH:mm`.")

    @app_commands.command(name="birthday-set")
    async def birthday_set(self, ctx, date: str):
        "Indiquez votre date d'anniversaire (JJ/MM/AAAA)."
        try:
            datetime.strptime(date, "%d/%m/%Y")
            birthdays = self.load_user_birthdays()
            birthdays[str(ctx.author.id)] = date
            self.save_user_birthdays(birthdays)
            await ctx.respond("Votre anniversaire a été enregistré.")
        except ValueError:
            await ctx.respond("Format de date invalide. Veuillez utiliser JJ/MM/AAAA.")

    @tasks.loop(minutes=1)
    async def check_birthdays(self):
        now = datetime.now()
        if now.strftime("%H:%M") != "00:00":
            return

        for guild in self.bot.guilds:
            config = self.load_server_config(guild.id)
            if not config.get("enabled"):
                continue

            channel_id = config.get("channel_id")
            time = config.get("time")
            if not channel_id or not time or now.strftime("%H:%M") != time:
                continue

            birthdays = self.load_user_birthdays()
            today = now.strftime("%d/%m")
            members_to_celebrate = [
                guild.get_member(int(user_id))
                for user_id, date in birthdays.items()
                if date[:5] == today
            ]

            if members_to_celebrate:
                channel = guild.get_channel(channel_id)
                if channel:
                    mentions = ", ".join(
                        f"{member.mention} (Il a désormais {now.year - int(date.split('/')[-1])} ans)"
                        for user_id, date in birthdays.items()
                        if (member := guild.get_member(int(user_id))) and date[:5] == today
                    )
                    await channel.send(f"Souhaitons un joyeux anniversaire à {mentions}! 🎉")
                else:
                    print(f"Erreur : Le canal avec l'ID {channel_id} n'existe pas ou est inaccessible dans le serveur {guild.name}.")

    @check_birthdays.before_loop
    async def before_check_birthdays(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Birthday(bot))