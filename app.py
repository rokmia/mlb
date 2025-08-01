import requests

# Define the milestone
MILESTONE = 13

# Get all team ids
def get_all_team_ids():
    url = "https://statsapi.mlb.com/api/v1/teams?sportId=1"
    teams = requests.get(url).json()["teams"]
    return [(team["id"], team["name"]) for team in teams]

# Get a team's roster by team_id
def get_team_roster(team_id):
    url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/roster"
    roster = requests.get(url).json()
    return [player["person"]["id"] for player in roster["roster"]]

# Get player stats by player_id
def get_player_stats(player_id):
    url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=season&group=hitting"
    stats = requests.get(url).json()
    if not stats["stats"]:
        return None
    return stats["stats"][0]["splits"][0]["stat"]

# Check if a player is a multiple of 13 away from a milestone
def is_multiple_of_13_away(stat_value):
    return (stat_value % MILESTONE) == (MILESTONE - 1)

# Process each team and player
def process_teams_and_players():
    teams = get_all_team_ids()
    players_away_from_milestones = []

    for team_id, team_name in teams:
        roster = get_team_roster(team_id)
        
        for player_id in roster:
            stats = get_player_stats(player_id)
            if stats:
                career_games = stats["gamesPlayed"]
                career_hits = stats["hits"]
                career_home_runs = stats["homeRuns"]
                career_runs = stats["runs"]
                career_total_bases = stats["totalBases"]

                season_stats = get_player_stats(player_id)  # Replace with season-specific stats if necessary
                season_games = season_hits = season_home_runs = season_runs = season_total_bases = 0  # Assume 0 if unavailable

                # Checking career stats
                if is_multiple_of_13_away(career_games):
                    players_away_from_milestones.append({
                        'player_id': player_id,
                        'team': team_name,
                        'stat': 'career_games',
                        'current_value': career_games,
                        'target': career_games + (MILESTONE - (career_games % MILESTONE))
                    })
                if is_multiple_of_13_away(career_hits):
                    players_away_from_milestones.append({
                        'player_id': player_id,
                        'team': team_name,
                        'stat': 'career_hits',
                        'current_value': career_hits,
                        'target': career_hits + (MILESTONE - (career_hits % MILESTONE))
                    })
                if is_multiple_of_13_away(career_home_runs):
                    players_away_from_milestones.append({
                        'player_id': player_id,
                        'team': team_name,
                        'stat': 'career_home_runs',
                        'current_value': career_home_runs,
                        'target': career_home_runs + (MILESTONE - (career_home_runs % MILESTONE))
                    })
                if is_multiple_of_13_away(career_runs):
                    players_away_from_milestones.append({
                        'player_id': player_id,
                        'team': team_name,
                        'stat': 'career_runs',
                        'current_value': career_runs,
                        'target': career_runs + (MILESTONE - (career_runs % MILESTONE))
                    })
                if is_multiple_of_13_away(career_total_bases):
                    players_away_from_milestones.append({
                        'player_id': player_id,
                        'team': team_name,
                        'stat': 'career_total_bases',
                        'current_value': career_total_bases,
                        'target': career_total_bases + (MILESTONE - (career_total_bases % MILESTONE))
                    })

                # Add season checks here if necessary

    return players_away_from_milestones

# Main function to get results
def main():
    players = process_teams_and_players()
    
    for player in players:
        print(f"Player ID: {player['player_id']}, Team: {player['team']}, "
              f"Stat: {player['stat']}, Current Value: {player['current_value']}, "
              f"Target: {player['target']}")

if __name__ == "__main__":
    main()
