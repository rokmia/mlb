import streamlit as st
import requests
import pandas as pd
from time import sleep

st.title("MLB Milestone Tracker (13-Based)")

@st.cache_data(ttl=86400)
def is_1_away_from_13(val):
    try:
        return (int(val) + 1) % 13 == 0
    except:
        return False

@st.cache_data(ttl=3600)
def get_active_players():
    url = "https://statsapi.mlb.com/api/v1/people?active=true&sportId=1"
    response = requests.get(url)
    if response.status_code != 200:
        st.error(f"Failed to fetch players. Status code: {response.status_code}")
        st.write(response.text)
        st.stop()
    return response.json().get("people", [])


@st.cache_data(ttl=3600)
def get_player_stats(player_id):
    url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=career&stats=season&group=all"
    response = requests.get(url)
    if response.status_code != 200:     
        st.error(f"Failed to fetch players. Status code: {response.status_code}")     
        st.stop()
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
        for stat_key, val in scope_stats.items():
            if is_1_away_from_13(val):
                milestone_stats.setdefault(scope, {})[stat_key] = val
    return milestone_stats

def process_players():
    players = get_active_players()
    batters = []
    pitchers = []

    for player in players:
        player_id = player.get("id")
        full_name = player.get("fullName", "")
        position_code = player.get("primaryPosition", {}).get("code", "")
        try:
            stats = get_player_stats(player_id)
            stat_blocks = extract_stats(stats)
            milestone_stats = check_milestone(stat_blocks)

            if milestone_stats:
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
        except:
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

if st.button("Run Tracker"):
    with st.spinner("Fetching MLB Data (this may take a minute)..."):
        batters, pitchers = process_players()
        batters_df = pd.DataFrame(flatten_results(batters, "batters"))
        pitchers_df = pd.DataFrame(flatten_results(pitchers, "pitchers"))

    st.success("Done!")
    st.subheader("Batters One Away From 13x Milestones")
    st.dataframe(batters_df)
    st.download_button("Download Batters (CSV)", batters_df.to_csv(index=False), "batters.csv")

    st.subheader("Pitchers One Away From 13x Milestones")
    st.dataframe(pitchers_df)
    st.download_button("Download Pitchers (CSV)", pitchers_df.to_csv(index=False), "pitchers.csv")
