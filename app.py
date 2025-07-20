from flask import Flask, render_template, request, jsonify, session
import json
import csv
import random
import os
from datetime import datetime
import pandas as pd

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a secure secret key

class PokerTrainer:
    def __init__(self):
        self.preflop_data = []
        self.postflop_data = []
        self.preflop_csv_data = []
        self.postflop_csv_data = []
        self.load_data()

    def convert_postflop_csv_to_scenarios(self, df):
        """Convert a dataframe row into a postflop scenario dict"""
        scenarios = []
        for _, row in df.iterrows():
            instruction = (
                f"You are a specialist in playing 6-handed No Limit Texas Hold'em.\n\n"
                f"• Your position: {row['hero_position']}\n"
                f"• Your hand: {row['holding']}\n\n"
                f"• Preflop action: {row['preflop_action']}\n"
                f"• Board: {row['board_flop']} {row['board_turn']} {row['board_river']}\n"
                f"• Postflop action: {row['postflop_action']}\n"
                f"• Pot size: {row['pot_size']}bb\n"
                f"• Available moves: {row['available_moves']}\n\n"
                f"What is your optimal decision?"
            )
            scenarios.append({
                "instruction": instruction,
                "output": row['correct_decision']
            })
        return scenarios


    def convert_csv_to_scenarios(self, df):
        """Convert a dataframe row into a simplified preflop-only scenario dict"""
        scenarios = []
        for _, row in df.iterrows():
            instruction = (
                f"You are a specialist in playing 6-handed No Limit Texas Hold'em.\n\n"
                f"• Your position: {row['hero_pos']}\n"
                f"• Your hand: {row['hero_holding']}\n\n"
                f"• Preflop history: {row['prev_line']}\n"
                f"• Number of players: {row['num_players']}\n"
                f"• Number of bets: {row['num_bets']}\n"
                f"• Pot size: {row['pot_size']}bb\n"
                f"• Available moves: {row['available_moves']}\n\n"
                f"What is your optimal decision?"
            )
            scenarios.append({
                "instruction": instruction,
                "output": row['correct_decision']
            })
        return scenarios



    def load_data(self):
        """Load poker data from CSV files and convert to scenarios."""

        # --- PREFLOP ---
        try:
            df = pd.read_csv('preflop_60k_train_set_game_scenario_information.csv')
            df.columns = df.columns.str.strip()
            print("Preflop CSV columns:", df.columns.tolist())

            required = {'hero_pos', 'hero_holding', 'prev_line', 'correct_decision',
                        'num_players', 'num_bets', 'available_moves', 'pot_size'}

            if required.issubset(df.columns):
                self.preflop_csv_data = df
                self.preflop_data = self.convert_csv_to_scenarios(df)
            else:
                missing = required - set(df.columns)
                raise KeyError(f"Missing columns: {missing}")
        except (FileNotFoundError, KeyError) as e:
            print(f"Preflop CSV load failed ({e}). Using sample data.")
            self.preflop_csv_data = pd.DataFrame()
            self.preflop_data = self.get_sample_preflop_data()

        # --- POSTFLOP ---
        try:
            df = pd.read_csv('postflop_500k_train_set_game_scenario_information.csv')
            df.columns = df.columns.str.strip()
            print("Postflop CSV columns:", df.columns.tolist())

            required = {'hero_position', 'holding', 'preflop_action', 'postflop_action',
                        'board_flop', 'board_turn', 'board_river',
                        'available_moves', 'pot_size', 'correct_decision'}

            if required.issubset(df.columns):
                self.postflop_csv_data = df
                self.postflop_data = self.convert_postflop_csv_to_scenarios(df)
            else:
                missing = required - set(df.columns)
                raise KeyError(f"Missing columns: {missing}")
        except (FileNotFoundError, KeyError) as e:
            print(f"Postflop CSV load failed ({e}). Using sample data.")
            self.postflop_csv_data = pd.DataFrame()
            self.postflop_data = self.get_sample_postflop_data()


    
    def get_sample_preflop_data(self):
        """Sample preflop data for demonstration"""
        return [
            {
                "instruction": "You are a specialist in playing 6-handed No Limit Texas Holdem. You are in the Big Blind position with AhAs. The action has been folded to the Button who raises to 2.5bb. The Small Blind folds. What is your optimal decision?",
                "output": "raise"
            },
            {
                "instruction": "You are a specialist in playing 6-handed No Limit Texas Holdem. You are in the Cut-Off position with 7h2d. The action has been folded to you. What is your optimal decision?",
                "output": "fold"
            },
            {
                "instruction": "You are a specialist in playing 6-handed No Limit Texas Holdem. You are in the Big Blind position with KdQs. UTG raises to 2.5bb, HJ folds, CO calls, BTN folds, SB folds. What is your optimal decision?",
                "output": "call"
            }
        ]
    
    def get_sample_postflop_data(self):
        """Sample postflop data for demonstration"""
        return [
            {
                "instruction": "You are a specialist in playing 6-handed No Limit Texas Holdem. You are in position with AsKd on a board of Ah7h2d. Your opponent checks to you. The pot is 12bb. What is your optimal decision?",
                "output": "bet"
            },
            {
                "instruction": "You are a specialist in playing 6-handed No Limit Texas Holdem. You are out of position with 8h8c on a board of Ks7h2d. You check, opponent bets 5bb into a 10bb pot. What is your optimal decision?",
                "output": "call"
            }
        ]
    
    def get_random_scenario(self, scenario_type='mixed'):
        """Get a random poker scenario"""
        if scenario_type == 'preflop':
            return random.choice(self.preflop_data)
        elif scenario_type == 'postflop':
            return random.choice(self.postflop_data)
        else:  # mixed
            all_scenarios = self.preflop_data + self.postflop_data
            return random.choice(all_scenarios)
    
    def get_stats(self):
        """Get statistics about the dataset"""
        return {
            'preflop_scenarios': len(self.preflop_data),
            'postflop_scenarios': len(self.postflop_data),
            'total_scenarios': len(self.preflop_data) + len(self.postflop_data)
        }

# Initialize the trainer
trainer = PokerTrainer()

@app.route('/')
def index():
    """Main page"""
    stats = trainer.get_stats()
    return render_template('index.html', stats=stats)

@app.route('/train')
def train():
    """Training page"""
    return render_template('train.html')

@app.route('/api/scenario')
def get_scenario():
    """API endpoint to get a new scenario"""
    scenario_type = request.args.get('type', 'mixed')
    scenario = trainer.get_random_scenario(scenario_type)
    
    # Store the correct answer in session
    session['correct_answer'] = scenario['output']
    session['scenario_id'] = random.randint(1, 1000000)
    
    return jsonify({
        'instruction': scenario['instruction'],
        'scenario_id': session['scenario_id']
    })

@app.route('/api/check-answer', methods=['POST'])
def check_answer():
    """API endpoint to check the user's answer"""
    data = request.get_json()
    user_answer = data.get('answer', '').lower().strip()
    scenario_id = data.get('scenario_id')
    
    # Check if this is the current scenario
    if scenario_id != session.get('scenario_id'):
        return jsonify({'error': 'Invalid scenario ID'}), 400
    
    correct_answer = session.get('correct_answer', '').lower().strip()
    is_correct = user_answer == correct_answer
    
    # Update session stats
    if 'stats' not in session:
        session['stats'] = {'correct': 0, 'total': 0}
    
    session['stats']['total'] += 1
    if is_correct:
        session['stats']['correct'] += 1
    
    return jsonify({
        'correct': is_correct,
        'correct_answer': correct_answer,
        'explanation': f"The optimal decision is '{correct_answer}'"
    })

@app.route('/api/stats')
def get_stats():
    """API endpoint to get user statistics"""
    stats = session.get('stats', {'correct': 0, 'total': 0})
    accuracy = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
    
    return jsonify({
        'correct': stats['correct'],
        'total': stats['total'],
        'accuracy': round(accuracy, 1)
    })

@app.route('/api/reset-stats', methods=['POST'])
def reset_stats():
    """API endpoint to reset user statistics"""
    session['stats'] = {'correct': 0, 'total': 0}
    return jsonify({'message': 'Statistics reset successfully'})

@app.route('/analysis')
def analysis():
    """Analysis page showing dataset insights"""
    return render_template('analysis.html')

@app.route('/api/dataset-analysis')
def dataset_analysis():
    """API endpoint for dataset analysis"""
    analysis_data = {
        'total_scenarios': len(trainer.preflop_data) + len(trainer.postflop_data),
        'preflop_count': len(trainer.preflop_data),
        'postflop_count': len(trainer.postflop_data)
    }
    
    # Analyze decision distribution if CSV data is available
    if not trainer.preflop_csv_data.empty:
        preflop_decisions = trainer.preflop_csv_data['correct_decision'].value_counts().to_dict()
        analysis_data['preflop_decisions'] = preflop_decisions
    
    if not trainer.postflop_csv_data.empty:
        postflop_decisions = trainer.postflop_csv_data['correct_decision'].value_counts().to_dict()
        analysis_data['postflop_decisions'] = postflop_decisions
    
    return jsonify(analysis_data)

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # Create static directory if it doesn't exist
    if not os.path.exists('static'):
        os.makedirs('static')
    
    app.run(debug=True)