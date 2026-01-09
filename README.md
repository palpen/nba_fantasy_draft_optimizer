# NBA Fantasy Optimizer 2026

## Overview
This tool automates the process of optimizing your NBA Fantasy Head-to-Head lineup. It replaces manual spreadsheet tracking by automatically fetching **real-time 2025-26 Season Stats** (or historical windows) and the **Weekly Schedule** to project your matchup results.

It analyzes your team vs. your opponent and recommends the best "Streamers" (Free Agents) to pick up to flip close categories.

## Features
*   **Live Data:** Uses the NBA API to get player averages and game schedules for the **2025-26 Season**.
*   **Time Travel & Backtesting:** Configure a `current_date` to simulate analysis from any point in the season.
*   **Custom Stats Window:** Set a `lookback` period (e.g., "Last 14 Days" or "Season") to analyze recent trends vs. long-term averages.
*   **Smart Projections:** Calculates weekly totals based on how many games each player has remaining in the specific week.
*   **Accurate Percentages:** Calculates FG% and FT% by projecting total Makes and Attempts.
*   **Swing Category Detection:** Automatically identifies which categories are "swings" (close margins) and prioritizes them.
*   **Streaming Recommendations:** Suggests the top available players who contribute most to the categories you need to flip.
*   **Markdown Reports:** Generates detailed, timestamped `.md` reports for every run.

## Setup

### 1. Installation from Scratch
If you are setting this up on a new machine, follow these steps to create the environment and install dependencies:

```bash
# 1. Clone or navigate to the project folder
cd "fantasy_draft_chooser v2"

# 2. Create a virtual environment
python3 -m venv venv

# 3. Activate the environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# .\venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt
```

### 2. Best Practices (Version Control)
**Note on `venv/`:** You should **NOT** include the `venv/` folder in version control (e.g., Git). Virtual environments contain machine-specific paths and binaries. Instead, always share the `requirements.txt` file.

### 3. Current Environment (Ready to Use)
If you are on the machine where this was created, the environment is already set up:
```bash
./venv/bin/python3 -m src.main
```

## Configuration & Usage

### 1. Configure Your Rosters & Settings
Open `inputs/rosters.json`. This is the control center for the tool.

```json
{
  "config": {
    "lookback": "14",            
    "current_date": "2026-01-08" 
  },
  "my_team": [
    "Nikola Jokic",
    "Jalen Williams"
  ],
  "opponent_team": [
    "Victor Wembanyama",
    "Luka Doncic"
  ]
}
```

*   **`lookback`**:
    *   Set to `"season"` for full season averages.
    *   Set to a number (e.g., `"7"`, `"14"`, `"30"`) to use stats from the last X days relative to the `current_date`.
*   **`current_date`**:
    *   Set to a specific date (YYYY-MM-DD) to run the analysis as if it were that day.
    *   Remove this line or set to `null` to automatically use **Today's Date**.
*   **`my_team` / `opponent_team`**:
    *   List the player names. Spelling is lenient (accents are handled automatically).

### 2. Run the Optimizer
```bash
./venv/bin/python3 -m src.main
```

### 3. View the Report
The tool will generate a new file in the current directory named `fantasy_report_YYYY-MM-DD_HHMMSS.md`. Open this file to see:

1.  **Analysis Context:** Date used, stats window, and schedule week.
2.  **Projected Totals:** Who wins each category based on remaining games.
3.  **Scouting Report:** Recommended pickups to flip specific "Swing Categories".

## How It Works (Under the Hood)

This tool is designed to be a "smart assistant" that automates the math you would typically do in a spreadsheet. Here is the technical breakdown of the optimization pipeline:

### 1. Data Fetching & Normalization
*   **Player Stats:** The tool uses `nba_api` to fetch the `LeagueDashPlayerStats` endpoint.
    *   *Lookback Window:* If you set `"lookback": "14"`, it calculates the specific date range (e.g., `2025-12-11` to `2025-12-25`) and requests stats *only* from that period.
    *   *Normalization:* To handle tricky names (e.g., "Nikola Jokić" vs "Nikola Jokic"), the script uses unicode normalization (NFD form) to strip accents and lowercase all names for robust matching.
*   **Schedule:** It fetches the game schedule for the *current week*. It then filters this schedule to count only the games remaining from "Today" (or your `current_date`) through Sunday.

### 2. The Projection Engine
For every player on your team and your opponent's team:
1.  **Games Left:** The tool looks up the player's team (e.g., "LAL") and counts how many times they appear in the remaining weekly schedule.
2.  **Stat Projection:**
    *   `Projected Stat = (Player Average) * (Games Left)`
    *   *Example:* If LeBron averages 25 PPG and plays 3 more times, he is projected to add 75 Points to your weekly total.
3.  **Percentage Calculation:**
    *   Unlike simple averages, FG% and FT% are calculated correctly by projecting total *Makes* and *Attempts* for the week.
    *   `Proj FG% = (Total Proj FGM) / (Total Proj FGA)`

### 3. The Recommendation Algorithm ("The Scout")
The tool doesn't just list good players; it specifically targets the categories you can actually flip.
1.  **Swing Identification:** It calculates the gap between you and your opponent for every category. If the gap is small (e.g., < 15 points, < 10 rebounds), it marks that category as a "Swing Category".
2.  **Availability Filter:** It looks at the pool of all active NBA players and removes anyone currently on your roster or your opponent's.
3.  **Weighted Scoring:** Available players are scored based on how much they contribute to the *Swing Categories* specifically.
    *   *Weights:* `STL` and `BLK` are weighted higher (x3.0) because they are scarcer and easier to flip with one good streamer than `PTS` (x1.0).
    *   `Score = Sum(Player_Avg_Stat * Games_Left * Category_Weight)` for all Swing Categories.

This ensures the top recommendation isn't just the best player, but the **best player for winning your specific close matchups**.

## Troubleshooting

*   **Missing Stats:**

    *   If you see `⚠️ Stats not found for [Name]...`, the tool will also suggest: **"Check if player was active during this period."**

    *   This usually means the player was injured, rested, or didn't play a game within your specified `lookback` window. Try increasing the `lookback` or checking the spelling.

*   **API Timeouts:** The NBA API can be slow. If the script hangs or errors, try again in a minute.
