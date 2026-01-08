async def load_all_cogs(bot):
    extensions = [
        "Files.Modules.Anti_alt.alt_behavior_analysis",
        "Files.Modules.AOV.aov",
        "Files.Modules.Birthday.birthday",
        "Files.Modules.Chan_lock.chan_lock",
        "Files.Modules.Clear_messages.clear_messages",
        "Files.Modules.Clear_messages.clear_messages_server",
        "Files.Modules.Confessions.confessions",
        "Files.Modules.Confessions.reponse",
        "Files.Modules.Convocations.convocations",
        "Files.Modules.DM_request.MP",
        "Files.Modules.Gemini.gemini",
        "Files.Modules.Lockdown.lockdown",
        "Files.Modules.Main.config",
        "Files.Modules.Main.data_deletion",
        "Files.Modules.Main.help_command",
        "Files.Modules.Main.infos",
        "Files.Modules.Main.on_join",
        "Files.Modules.Minimum_Age.minimum_age",
        "Files.Modules.Moderation.moderation",
        "Files.Modules.NSFW_AI.AI-enable-disable",
        "Files.Modules.OAuth2_backup.backup",
        "Files.Modules.R34.R34",
        "Files.Modules.Welcome.welcome",
    ]
    for ext in extensions:
        try:
            await bot.load_extension(ext)
            print(f"Extension chargée : {ext}")
        except Exception as e:
            print(f"Erreur lors du chargement de {ext} : {e}")

    # Synchroniser les commandes après le chargement des cogs
    try:
        synced = await bot.tree.sync()
        print(f"{len(synced)} commande(s) synchronisée(s)")

        # Nouvelles lignes pour afficher les commandes une à une
        command_names = [command.name for command in synced]
        if command_names:
            print("Commandes synchronisées : " + ", ".join(command_names))
    except Exception as e:
        print(f"Erreur lors de la synchronisation des commandes : {e}")

def setup_cogs(bot):
    # Lance le chargement des cogs au démarrage du bot
    @bot.event
    async def setup_hook():
        await load_all_cogs(bot)