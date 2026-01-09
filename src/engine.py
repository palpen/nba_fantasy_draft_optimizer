import pandas as pd
from src.utils import normalize_name

SCORING_WEIGHTS = {
    'PTS': 1.0, 'REB': 1.2, 'AST': 1.5, 
    'FG3M': 2.0, 'STL': 3.0, 'BLK': 3.0, 'TOV': -1.0
}

COUNTING_CATS = ['FG3M', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV']

def calculate_games_remaining(schedule_df, current_date_dt):
    """
    Returns a Series mapping TEAM_ABBREVIATION -> Games Remaining in the week.
    """
    remaining = schedule_df[schedule_df['GAME_DATE'] >= current_date_dt]
    # schedule_df has one row per team-game (LeagueGameFinder returns 2 rows per game, one for each team)
    # We group by TEAM_ABBREVIATION and count rows
    return remaining.groupby('TEAM_ABBREVIATION').size()

def project_team_totals(roster_names, stats_df, games_remaining_series, lookback_window):
    """
    Calculates projected weekly totals for a list of players.
    Returns: (DataFrame of individual projections, List of warning messages)
    """
    team_stats = []
    warnings = []
    
    for name in roster_names:
        norm_name = normalize_name(name)
        player_row = stats_df[stats_df['NORM_NAME'] == norm_name]
        
        if player_row.empty:
            period_msg = f"in the last {lookback_window} days" if str(lookback_window).isdigit() else "this season"
            msg = f"Stats not found for '{name}' {period_msg}. (Normalized: '{norm_name}'). Check if active."
            warnings.append(msg)
            continue
        
        p_data = player_row.iloc[0].to_dict()
        team_abbr = p_data['TEAM_ABBREVIATION']
        
        # Get games left (default to 0 if team not found in schedule)
        g_left = games_remaining_series.get(team_abbr, 0)
        p_data['G_LEFT'] = g_left
        
        # Project Counting Stats
        for cat in COUNTING_CATS:
            p_data[f'PROJ_{cat}'] = p_data[cat] * g_left
        
        # Project Shooting (for Percentages)
        p_data['PROJ_FGM'] = p_data['FGM'] * g_left
        p_data['PROJ_FGA'] = p_data['FGA'] * g_left
        p_data['PROJ_FTM'] = p_data['FTM'] * g_left
        p_data['PROJ_FTA'] = p_data['FTA'] * g_left
        
        team_stats.append(p_data)
        
    return pd.DataFrame(team_stats), warnings

def compare_matchup(my_proj_df, opp_proj_df):
    """
    Compares two projected dataframes and determines the winner per category.
    """
    results = {}
    
    # 1. Counting Stats
    for cat in COUNTING_CATS:
        m = my_proj_df[f'PROJ_{cat}'].sum()
        o = opp_proj_df[f'PROJ_{cat}'].sum()
        diff = m - o
        winner = "ME" if (diff > 0 and cat != 'TOV') or (diff < 0 and cat == 'TOV') else "OPP"
        results[cat] = {'my': m, 'opp': o, 'diff': diff, 'winner': winner}

    # 2. Percentages
    # FG%
    my_fgm = my_proj_df['PROJ_FGM'].sum(); my_fga = my_proj_df['PROJ_FGA'].sum()
    opp_fgm = opp_proj_df['PROJ_FGM'].sum(); opp_fga = opp_proj_df['PROJ_FGA'].sum()
    
    my_fgp = my_fgm / my_fga if my_fga > 0 else 0
    opp_fgp = opp_fgm / opp_fga if opp_fga > 0 else 0
    results['FG%'] = {'my': my_fgp, 'opp': opp_fgp, 'diff': my_fgp - opp_fgp, 'winner': "ME" if my_fgp > opp_fgp else "OPP"}
    
    # FT%
    my_ftm = my_proj_df['PROJ_FTM'].sum(); my_fta = my_proj_df['PROJ_FTA'].sum()
    opp_ftm = opp_proj_df['PROJ_FTM'].sum(); opp_fta = opp_proj_df['PROJ_FTA'].sum()
    
    my_ftp = my_ftm / my_fta if my_fta > 0 else 0
    opp_ftp = opp_ftm / opp_fta if opp_fta > 0 else 0
    results['FT%'] = {'my': my_ftp, 'opp': opp_ftp, 'diff': my_ftp - opp_ftp, 'winner': "ME" if my_ftp > opp_ftp else "OPP"}
    
    return results

def identify_swing_categories(matchup_results, diff_threshold=15):
    """
    Identifies categories where the difference is small.
    """
    swing_cats = []
    for cat in COUNTING_CATS:
        res = matchup_results[cat]
        if abs(res['diff']) < diff_threshold:
            swing_cats.append(cat)
    return swing_cats

def find_streamers(stats_df, rostered_names, games_remaining_series, swing_cats):
    """
    Finds top available players (not in rostered_names) who help with swing_cats.
    """
    # Default to all value if no swing cats
    target_cats = swing_cats if swing_cats else ['PTS', 'REB', 'AST', 'STL', 'BLK']
    
    available_players = []
    rostered_norm = [normalize_name(n) for n in rostered_names]
    
    for index, row in stats_df.iterrows():
        # Skip rostered
        if row['NORM_NAME'] in rostered_norm:
            continue
        
        team_abbr = row['TEAM_ABBREVIATION']
        g_left = games_remaining_series.get(team_abbr, 0)
        
        if g_left == 0:
            continue
            
        score = 0
        for cat in target_cats:
            val = row[cat]
            w = SCORING_WEIGHTS.get(cat, 1.0)
            score += (val * g_left * w)
            
        available_players.append({
            'Name': row['PLAYER_NAME'],
            'Team': team_abbr,
            'GamesLeft': g_left,
            'Score': score,
            'Cats': {c: round(row[c] * g_left, 1) for c in target_cats}
        })
        
    # Sort
    available_players.sort(key=lambda x: x['Score'], reverse=True)
    return available_players[:10]
