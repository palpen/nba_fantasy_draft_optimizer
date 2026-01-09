# NBA Fantasy Optimizer - Automation Plan

## Goal
Automate the manual process of analyzing NBA fantasy matchups currently managed in `Scarbizzy 2021.xlsb.xlsx`. The goal is to maximize the probability of winning the weekly 9-category head-to-head matchup by leveraging real-time data from the `nba_api`.

## Core Logic & Rules
*   **Format:** 9-Category Head-to-Head (FG%, FT%, 3PT, Pts, Reb, Ast, Stl, Blk, TO).
*   **Cycle:** Monday to Sunday.
*   **Transaction Limit:** 3 pickups/drops per week.
*   **Next-Day Rule:** Players added today are only available for games starting tomorrow.
*   **Projections:** `Weekly Total = [Stat Average] * [Games Played this Week]`.

## Implementation Phases

### Phase 1: Environment & Data Foundation
*   Initialize Python environment with `pandas`, `openpyxl`, and `nba_api`.
*   Develop a `nba_data_service.py` to:
    *   Fetch active player IDs and metadata.
    *   Fetch the official NBA schedule for the current/specified week.
    *   Fetch up-to-date player stat averages (Season/Last 14 days).

### Phase 2: Spreadsheet Integration (The "Reader")
*   Create a script to read the active week's tab (e.g., 'Week5') from `Scarbizzy 2021.xlsb.xlsx`.
*   Extract the rosters for "My Team" and "Opponent" based on the layout identified in instructions.
*   Map player names to NBA IDs.

### Phase 3: The Optimization Logic (The "Brain")
*   **Dynamic Schedule Mapping:** Map each player's team to the live schedule to calculate `Gtot` (Games Total).
*   **Statistical Projection:** Automatically populate the "Black" columns (Stats) from the API and calculate "White" columns (Projected Totals).
*   **Matchup Simulation:** Sum up totals for both teams and determine the winner of each category.
*   **Gap Analysis:** Identify "Swing Categories" where the margin of victory/loss is small.

### Phase 4: Recommendation Engine (The "Action")
*   **Daily Management:** Identify days with benching conflicts or empty roster spots.
*   **Streaming Strategy:** 
    *   Search for available players (general top performers) who maximize "Swing Categories".
    *   Prioritize players based on the number of remaining games in the week.
    *   Account for the "Next-Day" rule when suggesting adds.

## Expected Output
A report or updated spreadsheet indicating:
1.  Projected final score (e.g., 5-4 Win).
2.  Which categories are at risk.
3.  Recommended players to pick up to flip specific categories before the 3-transaction limit is reached.
