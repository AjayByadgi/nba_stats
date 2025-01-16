import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from nba_api.stats.endpoints import leaguegamefinder
from nba_api.stats.static import teams
import requests
import json
from datetime import datetime, timedelta

def fetch_player_stats(game_id):
    """
    Fetch detailed player statistics for a specific game from the NBA API
    """
    try:
        response = requests.get(
            f"https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{game_id}.json"
        )
        response.raise_for_status()
        data = response.json()
        if not data or 'game' not in data:
            print(f"Missing 'game' key in data for game ID {game_id}")
            return None
        return data['game']
    except Exception as e:
        print(f"Error fetching player stats: {e}")
        return None

def get_team_recent_games(team_abv, num_games= 50):
    """
    Get recent games for a team using the NBA API
    """
    nba_teams = teams.get_teams()
    team = [t for t in nba_teams if t['abbreviation'] == team_abv][0]
    team_id = team['id']
    
    gamefinder = leaguegamefinder.LeagueGameFinder(team_id_nullable=team_id)
    games = gamefinder.get_data_frames()[0]
    
    # Filter for recent seasons and sort by date
    games = games[games['SEASON_ID'].str[-4:].isin([ '2024', '2025'])]
    games = games.sort_values('GAME_DATE', ascending=False)
    
    return games.head(num_games)

def process_game_stats(game_data, team_name):
    """
    Process raw game data into usable features
    """
    if not game_data:
        return None
        
    is_home = game_data['homeTeam']["teamName"] == team_name
    team_data = game_data['homeTeam'] if is_home else game_data['awayTeam']
    
    # Process player statistics
    players = team_data.get('players', [])
    active_players = [p for p in players if p.get('played')]
    
    if not active_players:
        return None
        
    # Aggregate team statistics
    team_stats = {
        'total_points': team_data['score'],
        'is_home': 1 if is_home else 0,
        'num_players': len(active_players),
        'starters_points': 0,
        'bench_points': 0,
        
        'total_rebounds': 0,
        'total_assists': 0,
        'fg_percentage': 0,
        'three_pt_percentage': 0,
        'ft_percentage': 0
    }
    
    for player in active_players:
        stats = player.get('statistics', {})
        is_starter = player.get('starter') == '1'
        
        points = int(stats.get('points', 0))
        if is_starter:
            team_stats['starters_points'] += points
        else:
            team_stats['bench_points'] += points
            
        #team_stats['total_minutes'] += float(stats.get('minutes', '0').replace(':', '.'))
        team_stats['total_rebounds'] += int(stats.get('reboundsTotal', 0))
        team_stats['total_assists'] += int(stats.get('assists', 0))
        
        # Calculate shooting percentages
        fgm = int(stats.get('fieldGoalsMade', 0))
        fga = int(stats.get('fieldGoalsAttempted', 0))
        tpm = int(stats.get('threePointersMade', 0))
        tpa = int(stats.get('threePointersAttempted', 0))
        ftm = int(stats.get('freeThrowsMade', 0))
        fta = int(stats.get('freeThrowsAttempted', 0))
        
        if fga > 0:
            team_stats['fg_percentage'] += (fgm / fga) * 100
        if tpa > 0:
            team_stats['three_pt_percentage'] += (tpm / tpa) * 100
        if fta > 0:
            team_stats['ft_percentage'] += (ftm / fta) * 100
    
    # Average the percentages
    if len(active_players) > 0:
        team_stats['fg_percentage'] /= len(active_players)
        team_stats['three_pt_percentage'] /= len(active_players)
        team_stats['ft_percentage'] /= len(active_players)
    
    return team_stats

def create_game_features(home_team_abv, away_team_abv, num_recent_games=20):
    """
    Create features for prediction using recent games data from both teams,
    including win percentage.
    """
    home_recent_games = get_team_recent_games(home_team_abv, num_recent_games)
    away_recent_games = get_team_recent_games(away_team_abv, num_recent_games)
    
    home_features = []
    away_features = []
    
    # Calculate win percentage for both teams
    wins_home = home_recent_games[home_recent_games['WL'] == 'W'].shape[0]
    losses_home = home_recent_games[home_recent_games['WL'] == 'L'].shape[0]
    home_win_percentage = wins_home / max(wins_home + losses_home, 1)
    
    wins_away = away_recent_games[away_recent_games['WL'] == 'W'].shape[0]
    losses_away = away_recent_games[away_recent_games['WL'] == 'L'].shape[0]
    away_win_percentage = wins_away / max(wins_away + losses_away, 1)
    
    # Process recent games for both teams
    for _, game in home_recent_games.iterrows():
        stats = fetch_player_stats(game['GAME_ID'])
        if stats:
            processed_stats = process_game_stats(stats, home_team_abv)
            if processed_stats:
                home_features.append(processed_stats)
                
    for _, game in away_recent_games.iterrows():
        stats = fetch_player_stats(game['GAME_ID'])
        if stats:
            processed_stats = process_game_stats(stats, away_team_abv)
            if processed_stats:
                away_features.append(processed_stats)
    
    if not home_features or not away_features:
        return None
    
    # Calculate average features for both teams
    home_avg = pd.DataFrame(home_features).mean()
    away_avg = pd.DataFrame(away_features).mean()
    
    # Combine features for the matchup
    matchup_features = {
        # Home team features
        'home_avg_points': home_avg['total_points'],
        'home_avg_assists': home_avg['total_assists'],
        'home_avg_rebounds': home_avg['total_rebounds'],
        'home_fg_pct': home_avg['fg_percentage'],
        'home_three_pct': home_avg['three_pt_percentage'],
        'home_ft_pct': home_avg['ft_percentage'],
        'home_bench_scoring': home_avg['bench_points'],
        'home_win_percentage': home_win_percentage,  # Added feature
        
        # Away team features
        'away_avg_points': away_avg['total_points'],
        'away_avg_assists': away_avg['total_assists'],
        'away_avg_rebounds': away_avg['total_rebounds'],
        'away_fg_pct': away_avg['fg_percentage'],
        'away_three_pct': away_avg['three_pt_percentage'],
        'away_ft_pct': away_avg['ft_percentage'],
        'away_bench_scoring': away_avg['bench_points'],
        'away_win_percentage': away_win_percentage,  # Added feature
        
        # Differential features
        'point_diff': home_avg['total_points'] - away_avg['total_points'],
        'assist_diff': home_avg['total_assists'] - away_avg['total_assists'],
        'rebound_diff': home_avg['total_rebounds'] - away_avg['total_rebounds'],
        'bench_scoring_diff': home_avg['bench_points'] - away_avg['bench_points']
    }
    
    return pd.Series(matchup_features)

def train_prediction_model(home_team_abv, away_team_abv):
    """
    Train the prediction model using historical matchup data
    """
    # Get historical games
    home_games = get_team_recent_games(home_team_abv, 20)  # Use more games for training
    away_games = get_team_recent_games(away_team_abv, 20)
    
    # Create training dataset
    X = []
    y = []
    
    for _, game in home_games.iterrows():
        features = create_game_features(home_team_abv, away_team_abv)
        if features is not None:
            X.append(features)
            y.append(1 if game['WL'] == 'W' else 0)
    
    if not X:
        raise ValueError("No training data available")
    
    X = pd.DataFrame(X)
    y = np.array(y)
    
    # Split and scale data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train_scaled, y_train)
    
    return model, scaler, model.score(X_test_scaled, y_test)

def predict_upcoming_game(home_team_abv, away_team_abv):
    """
    Predict the outcome of an upcoming game
    """
    # Train model
    model, scaler, accuracy = train_prediction_model(home_team_abv, away_team_abv)
    
    # Get features for the upcoming game
    features = create_game_features(home_team_abv, away_team_abv)
    
    if features is None:
        return None
    
    # Make prediction
    features_scaled = scaler.transform(features.values.reshape(1, -1))
    probabilities = model.predict_proba(features_scaled)[0]
    
    return {
        'home_win_probability': probabilities[1],
        'away_win_probability': probabilities[0],
        'model_accuracy': accuracy
    }

# # Example usage
# home_team_abv = 'BOS'  # Celtics
# away_team_abv = 'NOP'  # Pelicans

# prediction = predict_upcoming_game(home_team_abv, away_team_abv)

# if prediction:
#     print(f"\nPrediction for {home_team_abv} vs {away_team_abv}:")
#     print(f"Model Accuracy: {prediction['model_accuracy']:.2%}")
#     print(f"{home_team_abv} win probability: {prediction['home_win_probability']:.2%}")
#     print(f"{away_team_abv} win probability: {prediction['away_win_probability']:.2%}")