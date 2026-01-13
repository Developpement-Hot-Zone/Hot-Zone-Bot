import discord
from discord.ext import commands
from discord import app_commands, ui
from fuzzywuzzy import fuzz
from datetime import datetime, timezone
import json
import os

# --- CONFIGURATION (À REMPLACER) ---
STAFF_CHANNEL_ID = 123456789012345678  # ID du salon de staff pour les alertes
QUARANTINE_ROLE_ID = 123456789012345678  # ID du rôle de quarantaine/muted (Score < 5)
SCORE_FILE_PATH = "Files/Data/Alt_Analysis/confidence_scores.json"
STAFF_ROLE_MENTION = "<@NONE>"  # Mention de rôle pour alerter le staff

# --- PARAMÈTRES DE RISQUE ---
RISK_POINTS_NAME_MATCH = 5    # Risque si le nom est similaire à un banni
RISK_POINTS_AVATAR_MATCH = 5  # Risque si l'avatar est identique à un banni
INITIAL_SCORE = 10            # Score de confiance initial pour tout nouveau membre
NAME_SIMILARITY_THRESHOLD = 70 # Seuil de similarité pour le nom (0-100)

class AltBehaviorAnalysis(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = self.load_data()
        self.watch_list_tag = "KICKED" # Tag pour la watch list

    # --- GESTION DES DONNÉES (JSON) ---

    def load_data(self):
        """Charge les scores et la watch list depuis le fichier JSON."""
        if os.path.exists(SCORE_FILE_PATH):
            with open(SCORE_FILE_PATH, 'r') as file:
                return json.load(file)
        # Structure par défaut : 'scores' pour les IDs et 'watch_list' pour les membres récemment kickés
        return {"scores": {}, "watch_list": {}}

    def save_data(self):
        """Sauvegarde les scores et la watch list dans le fichier JSON."""
        os.makedirs(os.path.dirname(SCORE_FILE_PATH), exist_ok=True)
        with open(SCORE_FILE_PATH, 'w') as file:
            json.dump(self.data, file, indent=4)

    def get_score(self, member_id):
        """Récupère le score d'un membre."""
        member_id_str = str(member_id)
        return self.data["scores"].get(member_id_str, INITIAL_SCORE)

    def update_score(self, member_id, change):
        """Met à jour le score d'un membre et sauvegarde."""
        member_id_str = str(member_id)
        current_score = self.get_score(member_id_str)
        new_score = max(0, current_score + change) # Le score ne peut pas être négatif
        self.data["scores"][member_id_str] = new_score
        self.save_data()
        return new_score

    # --- GESTION DE LA WATCH LIST (POUR LE KICK) ---

    def add_to_watch_list(self, member_id):
        """Ajoute un ID à la watch list des membres kickés."""
        member_id_str = str(member_id)
        self.data["watch_list"][member_id_str] = self.watch_list_tag
        self.save_data()

    def is_on_watch_list(self, member_id):
        """Vérifie si un ID est sur la watch list."""
        member_id_str = str(member_id)
        return member_id_str in self.data["watch_list"]

    def remove_from_watch_list(self, member_id):
        """Retire un ID de la watch list."""
        member_id_str = str(member_id)
        if member_id_str in self.data["watch_list"]:
            del self.data["watch_list"][member_id_str]
            self.save_data()

    # --- VÉRIFICATIONS DE RISQUE ---

    async def check_suspicious_name(self, member: discord.Member) -> int:
        """Vérifie la similarité de nom et retourne les points de risque."""
        guild = member.guild
        risk = 0

        try:
            banned_users = [entry async for entry in guild.bans()]
        except discord.Forbidden:
            print(f"Erreur: Permissions manquantes pour lire la liste des bans dans {guild.name}")
            return 0

        for ban_entry in banned_users:
            if fuzz.ratio(ban_entry.user.name.lower(), member.name.lower()) >= NAME_SIMILARITY_THRESHOLD:
                risk += RISK_POINTS_NAME_MATCH
                print(f"[Alt-Analysis] Risque Nom: {member.name} vs {ban_entry.user.name} (+{RISK_POINTS_NAME_MATCH})")
                break 
        return risk

    async def check_suspicious_avatar(self, member: discord.Member) -> int:
        """Vérifie l'identité de l'avatar et retourne les points de risque."""
        guild = member.guild
        risk = 0
        new_member_avatar_url = str(member.display_avatar.url).split('?')[0] # Enlève les paramètres de query

        try:
            banned_users = [entry async for entry in guild.bans()]
        except discord.Forbidden:
            return 0

        for ban_entry in banned_users:
            banned_avatar_url = str(ban_entry.user.display_avatar.url).split('?')[0]
            
            if banned_avatar_url == new_member_avatar_url:
                risk += RISK_POINTS_AVATAR_MATCH
                print(f"[Alt-Analysis] Risque Avatar: {member.name} (+{RISK_POINTS_AVATAR_MATCH})")
                break
        return risk
    
    # --- GESTION DES BOUTONS INTERACTIFS ---

    class ModActionsView(ui.View):
        def __init__(self, cog, target_member_id: int, initial_score: int, reason: str):
            super().__init__(timeout=None)
            self.cog = cog
            self.target_member_id = target_member_id
            self.initial_score = initial_score
            self.reason = reason

        async def get_target_member(self, interaction: discord.Interaction):
            """Tente de récupérer l'objet membre."""
            member = interaction.guild.get_member(self.target_member_id)
            if not member:
                await interaction.response.send_message(f"Le membre (ID: {self.target_member_id}) n'est plus sur le serveur.", ephemeral=True)
                return None
            return member

        @ui.button(label="Safe (+10)", style=discord.ButtonStyle.green, emoji="✅")
        async def safe_callback(self, interaction: discord.Interaction, button: ui.Button):
            member = await self.get_target_member(interaction)
            if not member: return

            new_score = self.cog.update_score(member.id, 10) # Regagne 10 points
            self.cog.remove_from_watch_list(member.id) # Retire de la watch list si présent

            quarantine_role = member.guild.get_role(QUARANTINE_ROLE_ID)
            if quarantine_role and quarantine_role in member.roles:
                await member.remove_roles(quarantine_role, reason="Marqué Safe par Modération")

            await interaction.response.edit_message(content=f"✅ **Safe :** {member.mention} (Score: {new_score}). Retiré du rôle de quarantaine.", view=None)

        @ui.button(label="Kick", style=discord.ButtonStyle.secondary, emoji="🟠")
        async def kick_callback(self, interaction: discord.Interaction, button: ui.Button):
            member = await self.get_target_member(interaction)
            if not member: return

            self.cog.add_to_watch_list(member.id) # Ajout à la watch list
            
            try:
                await member.kick(reason=f"Alt suspect (Score {self.initial_score}). Kick par {interaction.user.name}")
                await interaction.response.edit_message(content=f"🟠 **Expulsion :** {member.mention} a été expulsé et ajouté à la liste de surveillance. (Raison: {self.reason})", view=None)
            except discord.Forbidden:
                await interaction.response.send_message("Je n'ai pas la permission d'expulser ce membre.", ephemeral=True)

        @ui.button(label="Ban / Blacklist", style=discord.ButtonStyle.red, emoji="❌")
        async def ban_callback(self, interaction: discord.Interaction, button: ui.Button):
            member = await self.get_target_member(interaction)
            if not member: return
            
            # Message privé AVANT le ban (si possible)
            try:
                await member.send("Votre compte est suspecté d'être un double compte. Vous avez été banni du serveur.")
            except discord.Forbidden:
                pass # Les MPs sont désactivés

            try:
                await member.ban(reason=f"Alt suspect (Score {self.initial_score}). Bannissement par {interaction.user.name}")
                # Le ban est permanent, donc on retire le membre de toutes les données temporaires
                self.cog.remove_from_watch_list(member.id) 
                
                await interaction.response.edit_message(content=f"❌ **Bannissement :** {member.mention} a été banni. (Raison: {self.reason})", view=None)
            except discord.Forbidden:
                await interaction.response.send_message("Je n'ai pas la permission de bannir ce membre.", ephemeral=True)


    # --- ÉVÉNEMENT PRINCIPAL ---

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot:
            return

        total_risk = 0
        current_score = self.get_score(member.id)
        
        staff_channel = self.bot.get_channel(STAFF_CHANNEL_ID)
        
        # 1. VÉRIFICATION WATCH LIST (MEMBRE EXPULSÉ)
        if self.is_on_watch_list(member.id) and staff_channel:
            await staff_channel.send(
                f"🚨 **RETOUR D'ALT EXPULSÉ** 🚨 {member.mention} vient de rejoindre le serveur. "
                f"Il a été **précédemment expulsé** par un modérateur. Action requise."
            )
            # Ne pas continuer l'analyse de score pour un retour immédiat
            return

        # 2. VÉRIFICATION NOM ET AVATAR
        total_risk += await self.check_suspicious_name(member)
        total_risk += await self.check_suspicious_avatar(member)

        # 3. CALCUL DU NOUVEAU SCORE
        new_score = self.update_score(member.id, -total_risk) # Déduit les points de risque
        
        reason_list = []
        if total_risk > 0:
            if RISK_POINTS_NAME_MATCH in (total_risk, total_risk - RISK_POINTS_AVATAR_MATCH):
                reason_list.append("Nom similaire à un banni.")
            if RISK_POINTS_AVATAR_MATCH in (total_risk, total_risk - RISK_POINTS_NAME_MATCH):
                reason_list.append("Avatar identique à un banni.")
        
        reason_str = " & ".join(reason_list) if reason_list else "Score faible (Initial)"


        # 4. ACTIONS BASÉES SUR LE SCORE

        # ACTION CRITIQUE: SCORE < 5 -> QUARANTAINE
        if new_score < 5:
            quarantine_role = member.guild.get_role(QUARANTINE_ROLE_ID)
            if quarantine_role:
                try:
                    await member.add_roles(quarantine_role, reason=f"Score de confiance faible ({new_score})")
                    # Envoi de la même alerte au staff
                    if staff_channel:
                         await staff_channel.send(f"⚠️ **MISE EN QUARANTAINE** ⚠️ {member.mention} a été automatiquement mis en quarantaine (Score: {new_score}).")
                except discord.Forbidden:
                    print("Erreur: Impossible d'ajouter le rôle de quarantaine. Vérifiez les permissions.")


        # ACTION ALERTE: SCORE < 10 -> ALERTE STAFF AVEC BOUTONS
        if new_score < 10 and staff_channel:
            embed = discord.Embed(
                title=f"🚨 ALERTE ALT SUSPECT (Score: {new_score})",
                description=(
                    f"Le membre {member.mention} (`{member.id}`) présente un risque élevé."
                    f"\n**Signaux :** {reason_str}"
                ),
                color=discord.Color.red()
            )
            embed.add_field(name="Âge du compte", value=f"Créé il y a {(discord.utils.utcnow() - member.created_at).days} jours.", inline=True)
            embed.add_field(name="Action", value=f"Score mis à jour: {INITIAL_SCORE} -> {new_score}", inline=True)
            embed.set_thumbnail(url=member.display_avatar.url)

            # Envoi de l'alerte avec les boutons d'action
            await staff_channel.send(
                STAFF_ROLE_MENTION, 
                embed=embed, 
                view=self.ModActionsView(self, member.id, new_score, reason_str)
            )


async def setup(bot):
    await bot.add_cog(AltBehaviorAnalysis(bot))