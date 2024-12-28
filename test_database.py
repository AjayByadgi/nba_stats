import duckdb

# Connect to the database


conn = duckdb.connect('nba_live_stats.db')

# Example queries to verify the data
print("Games Table:")
print(conn.execute("SELECT * FROM games LIMIT 5").fetchdf())  # Fetch and display 5 rows from games

print("\nTeams Table:")
print(conn.execute("SELECT * FROM teams LIMIT 5").fetchdf())  # Fetch and display 5 rows from teams

print("\nPlayer Stats Table:")
print(conn.execute("SELECT * FROM player_stats LIMIT 5").fetchdf())  # Fetch and display 5 rows from player_stats

# Check the number of rows in each table
print("\nRow Counts:")
print(conn.execute("SELECT COUNT(*) AS games_count FROM games").fetchdf())
print(conn.execute("SELECT COUNT(*) AS teams_count FROM teams").fetchdf())
print(conn.execute("SELECT COUNT(*) AS player_stats_count FROM player_stats").fetchdf()) 