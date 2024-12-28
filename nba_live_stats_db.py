import duckdb
from datetime import datetime

class NBALiveStatsDB:
    def __init__(self, db_path='nba_live_stats.db'):
        self.conn = duckdb.connect(db_path)
        self.create_tables()
    
    def create_tables(self):
        # Games table - from scoreboard data
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS games (
                game_id VARCHAR PRIMARY KEY,
                gameStatus INTEGER,
                gameStatusText VARCHAR,
                period INTEGER,
                gameClock VARCHAR,
                gameTimeUTC TIMESTAMP,
                gameEt TIMESTAMP,
                regulationPeriods INTEGER,
                seriesGameNumber VARCHAR,
                seriesText VARCHAR,
                last_updated TIMESTAMP
            )
        """)
        
        # Teams table - combines data from scoreboard and boxscore
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS teams (
                team_id INTEGER PRIMARY KEY,
                team_name VARCHAR,
                team_city VARCHAR,
                team_tricode VARCHAR,
                wins INTEGER,
                losses INTEGER
            )
        """)
        
        # Game Teams table - team stats for specific games
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS game_teams (
                game_id VARCHAR,
                team_id INTEGER,
                is_home BOOLEAN,
                score INTEGER,
                in_bonus VARCHAR,
                timeouts_remaining INTEGER,
                points_period1 INTEGER,
                last_updated TIMESTAMP,
                PRIMARY KEY (game_id, team_id)
            )
        """)
        
        # Players table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS players (
                player_id INTEGER,
                team_id INTEGER,
                game_id VARCHAR,
                jersey_num VARCHAR,
                name VARCHAR,
                position VARCHAR,
                starter BOOLEAN,
                minutes VARCHAR,
                points INTEGER,
                rebounds INTEGER,
                assists INTEGER,
                field_goals_made INTEGER,
                field_goals_attempted INTEGER,
                field_goals_percentage DOUBLE,
                three_pointers_made INTEGER,
                three_pointers_attempted INTEGER,
                free_throws_made INTEGER,
                free_throws_attempted INTEGER,
                plus_minus DOUBLE,
                last_updated TIMESTAMP,
                PRIMARY KEY (player_id, game_id)
            )
        """)


    def process_scoreboard_data(self, scoreboard_data):
        games = scoreboard_data['scoreboard']['games']
        current_time = datetime.now()
        
        for game in games:
            # Insert game data
            self.conn.execute("""
                INSERT OR REPLACE INTO games (
                    game_id, gameStatus, gameStatusText,
                    period, gameClock, gameTimeUTC, gameEt,
                    regulationPeriods, seriesGameNumber, seriesText,
                    last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                game['gameId'], game['gameStatus'],
                game['gameStatusText'], game['period'], game['gameClock'],
                game['gameTimeUTC'], game['gameEt'], game['regulationPeriods'],
                game['seriesGameNumber'], game['seriesText'], current_time
            ])
            
            # Process home team
            home_team = game['homeTeam']
            self.conn.execute("""
                INSERT OR REPLACE INTO teams (
                    team_id, team_name, team_city, team_tricode,
                    wins, losses
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, [
                home_team['teamId'], home_team['teamName'],
                home_team['teamCity'], home_team['teamTricode'],
                home_team['wins'], home_team['losses']
            ])
            
            # Process away team
            away_team = game['awayTeam']
            self.conn.execute("""
                INSERT OR REPLACE INTO teams (
                    team_id, team_name, team_city, team_tricode,
                    wins, losses
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, [
                away_team['teamId'], away_team['teamName'],
                away_team['teamCity'], away_team['teamTricode'],
                away_team['wins'], away_team['losses']
            ])
            
            # Insert game_teams data
            self.conn.execute("""
                INSERT OR REPLACE INTO game_teams (
                    game_id, team_id, is_home, score, in_bonus,
                    timeouts_remaining, points_period1, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                game['gameId'], home_team['teamId'], True,
                home_team['score'], home_team['inBonus'],
                home_team['timeoutsRemaining'],
                home_team['periods'][0]['score'], current_time
            ])
            
            self.conn.execute("""
                INSERT OR REPLACE INTO game_teams (
                    game_id, team_id, is_home, score, in_bonus,
                    timeouts_remaining, points_period1, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                game['gameId'], away_team['teamId'], False,
                away_team['score'], away_team['inBonus'],
                away_team['timeoutsRemaining'],
                away_team['periods'][0]['score'], current_time
            ])

    def process_boxscore_data(self, boxscore_data):
        game_data = boxscore_data['game']
        game_id = game_data['gameId']
        current_time = datetime.now()
        
        # Process home team players
        for player in game_data['homeTeam']['players']:
            if player.get('played') == '1':
                stats = player['statistics']
                self.conn.execute("""
                    INSERT OR REPLACE INTO players (
                        player_id, team_id, game_id, jersey_num, name,
                        position, starter, minutes, points, rebounds,
                        assists, field_goals_made, field_goals_attempted,
                        field_goals_percentage, three_pointers_made,
                        three_pointers_attempted, free_throws_made,
                        free_throws_attempted, plus_minus, last_updated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    player['personId'], game_data['homeTeam']['teamId'],
                    game_id, player['jerseyNum'], player['name'],
                    player.get('position', ''), player['starter'] == '1',
                    stats['minutes'], stats['points'], stats['reboundsTotal'],
                    stats['assists'], stats['fieldGoalsMade'],
                    stats['fieldGoalsAttempted'], stats['fieldGoalsPercentage'],
                    stats['threePointersMade'], stats['threePointersAttempted'],
                    stats['freeThrowsMade'], stats['freeThrowsAttempted'],
                    stats['plusMinusPoints'], current_time
                ])
        
        # Process away team players
        for player in game_data['awayTeam']['players']:
            if player.get('played') == '1':
                stats = player['statistics']
                self.conn.execute("""
                    INSERT OR REPLACE INTO players (
                        player_id, team_id, game_id, jersey_num, name,
                        position, starter, minutes, points, rebounds,
                        assists, field_goals_made, field_goals_attempted,
                        field_goals_percentage, three_pointers_made,
                        three_pointers_attempted, free_throws_made,
                        free_throws_attempted, plus_minus, last_updated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    player['personId'], game_data['awayTeam']['teamId'],
                    game_id, player['jerseyNum'], player['name'],
                    player.get('position', ''), player['starter'] == '1',
                    stats['minutes'], stats['points'], stats['reboundsTotal'],
                    stats['assists'], stats['fieldGoalsMade'],
                    stats['fieldGoalsAttempted'], stats['fieldGoalsPercentage'],
                    stats['threePointersMade'], stats['threePointersAttempted'],
                    stats['freeThrowsMade'], stats['freeThrowsAttempted'],
                    stats['plusMinusPoints'], current_time
                ])

    def get_database_stats(self):
        return self.conn.execute("""
            SELECT 
                (SELECT COUNT(DISTINCT game_id) FROM games) as total_games,
                (SELECT COUNT(DISTINCT team_id) FROM teams) as total_teams,
                (SELECT COUNT(DISTINCT player_id) FROM players) as total_players
        """).fetchone()



    def clear_database(self):
            """
            Drops all tables and recreates them to ensure schema consistency.
            """
            try:
                # Drop tables if they exist
                self.conn.execute("DROP TABLE IF EXISTS games")
                self.conn.execute("DROP TABLE IF EXISTS teams")
                self.conn.execute("DROP TABLE IF EXISTS game_teams")
                self.conn.execute("DROP TABLE IF EXISTS players")
                
                # Recreate tables using the current schema
                self.create_tables()
                print("Database cleared and tables recreated successfully.")
            except Exception as e:
                print(f"Error clearing the database: {e}")
    def commit(self):
        self.conn.commit()