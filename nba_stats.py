# Import required libraries
import requests  # For making HTTP requests to fetch live data from the NBA API
from datetime import datetime  # For handling date and time operations
import streamlit as st  # For building the interactive web app interface
import pandas as pd  # For data manipulation and creating data tables
import time  # For managing time-based operations, like refresh intervals
from nba_live_stats_db import NBALiveStatsDB  # Custom module for handling database operations

# Initialize the database for storing NBA game, team, and player data
db = NBALiveStatsDB()

# Function to format the minutes played in a human-readable format
def format_minutes(minutes_str):
    try:
        # Extract minutes and seconds from the input string (e.g., "PT12M34.56S")
        minutes = minutes_str.split('PT')[1].split('M')[0]
        seconds = minutes_str.split('M')[1].split('.')[0]
        # Return formatted time in "MM:SS" format
        return f"{minutes}:{seconds.zfill(2)}"
    except:
        # Return "0:00" if input format is invalid or minutes are not available
        return "0:00"

# Function to fetch player statistics for a specific game
def fetch_player_stats(game_id):
    try:
        # Send a GET request to fetch the game's box score data
        response = requests.get(
            f"https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{game_id}.json"
        )
        response.raise_for_status()  # Raise an error if the request fails
        data = response.json()  # Parse the response as JSON
        if not data or 'game' not in data:
            # Show a warning in the app if the game data is missing
            st.warning(f"Missing 'game' key in data for game ID {game_id}.")
            return None
        return data['game']  # Return the game data
    except Exception as e:
        # Show an error message in the app if fetching data fails
        st.error(f"Error fetching player stats: {e}")
        return None

# Function to display player statistics for both teams in a game
def display_player_stats(game_id, home_team, away_team):
    # Fetch game data using the game ID
    game_data = fetch_player_stats(game_id)
    if not game_data:
        st.warning("Player statistics are unavailable for this game.")
        return

    # Create tabs for home and away teams
    team_tab1, team_tab2 = st.tabs([
        f"{home_team['teamCity']} {home_team['teamName']}",
        f"{away_team['teamCity']} {away_team['teamName']}"
    ])

    # Display player stats for the home team
    with team_tab1:
        players = game_data.get('homeTeam', {}).get('players', [])
        if players:
            players_data = []
            for player in players:
                if player.get('played'):  # Only include players who played
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
                # Display the player stats in a table
                st.dataframe(pd.DataFrame(players_data), use_container_width=True)
            else:
                st.info("No statistics available for home team players.")

    # Display player stats for the away team
    with team_tab2:
        players = game_data.get('awayTeam', {}).get('players', [])
        if players:
            players_data = []
            for player in players:
                if player.get('played'):  # Only include players who played
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
                # Display the player stats in a table
                st.dataframe(pd.DataFrame(players_data), use_container_width=True)
            else:
                st.info("No statistics available for away team players.")

# Main application interface
st.title("🏀 NBA Live Games")  # App title

# Sidebar controls for refresh interval
refresh_interval = st.sidebar.slider("Refresh Interval (seconds):", min_value=5, max_value=120, value=30, step=5)

# Button to reset the database
if st.sidebar.button("Reset Database"):
    db.clear_database()  # Clear all data in the database

# Sidebar section to display database statistics
with st.sidebar:
    st.subheader("Database Statistics")
    stats = db.get_database_stats()
    st.write(f"Total Games Tracked: {stats[0]}")
    st.write(f"Total Teams: {stats[1]}")
    st.write(f"Total Players: {stats[2]}")
    view_database = st.checkbox("View Database")

# If "View Database" is checked, display database tables
if view_database:
    st.subheader("📊 View Database")
    selected_table = st.selectbox(
        "Select a table to view:",
        options=["Games", "Game Teams", "Players"]
    )
    try:
        # Display the selected table
        if selected_table == "Games":
            # Query all rows from the 'games' table in the database
            games_data = db.conn.execute("SELECT * FROM games").df()
            # Display the queried data as an interactive table in the app
            st.dataframe(games_data)
        elif selected_table == "Game Teams":
            # Query all rows from the 'game_teams' table in the database
            game_teams_data = db.conn.execute("SELECT * FROM game_teams").df()
            # Display the queried data as an interactive table in the app
            st.dataframe(game_teams_data)
        elif selected_table == "Players":
            # Query all rows from the 'players' table in the database
            players_data = db.conn.execute("SELECT * FROM players").df()
            # Display the queried data as an interactive table in the app
            st.dataframe(players_data)

    except Exception as e:
        st.error(f"Error fetching data from the {selected_table} table: {e}")

# Fetch live scoreboard data and process game information
try:
    response = requests.get("https://nba-prod-us-east-1-mediaops-stats.s3.amazonaws.com/NBA/liveData/scoreboard/todaysScoreboard_00.json")
    response.raise_for_status()  # Raise an error if the request fails
    scoreboard_data = response.json()  # Parse response as JSON
    db.process_scoreboard_data(scoreboard_data)  # Update database with game data

    games = scoreboard_data['scoreboard']['games']
    for game in games:
        game_id = game["gameId"]
        away_team = game["awayTeam"]
        home_team = game["homeTeam"]

        # Display game information
        st.subheader(f"{away_team['teamCity']} {away_team['teamName']} ({away_team['wins']}-{away_team['losses']}) at "
                     f"{home_team['teamCity']} {home_team['teamName']} ({home_team['wins']}-{home_team['losses']})")

        game_status = game["gameStatusText"]
        col1, col2 = st.columns([2, 1])

        with col1:
            # Display game status
            if game["gameStatus"] == 1:  # Pre-game
                game_time = datetime.strptime(game['gameEt'], '%Y-%m-%dT%H:%M:%SZ')
                st.info(f"🕒 Tip-off at {game_time.strftime('%I:%M %p ET')}")
                continue
            elif game["gameStatus"] == 2:  # Live game
                st.write(f"Q{game['period']} - {game['gameClock']}")
                st.header(f"{away_team['score']} - {home_team['score']}")
            else:  # Final score
                st.write("Final")
                st.header(f"{away_team['score']} - {home_team['score']}")

        with col2:
            # Display team statistics
            st.write("Team Stats")
            st.write(f"Timeouts: {away_team['timeoutsRemaining']} - {home_team['timeoutsRemaining']}")
            if away_team['inBonus'] != "None":
                st.write(f"{away_team['teamCity']} in bonus")
            if home_team['inBonus'] != "None":
                st.write(f"{home_team['teamCity']} in bonus")

        # Display player statistics for the game
        try:
            with st.expander("View Player Statistics"):
                display_player_stats(game_id, home_team, away_team)
        except Exception as e:
            st.error(f"Error displaying player stats: {e}")

        st.markdown("---")  # Separator for games

    db.commit()  # Save changes to the database
    time.sleep(refresh_interval)  # Wait for the refresh interval
    st.rerun()  # Restart the app to refresh data

except Exception as e:
    st.error(f"Error updating data: {e}")  # Handle errors gracefully
