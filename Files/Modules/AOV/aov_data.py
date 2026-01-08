import os
import json
from datetime import datetime

DATA_PATH = os.path.join(os.path.dirname(__file__), "../../Data/AOV/aov_players.json")

def load_players():
    if not os.path.exists(DATA_PATH):
        return {}
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_players(players):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(players, f)

def add_player(guild_id, user_id):
    players = load_players()
    guild_players = players.setdefault(str(guild_id), {})
    now = int(datetime.utcnow().timestamp())
    guild_players[str(user_id)] = now
    save_players(players)

def remove_player(guild_id, user_id):
    players = load_players()
    guild_players = players.get(str(guild_id), {})
    if str(user_id) in guild_players:
        del guild_players[str(user_id)]
        players[str(guild_id)] = guild_players
        save_players(players)

def update_player_time(guild_id, user_id):
    players = load_players()
    guild_players = players.setdefault(str(guild_id), {})
    now = int(datetime.utcnow().timestamp())
    guild_players[str(user_id)] = now
    save_players(players)

def get_players(guild_id):
    players = load_players()
    return players.get(str(guild_id), {})

def get_player_time(guild_id, user_id):
    players = load_players()
    guild_players = players.get(str(guild_id), {})
    return guild_players.get(str(user_id))