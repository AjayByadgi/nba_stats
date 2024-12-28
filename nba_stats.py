import requests
from datetime import datetime
import streamlit as st
import pandas as pd
import time
from nba_live_stats_db import NBALiveStatsDB

# Initialize database
db = NBALiveStatsDB()

def format_minutes(minutes_str):
    try:
        minutes = minutes_str.split('PT')[1].split('M')[0]
        seconds = minutes_str.split('M')[1].split('.')[0]
        return f"{minutes}:{seconds.zfill(2)}"
    except:
        return "0:00"

def fetch_player_stats(game_id):
    try:
        response = requests.get(
            f"https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{game_id}.json"
        )
        response.raise_for_status()
        data = response.json()
        if not data or 'game' not in data:
            st.warning(f"Missing 'game' key in data for game ID {game_id}.")
            return None
        return data['game']
    except Exception as e:
        st.error(f"Error fetching player stats: {e}")
        return None

def display_player_stats(game_id, home_team, away_team):
    game_data = fetch_player_stats(game_id)
    if not game_data:
        st.warning("Player statistics are unavailable for this game.")
        return

    # Create tabs for home and away teams
    team_tab1, team_tab2 = st.tabs([
        f"{home_team['teamCity']} {home_team['teamName']}",
        f"{away_team['teamCity']} {away_team['teamName']}"
    ])

    # Process stats for home team
    with team_tab1:
        players = game_data.get('homeTeam', {}).get('players', [])
        if players:
            players_data = []
            for player in players:
                if player.get('played'):
                    stats = player.get('statistics', {})
                    players_data.append({
                        'PLAYER': f"{player['name']} {'(S)' if player.get('starter') == '1' else ''}",
                        'MIN': format_minutes(stats.get('minutes', '0')),
                        'PTS': stats.get('points', 0),
                        'REB': stats.get('reboundsTotal', 0),
                        'AST': stats.get('assists', 0),
                        'FG': f"{stats.get('fieldGoalsMade', 0)}-{stats.get('fieldGoalsAttempted', 0)}",
                        'FG%': f"{stats.get('fieldGoalsPercentage', 0) * 100:.1f}",
                        '3P': f"{stats.get('threePointersMade', 0)}-{stats.get('threePointersAttempted', 0)}",
                        'FT': f"{stats.get('freeThrowsMade', 0)}-{stats.get('freeThrowsAttempted', 0)}"
                    })
            if players_data:
                st.dataframe(pd.DataFrame(players_data), use_container_width=True)
            else:
                st.info("No statistics available for home team players.")

    # Process stats for away team
    with team_tab2:
        players = game_data.get('awayTeam', {}).get('players', [])
        if players:
            players_data = []
            for player in players:
                if player.get('played'):
                    stats = player.get('statistics', {})
                    players_data.append({
                        'PLAYER': f"{player['name']} {'(S)' if player.get('starter') == '1' else ''}",
                        'MIN': format_minutes(stats.get('minutes', '0')),
                        'PTS': stats.get('points', 0),
                        'REB': stats.get('reboundsTotal', 0),
                        'AST': stats.get('assists', 0),
                        'FG': f"{stats.get('fieldGoalsMade', 0)}-{stats.get('fieldGoalsAttempted', 0)}",
                        'FG%': f"{stats.get('fieldGoalsPercentage', 0) * 100:.1f}",
                        '3P': f"{stats.get('threePointersMade', 0)}-{stats.get('threePointersAttempted', 0)}",
                        'FT': f"{stats.get('freeThrowsMade', 0)}-{stats.get('freeThrowsAttempted', 0)}"
                    })
            if players_data:
                st.dataframe(pd.DataFrame(players_data), use_container_width=True)
            else:
                st.info("No statistics available for away team players.")

# Main App
st.title("🏀 NBA Live Games")
refresh_interval = st.sidebar.slider("Refresh Interval (seconds):", min_value=5, max_value=120, value=30, step=5)

if st.sidebar.button("Reset Database"):
    db.clear_database()

with st.sidebar:
    st.subheader("Database Statistics")
    stats = db.get_database_stats()
    st.write(f"Total Games Tracked: {stats[0]}")
    st.write(f"Total Teams: {stats[1]}")
    st.write(f"Total Players: {stats[2]}")
    view_database = st.checkbox("View Database")

if view_database:
    st.subheader("📊 View Database")
    selected_table = st.selectbox(
        "Select a table to view:",
        options=["Games", "Game Teams", "Players"]
    )
    try:
        if selected_table == "Games":
            games_data = db.conn.execute("SELECT * FROM games").df()
            st.dataframe(games_data)
        elif selected_table == "Game Teams":
            game_teams_data = db.conn.execute("SELECT * FROM game_teams").df()
            st.dataframe(game_teams_data)
        elif selected_table == "Players":
            players_data = db.conn.execute("SELECT * FROM players").df()
            st.dataframe(players_data)
    except Exception as e:
        st.error(f"Error fetching data from the {selected_table} table: {e}")

try:
    response = requests.get("https://nba-prod-us-east-1-mediaops-stats.s3.amazonaws.com/NBA/liveData/scoreboard/todaysScoreboard_00.json")
    response.raise_for_status()
    scoreboard_data = response.json()
    db.process_scoreboard_data(scoreboard_data)

    games = scoreboard_data['scoreboard']['games']
    for game in games:
        game_id = game["gameId"]
        away_team = game["awayTeam"]
        home_team = game["homeTeam"]

        st.subheader(f"{away_team['teamCity']} {away_team['teamName']} ({away_team['wins']}-{away_team['losses']}) at "
                     f"{home_team['teamCity']} {home_team['teamName']} ({home_team['wins']}-{home_team['losses']})")

        game_status = game["gameStatusText"]
        col1, col2 = st.columns([2, 1])

        with col1:
            if game["gameStatus"] == 1:
                game_time = datetime.strptime(game['gameEt'], '%Y-%m-%dT%H:%M:%SZ')
                st.info(f"🕒 Tip-off at {game_time.strftime('%I:%M %p ET')}")
                continue
            elif game["gameStatus"] == 2:
                st.write(f"Q{game['period']} - {game['gameClock']}")
                st.header(f"{away_team['score']} - {home_team['score']}")
            else:
                st.write("Final")
                st.header(f"{away_team['score']} - {home_team['score']}")

        with col2:
            st.write("Team Stats")
            st.write(f"Timeouts: {away_team['timeoutsRemaining']} - {home_team['timeoutsRemaining']}")
            if away_team['inBonus'] != "None":
                st.write(f"{away_team['teamCity']} in bonus")
            if home_team['inBonus'] != "None":
                st.write(f"{home_team['teamCity']} in bonus")

        try:
            with st.expander("View Player Statistics"):
                display_player_stats(game_id, home_team, away_team)
        except Exception as e:
            st.error(f"Error displaying player stats: {e}")


        try:
            # Fetch the box score data for this game
            boxscore_url = f"https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{game_id}.json"
            response = requests.get(boxscore_url)
            response.raise_for_status()
            boxscore_data = response.json()

            # Process box score data to update players in the database
            db.process_boxscore_data(boxscore_data)

            with st.expander("View Player Statistics"):
                display_player_stats(game_id, home_team, away_team)

        except requests.exceptions.HTTPError as http_err:
            st.error(f"HTTP error occurred while fetching box score data: {http_err}")
        except Exception as e:
            st.error(f"An error occurred while processing box score data: {e}")

        st.markdown("---")

    db.commit()
    time.sleep(refresh_interval)
    st.rerun()

except Exception as e:
    st.error(f"Error updating data: {e}")
