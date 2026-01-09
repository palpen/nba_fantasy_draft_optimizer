import sys
import argparse
import datetime
from src.config import load_config
from src.api import fetch_player_stats, fetch_weekly_schedule
from src.engine import (
    calculate_games_remaining, 
    project_team_totals, 
    compare_matchup, 
    identify_swing_categories, 
    find_streamers
)
from src.report import generate_markdown_report

def main():
    print("--- NBA Fantasy Optimizer ---")
    
    # Parse CLI Arguments
    parser = argparse.ArgumentParser(description="NBA Fantasy Optimizer")
    parser.add_argument(
        "--config", 
        type=str, 
        default="inputs/rosters.json", 
        help="Path to the rosters.json configuration file"
    )
    args = parser.parse_args()
    
    # 1. Config
    try:
        data = load_config(args.config)
        config = data['config']
        my_team = data['my_team']
        opp_team = data['opponent_team']
    except Exception as e:
        print(f"Error loading config: {e}")
        return

    current_date_str = config['current_date']
    lookback = config['lookback']
    
    print(f"1. Configuration Loaded")
    print(f"   - File: {args.config}")
    print(f"   - Date: {current_date_str}")
    print(f"   - Lookback: {lookback}")

    # 2. Data Fetching
    print("2. Fetching Data...")
    stats_df = fetch_player_stats(lookback, current_date_str)
    
    # Calculate Week Start
    dt_current = datetime.datetime.strptime(current_date_str, '%Y-%m-%d')
    week_start_dt = dt_current - datetime.timedelta(days=dt_current.weekday())
    week_start_str = week_start_dt.strftime('%Y-%m-%d')
    
    schedule_df = fetch_weekly_schedule(week_start_str)
    print(f"   - Schedule fetched for week of {week_start_str}")

    # 3. Engine Execution
    print("3. Running Optimization Engine...")
    
    # Games Remaining
    games_remaining = calculate_games_remaining(schedule_df, dt_current)
    
    # Projections
    my_proj, my_warn = project_team_totals(my_team, stats_df, games_remaining, lookback)
    opp_proj, opp_warn = project_team_totals(opp_team, stats_df, games_remaining, lookback)
    
    all_warnings = my_warn + opp_warn
    for w in all_warnings:
        print(f"   ⚠️  {w}")

    # Matchup Analysis
    results = compare_matchup(my_proj, opp_proj)
    
    # Scouting
    swing_cats = identify_swing_categories(results)
    rostered = my_team + opp_team
    top_picks = find_streamers(stats_df, rostered, games_remaining, swing_cats)
    
    # 4. Reporting
    print("4. Generating Report...")
    context = {
        'current_date': current_date_str,
        'week_start': week_start_str,
        'lookback': lookback
    }
    
    report_path = generate_markdown_report(
        context, 
        results, 
        all_warnings, 
        {'targets': swing_cats, 'players': top_picks}
    )
    
    print(f"Success! Report saved to: {report_path}")

if __name__ == "__main__":
    main()
