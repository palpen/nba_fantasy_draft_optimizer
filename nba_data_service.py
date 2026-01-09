from nba_api.stats.static import players
from nba_api.stats.endpoints import playercareerstats, leaguedashplayerstats
from nba_api.stats.library.parameters import SeasonAll
import pandas as pd
import datetime

def get_active_players():
    """Returns a DataFrame of all active NBA players."""
    all_players = players.get_active_players()
    return pd.DataFrame(all_players)

def get_player_stats(season='2025-26'):
    """Fetches season averages for all players for the current season."""
    stats = leaguedashplayerstats.LeagueDashPlayerStats(season=season, per_mode_detailed='PerGame')
    df = stats.get_data_frames()[0]
    # Filter for standard 9 categories
    cols = ['PLAYER_ID', 'PLAYER_NAME', 'TEAM_ABBREVIATION', 'GP', 'MIN', 'FG_PCT', 
            'FT_PCT', 'FG3M', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV']
    return df[cols]

def get_weekly_schedule(start_date_str):
    """
    Fetches the NBA schedule for the week starting at start_date_str (YYYY-MM-DD).
    """
    from nba_api.stats.endpoints import leaguegamefinder
    import datetime
    
    start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = start_date + datetime.timedelta(days=6)
    
    # We use leaguegamefinder to find games in the date range
    game_finder = leaguegamefinder.LeagueGameFinder(season_nullable='2025-26', league_id_nullable='00')
    games = game_finder.get_data_frames()[0]
    
    # Convert GAME_DATE to datetime
    games['GAME_DATE'] = pd.to_datetime(games['GAME_DATE'])
    
    # Filter for the specific week
    weekly_games = games[(games['GAME_DATE'] >= start_date) & (games['GAME_DATE'] <= end_date)]
    
    # We only need Team and Date to count games per team
    schedule_summary = weekly_games.groupby(['TEAM_ABBREVIATION', 'GAME_DATE']).size().reset_index()
    return schedule_summary

if __name__ == "__main__":
    print("Fetching active players...")
    p_df = get_active_players()
    print(f"Found {len(p_df)} active players.")
    print(p_df.head())
