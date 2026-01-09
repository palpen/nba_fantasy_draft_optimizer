import pandas as pd
import datetime
from nba_api.stats.endpoints import leaguedashplayerstats, leaguegamefinder
from src.utils import normalize_name

def fetch_player_stats(lookback='season', current_date_str=None):
    """
    Fetches player stats for the 2025-26 season.
    Applies lookback filtering if specified.
    """
    api_params = {
        'season': '2025-26',
        'per_mode_detailed': 'PerGame'
    }
    
    # Handle Lookback Window
    if str(lookback).isdigit() and current_date_str:
        days = int(lookback)
        dt_current = datetime.datetime.strptime(current_date_str, '%Y-%m-%d')
        dt_from = dt_current - datetime.timedelta(days=days)
        
        api_params['date_from_nullable'] = dt_from.strftime('%m/%d/%Y')
        api_params['date_to_nullable'] = dt_current.strftime('%m/%d/%Y')
        print(f"   -> Fetching stats from {api_params['date_from_nullable']} to {api_params['date_to_nullable']}")
    else:
        print("   -> Fetching full 2025-26 season stats")

    stats = leaguedashplayerstats.LeagueDashPlayerStats(**api_params)
    df = stats.get_data_frames()[0]
    
    # Add normalized name column for easier matching
    df['NORM_NAME'] = df['PLAYER_NAME'].apply(normalize_name)
    return df

def fetch_weekly_schedule(week_start_date_str):
    """
    Fetches schedule for the week starting on the given date string (YYYY-MM-DD).
    Returns a DataFrame of remaining games per team.
    """
    start_date = datetime.datetime.strptime(week_start_date_str, '%Y-%m-%d')
    end_date = start_date + datetime.timedelta(days=6)
    
    # Check 2025-26 season
    game_finder = leaguegamefinder.LeagueGameFinder(season_nullable='2025-26', league_id_nullable='00')
    games = game_finder.get_data_frames()[0]
    
    games['GAME_DATE'] = pd.to_datetime(games['GAME_DATE'])
    
    # Filter for the specific week
    weekly_games = games[(games['GAME_DATE'] >= start_date) & (games['GAME_DATE'] <= end_date)]
    
    # We return the raw schedule df, filtering for "remaining" happens in the engine
    return weekly_games
