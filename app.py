
import json
import re
from flask import Flask, render_template, request, jsonify, session
import pandas as pd
import random
import os

# --- Constants ---
PREFLOP_CSV_PATH = 'preflop_60k_train_set_game_scenario_information.csv'
POSTFLOP_CSV_PATH = 'postflop_500k_train_set_game_scenario_information.csv'

PREFLOP_REQUIRED_COLS = {
    'hero_pos', 'hero_holding', 'prev_line', 'correct_decision',
    'num_players', 'num_bets', 'available_moves', 'pot_size'
}
POSTFLOP_REQUIRED_COLS = {
    'hero_position', 'holding', 'preflop_action', 'postflop_action',
    'board_flop', 'board_turn', 'board_river',
    'available_moves', 'pot_size', 'correct_decision'
}

# --- Formatting Helpers ---

def format_hand(hand_string):
    """Formats a hand string with Unicode suits and colors."""
    if not isinstance(hand_string, str):
        return hand_string

    suit_map = {
        's': '<span class="text-dark">♠</span>',
        'h': '<span class="text-danger">♥</span>',
        'd': '<span class="text-primary">♦</span>',
        'c': '<span class="text-success">♣</span>',
    }
    return re.sub(r'([AKQJT98765432])([shdc])', lambda m: m.group(1) + suit_map.get(m.group(2), m.group(2)), hand_string)

def format_preflop_action(action_str):
    """Converts a pre-flop action string into a readable sentence."""
    if not isinstance(action_str, str) or '/' not in action_str:
        return action_str
    parts = action_str.split('/')
    actions = []
    for i in range(0, len(parts), 2):
        if i + 1 < len(parts):
            actor, move = parts[i], parts[i+1]
            if 'bb' in move:
                actions.append(f"{actor} raises to {move}")
            else:
                actions.append(f"{actor} {move}s")
    return ", ".join(actions)

def format_postflop_action(action_str):
    """Converts a post-flop action string into a readable sentence."""
    if not isinstance(action_str, str):
        return action_str
    return action_str.replace('OOP_CHECK', 'Opponent checks').replace('IP_BET', 'Hero bets').replace('OOP_CALL', 'Opponent calls').replace('_', ' ').replace('dealcards', 'deal')


app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a secure secret key


class PokerTrainer:
    """Manages poker training data and scenarios."""

    def __init__(self):
        """Initializes the trainer by loading all poker data."""
        self.preflop_data = []
        self.postflop_data = []
        self.preflop_csv_data = pd.DataFrame()
        self.postflop_csv_data = pd.DataFrame()
        self.load_data()

    def convert_postflop_csv_to_scenarios(self, df):
        """Converts a DataFrame row into a postflop scenario dict."""
        scenarios = []
        for _, row in df.iterrows():
            try:
                moves = json.loads(row['available_moves'].replace("'", '"'))
            except (json.JSONDecodeError, AttributeError):
                moves = ["fold", "call", "raise"]
            scenarios.append({
                "type": "postflop",
                "position": row['hero_position'],
                "hand": format_hand(row['holding']),
                "preflop_action": format_preflop_action(row['preflop_action']),
                "board": format_hand(f"{row['board_flop']} {row['board_turn']} {row['board_river']}"),
                "postflop_action": format_postflop_action(row['postflop_action']),
                "pot_size": f"{row['pot_size']}bb",
                "available_moves": moves,
                "output": row['correct_decision']
            })
        return scenarios

    def convert_csv_to_scenarios(self, df):
        """Converts a DataFrame row into a simplified preflop-only scenario dict."""
        scenarios = []
        for _, row in df.iterrows():
            try:
                moves = json.loads(row['available_moves'].replace("'", '"'))
            except (json.JSONDecodeError, AttributeError):
                moves = ["fold", "call", "raise"]
            scenarios.append({
                "type": "preflop",
                "position": row['hero_pos'],
                "hand": format_hand(row['hero_holding']),
                "preflop_history": format_preflop_action(row['prev_line']),
                "num_players": row['num_players'],
                "num_bets": row['num_bets'],
                "pot_size": f"{row['pot_size']}bb",
                "available_moves": moves,
                "output": row['correct_decision']
            })
        return scenarios

    def _load_poker_data(self, file_path, required_columns, conversion_func, sample_func):
        """Helper to load data from a CSV file or use sample data."""
        try:
            df = pd.read_csv(file_path)
            df.columns = df.columns.str.strip()
            print(f"Loaded {file_path}. Columns: {df.columns.tolist()}")

            if not required_columns.issubset(df.columns):
                missing = required_columns - set(df.columns)
                raise KeyError(f"Missing required columns: {missing}")
            
            return df, conversion_func(df)

        except (FileNotFoundError, KeyError) as e:
            print(f"CSV load failed for {file_path}: {e}. Using sample data.")
            return pd.DataFrame(), sample_func()

    def load_data(self):
        """Load all poker data from CSV files and convert to scenarios."""
        self.preflop_csv_data, self.preflop_data = self._load_poker_data(
            PREFLOP_CSV_PATH,
            PREFLOP_REQUIRED_COLS,
            self.convert_csv_to_scenarios,
            self.get_sample_preflop_data
        )

        self.postflop_csv_data, self.postflop_data = self._load_poker_data(
            POSTFLOP_CSV_PATH,
            POSTFLOP_REQUIRED_COLS,
            self.convert_postflop_csv_to_scenarios,
            self.get_sample_postflop_data
        )

    def get_sample_preflop_data(self):
        """Returns sample preflop data for demonstration."""
        return [
            {
                "type": "preflop",
                "position": "Big Blind",
                "hand": format_hand("AhAs"),
                "preflop_history": "Folds to BTN, BTN raises to 2.5bb, SB folds.",
                "pot_size": "4bb",
                "available_moves": ["fold", "call", "raise"],
                "output": "raise"
            },
            {
                "type": "preflop",
                "position": "Cut-Off",
                "hand": format_hand("7h2d"),
                "preflop_history": "Action folds to you.",
                "pot_size": "1.5bb",
                "available_moves": ["fold", "raise"],
                "output": "fold"
            },
        ]

    def get_sample_postflop_data(self):
        """Returns sample postflop data for demonstration."""
        return [
            {
                "type": "postflop",
                "position": "In Position",
                "hand": format_hand("AsKd"),
                "board": format_hand("Ah7h2d"),
                "postflop_action": "Opponent checks.",
                "pot_size": "12bb",
                "available_moves": ["check", "bet"],
                "output": "bet"
            },
            {
                "type": "postflop",
                "position": "Out of Position",
                "hand": format_hand("8h8c"),
                "board": format_hand("Ks7h2d"),
                "postflop_action": "You check, opponent bets 5bb into 10bb pot.",
                "pot_size": "20bb",
                "available_moves": ["fold", "call", "raise"],
                "output": "call"
            }
        ]

    def get_random_scenario(self, scenario_type='mixed'):
        """Get a random poker scenario based on the selected type."""
        preflop_available = bool(self.preflop_data)
        postflop_available = bool(self.postflop_data)

        choices = []
        if scenario_type in ('mixed', 'preflop') and preflop_available:
            choices.extend(self.preflop_data)
        if scenario_type in ('mixed', 'postflop') and postflop_available:
            choices.extend(self.postflop_data)

        if not choices:
            return {
                "type": "error",
                "message": "No scenarios available for the selected type. Check data files.",
                "output": "",
                "available_moves": []
            }
        return random.choice(choices)

    def get_stats(self):
        """Get statistics about the loaded dataset."""
        return {
            'preflop_scenarios': len(self.preflop_data),
            'postflop_scenarios': len(self.postflop_data),
            'total_scenarios': len(self.preflop_data) + len(self.postflop_data)
        }


# --- Flask App ---
trainer = PokerTrainer()

@app.route('/')
def index():
    """Renders the main page with dataset statistics."""
    return render_template('index.html', stats=trainer.get_stats())


@app.route('/train')
def train():
    """Renders the training page."""
    return render_template('train.html')


@app.route('/api/scenario')
def get_scenario():
    """API endpoint to fetch a new poker scenario."""
    scenario_type = request.args.get('type', 'mixed')
    scenario = trainer.get_random_scenario(scenario_type)

    if scenario.get("type") == "error":
        return jsonify(scenario), 404

    session['correct_answer'] = scenario['output']
    session['scenario_id'] = random.randint(1, 1_000_000)

    # Add scenario_id to the scenario dict to be sent to the client
    scenario_with_id = scenario.copy()
    scenario_with_id['scenario_id'] = session['scenario_id']

    return jsonify(scenario_with_id)


@app.route('/api/check-answer', methods=['POST'])
def check_answer():
    """API endpoint to validate the user's answer."""
    data = request.get_json()
    user_answer = data.get('answer', '').lower().strip()
    scenario_id = data.get('scenario_id')
    
    if not data or scenario_id != session.get('scenario_id'):
        return jsonify({'error': 'Invalid or stale scenario. Please refresh.'}), 400
    
    correct_answer = session.get('correct_answer', '').lower().strip()
    is_correct = user_answer == correct_answer
    
    session.setdefault('stats', {'correct': 0, 'total': 0})
    
    session['stats']['total'] += 1
    if is_correct:
        session['stats']['correct'] += 1
    
    session.pop('scenario_id', None)  # Prevent re-answering

    return jsonify({
        'correct': is_correct,
        'correct_answer': correct_answer,
    })


@app.route('/api/stats')
def get_stats():
    """API endpoint to retrieve user's session statistics."""
    stats = session.get('stats', {'correct': 0, 'total': 0})
    total = stats.get('total', 0)
    correct = stats.get('correct', 0)
    accuracy = (correct / total * 100) if total > 0 else 0
    
    return jsonify({
        'correct': correct,
        'total': total,
        'accuracy': round(accuracy, 1)
    })


@app.route('/api/reset-stats', methods=['POST'])
def reset_stats():
    """API endpoint to reset user's session statistics."""
    session['stats'] = {'correct': 0, 'total': 0}
    return jsonify({'message': 'Statistics reset successfully.'})


@app.route('/analysis')
def analysis():
    """Renders the analysis page for dataset insights."""
    return render_template('analysis.html')


@app.route('/api/dataset-analysis')
def dataset_analysis():
    """API endpoint for high-level dataset analysis."""
    stats = trainer.get_stats()
    analysis_data = {
        'total_scenarios': stats['total_scenarios'],
        'preflop_count': stats['preflop_scenarios'],
        'postflop_count': stats['postflop_scenarios'],
        'preflop_decisions': {},
        'postflop_decisions': {}
    }
    
    if not trainer.preflop_csv_data.empty:
        analysis_data['preflop_decisions'] = trainer.preflop_csv_data['correct_decision'].value_counts().to_dict()
    
    if not trainer.postflop_csv_data.empty:
        analysis_data['postflop_decisions'] = trainer.postflop_csv_data['correct_decision'].value_counts().to_dict()
    
    return jsonify(analysis_data)


def setup_directories():
    """Creates 'templates' and 'static' directories if they don't exist."""
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)


if __name__ == '__main__':
    setup_directories()
    app.run(debug=True)
