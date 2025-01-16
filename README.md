# NBA Live Games Tracker 🏀

This Streamlit app provides real-time updates and statistics for live NBA games by integrating NBA's live data API. It tracks game scores, player statistics, and team performance while maintaining a local DuckDB database for historical data analysis.

Additionally has predictions for live games ( experimental ) which uses random forest machine learning! 

https://nbalive.streamlit.app/

## Features

- **Live Game Dashboard**: Displays live scores, game status, and player statistics for home and away teams.
- **Player Statistics**: Detailed stats including minutes played, points, rebounds, assists, shooting percentages, and more.
- **Database Integration**: Uses DuckDB to store and query game, team, and player data.
- **Custom Refresh Rates**: Adjustable refresh interval for real-time updates.
- **Data Visualization**: Interactive data tables for exploring historical game data.
- **Database Management**: Tools to reset and view database content directly from the app.



## Relational Database with Duckdb 

Database Schema and Relations:
The code creates four related tables with clear relationships:


games - Stores game information with game_id as primary key
teams - Stores team information with team_id as primary key
game_teams - Junction table linking games and teams with composite primary key (game_id, team_id)
players - Stores player statistics with composite primary key (player_id, game_id)


Relationships between tables:


game_teams has foreign key relationships to both games (game_id) and teams (team_id)
players has foreign key relationships to games (game_id) and teams (team_id)


SQL Operations:
The code uses standard SQL operations:


INSERT OR REPLACE for upserting data
SELECT queries for retrieving statistics
Joins (implied in the database design)
Primary key constraints
Timestamp tracking for data currency


Database Management:

def __init__(self, db_path='nba_live_stats.db'):
    self.conn = duckdb.connect(db_path)

The code establishes and maintains a persistent connection to a DuckDB database file.

ACID Properties:
The code maintains database consistency through:

Transaction management using commit()
Atomic updates using INSERT OR REPLACE
Primary key constraints ensuring data integrity
