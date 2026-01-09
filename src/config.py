import json
import os
import datetime

DEFAULT_ROSTER_PATH = os.path.join("inputs", "rosters.json")

def load_config(filepath=DEFAULT_ROSTER_PATH):
    """Loads the roster and configuration from the JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Configuration file not found at: {filepath}")
        
    with open(filepath, 'r') as f:
        data = json.load(f)
        
    config = data.get('config', {})
    
    # Set defaults if not present
    if 'lookback' not in config:
        config['lookback'] = 'season'
    
    # If current_date is missing or None, use today
    if not config.get('current_date'):
        config['current_date'] = datetime.datetime.now().strftime('%Y-%m-%d')
        
    return {
        "my_team": data.get('my_team', []),
        "opponent_team": data.get('opponent_team', []),
        "config": config
    }
