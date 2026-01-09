import json
import pandas as pd
import datetime
import unicodedata
import os
from nba_data_service import get_player_stats, get_weekly_schedule

def normalize_name(name):
    """Removes accents and converts to lowercase for robust matching."""
    return "".join(
        c for c in unicodedata.normalize('NFD', name)
        if unicodedata.category(c) != 'Mn'
    ).lower().strip()

def load_rosters(filename='demo_rosters.json'):
    with open(filename, 'r') as f:
        return json.load(f)

def run_analysis(current_date_str=None):
    # 1. Load Rosters & Config
    rosters = load_rosters()
    config = rosters.get('config', {})
    
    # Priority: Function Argument > Config File > Today's Date
    if current_date_str is None:
        current_date_str = config.get('current_date')
    
    if current_date_str is None:
        current_date_str = datetime.datetime.now().strftime('%Y-%m-%d')

    # Prepare Markdown Output
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    report_filename = f"fantasy_report_{file_timestamp}.md"
    
    lookback = config.get('lookback', 'season')
    
    md_output = []
    def log(line=""):
        md_output.append(line)

    print(f"Running analysis... (Report will be saved to {report_filename})")
    
    log(f"# NBA Fantasy Optimization Report")
    log(f"**Report Generated:** {timestamp}  ")
    # 3. Fetch Schedule Setup
    dt_current = datetime.datetime.strptime(current_date_str, '%Y-%m-%d')
    # weekday(): Monday is 0, Sunday is 6
    week_start_dt = dt_current - datetime.timedelta(days=dt_current.weekday())
    week_start_str = week_start_dt.strftime('%Y-%m-%d')
    
    log(f"**Analysis Week Start:** {week_start_str}  ")
    log("")

    # 1.1 Load Rosters
    my_team_names = rosters['my_team']
    opp_team_names = rosters['opponent_team']
    
    # 2. Fetch Active Stats (2025-26)
    from nba_api.stats.endpoints import leaguedashplayerstats
    
    # Prepare API params based on lookback
    api_params = {
        'season': '2025-26',
        'per_mode_detailed': 'PerGame'
    }
    
    if str(lookback).isdigit():
        days = int(lookback)
        dt_from = dt_current - datetime.timedelta(days=days)
        api_params['date_from_nullable'] = dt_from.strftime('%m/%d/%Y')
        api_params['date_to_nullable'] = dt_current.strftime('%m/%d/%Y')
        log(f"> ℹ️ **Stats Period:** {api_params['date_from_nullable']} to {api_params['date_to_nullable']}  ")
    else:
        log(f"> ℹ️ **Stats Period:** Full 2025-26 Season  ")
    
    log("")
    
    stats = leaguedashplayerstats.LeagueDashPlayerStats(**api_params)
    stats_df = stats.get_data_frames()[0]
    
    # Normalize the names in the stats dataframe
    stats_df['NORM_NAME'] = stats_df['PLAYER_NAME'].apply(normalize_name)
    
    # 3. Fetch Schedule Execution
    schedule_df = get_weekly_schedule(week_start_str)
    
    today_dt = pd.to_datetime(current_date_str)
    remaining_schedule = schedule_df[schedule_df['GAME_DATE'] >= today_dt]
    
    # 4. Map Players to Stats & Schedule
    def get_team_totals(player_names):
        team_stats = []
        for name in player_names:
            norm_name = normalize_name(name)
            player_row = stats_df[stats_df['NORM_NAME'] == norm_name]
            
            if player_row.empty:
                period_msg = f"in the last {lookback} days" if str(lookback).isdigit() else "this season"
                warn_text = f"Stats not found for '{name}' {period_msg}. (Normalized check: '{norm_name}'). Check if player was active during this period."
                print(f"⚠️  {warn_text}")
                log(f"> ⚠️ **Warning:** {warn_text}")
                continue
            
            p_data = player_row.iloc[0].to_dict()
            team_abbr = p_data['TEAM_ABBREVIATION']
            
            p_games_left = remaining_schedule[remaining_schedule['TEAM_ABBREVIATION'] == team_abbr][0].sum()
            
            p_data['G_LEFT'] = p_games_left
            
            # Counting Stats
            cats = ['FG3M', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV']
            for cat in cats:
                p_data[f'PROJ_{cat}'] = p_data[cat] * p_games_left
            
            # Shooting Stats for Percentages
            p_data['PROJ_FGM'] = p_data['FGM'] * p_games_left
            p_data['PROJ_FGA'] = p_data['FGA'] * p_games_left
            p_data['PROJ_FTM'] = p_data['FTM'] * p_games_left
            p_data['PROJ_FTA'] = p_data['FTA'] * p_games_left
            
            team_stats.append(p_data)
        return pd.DataFrame(team_stats)

    my_proj = get_team_totals(my_team_names)
    opp_proj = get_team_totals(opp_team_names)
    
    # 5. Aggregate & Compare
    log("## Projected Totals (Rest of Week)")
    log("Only includes stats from games remaining in the current week.")
    log("")
    log("| Category | My Team | Opponent | Diff | Winner |")
    log("| :--- | :--- | :--- | :--- | :--- |")
    
    results = []
    
    # Counting Stats
    counting_cats = ['FG3M', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV']
    for cat in counting_cats:
        m = my_proj[f'PROJ_{cat}'].sum()
        o = opp_proj[f'PROJ_{cat}'].sum()
        diff = m - o
        
        # Determine winner
        winner = "ME" if (diff > 0 and cat != 'TOV') or (diff < 0 and cat == 'TOV') else "OPP"
        results.append(winner)
        
        # Formatting for markdown
        winner_str = f"**{winner}**" if winner == "ME" else winner
        diff_str = f"{diff:+.1f}"
        
        log(f"| {cat} | {m:.1f} | {o:.1f} | {diff_str} | {winner_str} |")

    # Percentages
    # FG%
    my_fgpct = my_proj['PROJ_FGM'].sum() / my_proj['PROJ_FGA'].sum() if my_proj['PROJ_FGA'].sum() > 0 else 0
    opp_fgpct = opp_proj['PROJ_FGM'].sum() / opp_proj['PROJ_FGA'].sum() if opp_proj['PROJ_FGA'].sum() > 0 else 0
    winner = "ME" if my_fgpct > opp_fgpct else "OPP"
    results.append(winner)
    winner_str = f"**{winner}**" if winner == "ME" else winner
    diff_str = f"{my_fgpct-opp_fgpct:+.3f}"
    log(f"| FG% | {my_fgpct:.3f} | {opp_fgpct:.3f} | {diff_str} | {winner_str} |")
    
    # FT%
    my_ftpct = my_proj['PROJ_FTM'].sum() / my_proj['PROJ_FTA'].sum() if my_proj['PROJ_FTA'].sum() > 0 else 0
    opp_ftpct = opp_proj['PROJ_FTM'].sum() / opp_proj['PROJ_FTA'].sum() if opp_proj['PROJ_FTA'].sum() > 0 else 0
    winner = "ME" if my_ftpct > opp_ftpct else "OPP"
    results.append(winner)
    winner_str = f"**{winner}**" if winner == "ME" else winner
    diff_str = f"{my_ftpct-opp_ftpct:+.3f}"
    log(f"| FT% | {my_ftpct:.3f} | {opp_ftpct:.3f} | {diff_str} | {winner_str} |")

    my_wins = results.count("ME")
    opp_wins = results.count("OPP")
    
    log("")
    log(f"### Projected Score: **Me {my_wins}** - {opp_wins} Opponent")
    log("")

    # 6. Streaming Recommendations
    log("## Scouting Report: Top Streaming Targets")
    
    # Identify Swing Categories (Difference < 15 for counting, < 0.02 for %)
    swing_cats = []
    for cat in counting_cats:
        m = my_proj[f'PROJ_{cat}'].sum()
        o = opp_proj[f'PROJ_{cat}'].sum()
        diff = abs(m - o)
        if diff < 15: # Arbitrary threshold for "close"
            swing_cats.append(cat)
            
    if not swing_cats:
        log("No specifically close categories found. Recommendations prioritized by overall value.")
        swing_cats = ['PTS', 'REB', 'AST', 'STL', 'BLK'] 
    else:
        log(f"**Targeting Swing Categories:** {', '.join(swing_cats)}")

    # Find available players (Not in my_team or opp_team)
    rostered_names = [normalize_name(n) for n in my_team_names + opp_team_names]
    
    available_players = []
    
    for index, row in stats_df.iterrows():
        n_name = row['NORM_NAME']
        if n_name in rostered_names:
            continue
            
        team_abbr = row['TEAM_ABBREVIATION']
        g_left = remaining_schedule[remaining_schedule['TEAM_ABBREVIATION'] == team_abbr][0].sum()
        
        if g_left == 0:
            continue
            
        score = 0
        weights = {'PTS': 1.0, 'REB': 1.2, 'AST': 1.5, 'FG3M': 2.0, 'STL': 3.0, 'BLK': 3.0, 'TOV': -1.0}
        
        for cat in swing_cats:
            val = row[cat]
            w = weights.get(cat, 1.0)
            score += (val * g_left * w)
            
        available_players.append({
            'Name': row['PLAYER_NAME'],
            'Team': team_abbr,
            'GamesLeft': g_left,
            'Score': score,
            'Cats': {c: round(row[c] * g_left, 1) for c in swing_cats}
        })
        
    # Sort by Score
    available_players.sort(key=lambda x: x['Score'], reverse=True)
    
    log("")
    log("| Rank | Player | Team | Games Left | Projected Swing Stats |")
    log("| :--- | :--- | :--- | :--- | :--- |")
    
    for i, p in enumerate(available_players[:10], 1):
        stats_str = ", ".join([f"**{k}**: {v}" for k,v in p['Cats'].items()])
        log(f"| {i} | {p['Name']} | {p['Team']} | {p['GamesLeft']} | {stats_str} |")

    # Write to file
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write("\n".join(md_output))
        
    print(f"Success! Report saved to: {os.path.abspath(report_filename)}")

if __name__ == "__main__":
    run_analysis()