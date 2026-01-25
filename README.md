# Hot Zone Bot

## Code du projet

### Fichiers : fonctions et scripts

#### Participations au projet

"Participer au projet" peut dire plusieurs choses. Cela peut se faire :

- En créant une ou des branches afin de suggérer directement des modification ou
des nouvelles fonctionnalités qui peuvent être implémantées par la suite dans le code global du projet
- En signalant des bugs, en envoyant des suggestions sans créer de branche,
en signalant des potentiels risques et vulnérabilités
- En rejoignant directement l'équipe des collaborateurs et en étant actif sur le projet

#### Copie partielle et utilisation du projet

Cette page GitHub a été créée dans le but de savoir exactement ce que fait Hot Zone Bot,
créant une transparence entre développeurs et utilisateurs.

> [!CAUTION]
La copie partielle des fichiers du projet est autorisée. Tant que
vous n'en faites aucune utilisation commerciale.

#### Copie totale et usurpation

Comme dit précédemment, il est autorissé de copier et utiliser des fichiers du projet.
Cependant, il est strictement prohibé de copier et d'utiliser l'intégralité des fichiers présents
tout en créant une copie parfaite du bot relié au projet.

### Données des utilisateurs

Toute donnée collectée par le bot est stockée dans ses fichiers. L'intégralité de ses données resteront privées
et ne seront pas partagées avec des tiers.
Seules les données nécessaires au fonctionnement du bot sont collectées.
Cela exclut toute donnée sensible ou personnelle des utilisateurs.

### Installation des modules

Pour faire fonctionner le bot, vous devez installer les modules présents dans le fichier `requirements.txt`.

> [!TIP]
L'installation de ces modules sur votre machine doit se faire via un terminal ou une invite de commande.
Vous pouvez utiliser la commande `pip install -r requirements.txt` pour installer automatiquement
tous les modules nécessaires qui apparaissent dans le fichier `requirements.txt`.
---
> Assurez-vous d'avoir `pip` installé sur votre machine avant d'exécuter cette commande.

Vous pourrez ensuite installer les modules dans votre environnement virtuel si vous en utilisez un.

---

> Vous pouvez créer un environnement virtuel avec la commande `python -m venv "nom_de_votre_env"`.

---

> [!WARNING]
Sur linux, l'environnement virtuel se crée avec la commande `python3 -m venv "nom_de_votre_env"`.

Pour activer l'environnement virtuel, utilisez la commande appropriée en fonction de votre système d'exploitation :

- Sur Windows :

```text
"nom_de_votre_env"\Scripts\activate
```

- Sur macOS et Linux :

```text
source "nom_de_votre_env"/bin/activate
```

> Vous pouvez aussi choisir l'interprêteur Python de votre environnement virtuel
directement dans votre éditeur de code (en bas à droite dans VSCode par exemple).

Après avoir activé votre environnement virtuel, vous pouvez exécuter la commande `pip install -r requirements.txt`
directement dans le terminal de votre éditeur de code avec l'environnement virtuel activé.

### Lancement du bot

Le bot sera lancé via un fichier principal non partagé publiquement pour des raisons de sécurité.
Ce fichier contient le token du bot et permettra de le faire fonctionner.

> Le bot est capable de tourner en 24/7 si votre hébergeur le permet.

### Mise à jour du bot

Les fichiers du projet sont mis à jour régulièrement pour ajouter des fonctionnalités,
corriger des bugs et améliorer la sécurité.

> [!TIP]
Vous pouvez consulter l'historique des modifications dans l'onglet "Commits" du dépôt GitHub.
---
> [!NOTE]
Il est recommandé de vérifier régulièrement les mises à jour
et de les appliquer pour bénéficier des dernières améliorations.
---
> [!TIP]
Vous pouvez également suivre les discussions
et les demandes de fonctionnalités dans l'onglet "Issues" de ce dépôt GitHub.
---
> Notez qu'aucun module ne sera supprimé et que ceux déjà présents dans le projet ne seront pas mis à jour de manière
régulière afin d'éviter de rendre des commandes inutilisables et de devoir les réécrire.
Cependant, des mises à jour ponctuelles des modules peuvent être effectuées si nécessaire.
---

## Interactions avec Discord

### Interactions, commandes et données stockées

L'intégralité des commandes disponibles sont visibles via la commande `/help`dans Discord.

Le bot peut interagir avec les utilisateurs uniquement via ces commandes.
Le bot n'interagit pas avec les utilisateurs si aucune commande n'a été utilisée.
Certaines commandes peuvent récupérer des données puis les stocker de manière temporaire.
C'est le cas des modules AI, AOV, Chan_lock, Confessions, Convocations, Lockdown et Modération (et NSFW-AI prochainement):

|    **Module**     |                                    **Données stockées**                                                 |
|-------------------|---------------------------------------------------------------------------------------------------------|
| **AI**            | ID des salons où l'IA est activée                                                                       |
| **AOV**           | ID des joueurs et heure de leur dernier tour                                                            |
| **Chan_lock**     | ID des salons vérouillés et permission d'écrire pour chaque role                                        |
| **Confessions**   | Numéro des confessions et des réponses                                                                  |
| **Convocations**  | Sauvegarde l'ID et de l'heure de la ou les convocations échouées                                        |
| **Lockdown**      | Sauvegarde des permission d'écrire dans chaque salon et pour chaque rôle pour restaurer les permissions |
| **Modération**    | Données relatives aux sanctions                                                                         |
| **NSFW-AI**       | ID des salons où l'IA est activée                                                                       |

> [!IMPORTANT]
Absolument aucune donnée n'est stockée de manière permanente par le bot. Ceux-ci sont toujours supprimés après un certain temps
(Après leur utilisation dans Discord)

|    **Module**     |                      **Suppression des données**                          |
|-------------------|---------------------------------------------------------------------------|
| **AI**            | Après désactivation du module dans le salon                               |
| **AOV**           | En quittant la partie en cours                                            |
| **Chan_lock**     | En débloquant le salon                                                    |
| **Confessions**   | Ce module stocke le numéro de confession, elle ne sera donc pas supprimée |
| **Convocations**  | Après utilisation de la commande "/sanction-remove"                       |
| **Lockdown**      | Après avoir dévérouiller le serveur                                       |
| **Modération**    | Après utilisation de la commande "/sanction-remove"                       |
| **NSFW-AI**       | Après désactivation du module dans le salon                               |

## Support et contact

Pour toute question, suggestion ou problème lié au projet, vous pouvez ouvrir une "Issue" dans ce dépôt GitHub.
Vous pouvez également contacter l'équipe de développement et des collaborateurs
via le [serveur Discord du projet](https://discord.gg/SC2X7yWU6Y)

## Modifications de README.md et [SECURITY.md](https://github.com/clewmoa-HZB/Hot-Zone-Bot/blob/c090510686cb4362cb63f60fa53632d78a176048/SECURITY.md)

Toute modification des fichiers mentionnés ci-dessus vous sera notifié grâce à
un commit envoyé indépendamment aux commits envoyés pour les autres modifications du projet.
