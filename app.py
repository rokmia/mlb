import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from time import sleep

st.title("MLB Milestone Tracker (13-Based)")

def is_1_away_from_13(val):
    try:
        return (int(val) + 1) % 13 == 0
    except:
        return False

def get_tomorrows_games():
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={tomorrow}"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    games = data.get("dates", [])[0].get("games", []) if data.get("dates") else []
    st.info(f"Found {len(games)} scheduled games for tomorrow.")
    return games

def get_team_roster(team_id):
    url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/roster/active"
    response = requests.get(url)
    response.raise_for_status()
    return response.json().get("roster", [])

def get_player_stats(player_id):
    url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=career&stats=season&group=all"
    response = requests.get(url)
    response.raise_for_status()
    return response.json().get("stats", [])

def extract_stats(stats):
    stat_dict = {}
    for item in stats:
        splits = item.get("splits", [])
        for split in splits:
            type_label = split.get("type", {}).get("displayName", "").lower()
            stat = split.get("stat", {})
            if type_label in ["season", "career"]:
                stat_dict[type_label] = stat
    return stat_dict

def check_milestone(stats):
    milestone_stats = {}
    for scope in ["season", "career"]:
        scope_stats = stats.get(scope, {})

        if scope == "season":
            keys = ["gamesPlayed", "hits", "doubles", "triples", "homeRuns", "stolenBases", "totalBases"]
        elif scope == "career":
            keys = ["gamesPlayed", "hits", "doubles", "triples", "homeRuns", "stolenBases", "totalBases"]

        for key in keys:
            val = scope_stats.get(key)
            if is_1_away_from_13(val):
                milestone_stats.setdefault(scope, {})[key] = val

        # Calculate singles if possible
        hits = scope_stats.get("hits")
        doubles = scope_stats.get("doubles")
        triples = scope_stats.get("triples")
        home_runs = scope_stats.get("homeRuns")
        if all(isinstance(v, (int, float)) for v in [hits, doubles, triples, home_runs]):
            singles = hits - doubles - triples - home_runs
            if is_1_away_from_13(singles):
                milestone_stats.setdefault(scope, {})["singles"] = singles

    return milestone_stats

def process_players_for_tomorrow():
    games = get_tomorrows_games()
    batters = []
    pitchers = []
    player_ids_seen = set()

    for game in games:
        for team_type in ["home", "away"]:
            team = game.get(f"{team_type}Team", {})
            team_id = team.get("id")
            if not team_id:
                continue
            try:
                roster = get_team_roster(team_id)
                st.write(f"{team.get('name', 'Unknown')} roster: {len(roster)} players")
            except Exception as e:
                st.warning(f"Roster fetch failed for team {team.get('name', 'unknown')}: {e}")
                continue

            for player in roster:
                player_id = player.get("person", {}).get("id")
                full_name = player.get("person", {}).get("fullName")
                position_code = player.get("position", {}).get("code")
                if player_id in player_ids_seen:
                    continue
                player_ids_seen.add(player_id)

                try:
                    stats = get_player_stats(player_id)
                    stat_blocks = extract_stats(stats)
                    milestone_stats = check_milestone(stat_blocks)

                    if milestone_stats:
                        st.write(f"✅ {full_name} matched milestones: {milestone_stats}")
                        entry = {
                            "id": player_id,
                            "name": full_name,
                            "position": position_code,
                            "milestone_stats": milestone_stats
                        }
                        if position_code == "1":
                            pitchers.append(entry)
                        else:
                            batters.append(entry)
                    else:
                        st.write(f"❌ {full_name} has no milestone stats")
                except Exception as e:
                    st.warning(f"Error fetching stats for {full_name}: {e}")
                    continue
                sleep(0.1)

    return batters, pitchers

def flatten_results(data, role):
    flat_data = []
    for entry in data:
        for scope, stats in entry["milestone_stats"].items():
            for stat, val in stats.items():
                flat_data.append({
                    "Name": entry["name"],
                    "Role": "Pitcher" if role == "pitchers" else "Batter",
                    "Scope": scope,
                    "Stat": stat,
                    "Value": val,
                    "One Away From": int(val) + 1
                })
    return flat_data

if st.button("Run Tracker for Tomorrow's Games"):
    with st.spinner("Fetching MLB Data (this may take a minute)..."):
        batters, pitchers = process_players_for_tomorrow()
        batters_df = pd.DataFrame(flatten_results(batters, "batters"))
        pitchers_df = pd.DataFrame(flatten_results(pitchers, "pitchers"))

    st.success("Done!")
    st.subheader("Batters Playing Tomorrow One Away From 13x Milestones")
    st.dataframe(batters_df)
    st.download_button("Download Batters (CSV)", batters_df.to_csv(index=False), "batters.csv")

    st.subheader("Pitchers Playing Tomorrow One Away From 13x Milestones")
    st.dataframe(pitchers_df)
    st.download_button("Download Pitchers (CSV)", pitchers_df.to_csv(index=False), "pitchers.csv")
