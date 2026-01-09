import os
import datetime

def generate_markdown_report(context, matchup_results, warnings, streamers, output_dir="."):
    """
    Generates a Markdown report file.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    filename = f"fantasy_report_{file_timestamp}.md"
    filepath = os.path.join(output_dir, filename)
    
    lines = []
    def log(s=""):
        lines.append(s)
    
    log(f"# NBA Fantasy Optimization Report")
    log(f"**Generated:** {timestamp}  ")
    log(f"**Analysis Date:** {context['current_date']}  ")
    log(f"**Week Start:** {context['week_start']}  ")
    log(f"**Lookback:** {context['lookback']}  ")
    log("")
    
    # Warnings
    for w in warnings:
        log(f"> ⚠️ **Warning:** {w}")
    if warnings:
        log("")
        
    # Matchup Table
    log("## Projected Totals (Rest of Week)")
    log("| Category | My Team | Opponent | Diff | Winner |")
    log("| :--- | :--- | :--- | :--- | :--- |")
    
    my_wins = 0
    opp_wins = 0
    
    # Order: Counting then %
    cats_order = ['FG3M', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'FG%', 'FT%']
    
    for cat in cats_order:
        res = matchup_results[cat]
        
        # Format numbers
        if '%' in cat:
            my_val = f"{res['my']:.3f}"
            opp_val = f"{res['opp']:.3f}"
            diff_val = f"{res['diff']:+.3f}"
        else:
            my_val = f"{res['my']:.1f}"
            opp_val = f"{res['opp']:.1f}"
            diff_val = f"{res['diff']:+.1f}"
            
        winner_str = f"**{res['winner']}**" if res['winner'] == 'ME' else res['winner']
        
        if res['winner'] == 'ME': my_wins += 1
        else: opp_wins += 1
            
        log(f"| {cat} | {my_val} | {opp_val} | {diff_val} | {winner_str} |")
        
    log("")
    log(f"### Projected Score: **Me {my_wins}** - {opp_wins} Opponent")
    log("")
    
    # Streamers
    log("## Scouting Report: Top Streaming Targets")
    swing_cats = streamers['targets']
    log(f"**Targeting Swing Categories:** {', '.join(swing_cats)}")
    log("")
    log("| Rank | Player | Team | Games Left | Projected Swing Stats |")
    log("| :--- | :--- | :--- | :--- | :--- |")
    
    for i, p in enumerate(streamers['players'], 1):
        stats_str = ", ".join([f"**{k}**: {v}" for k,v in p['Cats'].items()])
        log(f"| {i} | {p['Name']} | {p['Team']} | {p['GamesLeft']} | {stats_str} |")
        
    # Write
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
        
    return filepath
