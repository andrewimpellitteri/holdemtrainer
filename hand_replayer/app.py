from flask import Flask, render_template, jsonify
import pandas as pd
import json
import os
import re

app = Flask(__name__)

# --- Constants ---
POSTFLOP_CSV_PATH = '../postflop_500k_train_set_game_scenario_information.csv'
POSITIONS = ['SB', 'BB', 'UTG', 'HJ', 'CO', 'BTN']

def get_players_in_hand(preflop_actions_raw):
    actors = [preflop_actions_raw[i] for i in range(0, len(preflop_actions_raw), 2)]
    if len(actors) > 1:
        return list(set([actors[0], actors[-1]]))[:2]
    return actors[:2]

def parse_hand_history(row):
    """Parses a postflop CSV row into a detailed, robust action sequence with pot calculation."""
    preflop_actions_raw = row['preflop_action'].split('/')
    players_in_hand = get_players_in_hand(preflop_actions_raw)
    if len(players_in_hand) < 2: players_in_hand = ['UTG', 'BB']

    pos1_index = POSITIONS.index(players_in_hand[0]) if players_in_hand[0] in POSITIONS else -1
    pos2_index = POSITIONS.index(players_in_hand[1]) if players_in_hand[1] in POSITIONS else -1
    oop_player_id = players_in_hand[0] if pos1_index < pos2_index else players_in_hand[1]
    ip_player_id = players_in_hand[1] if pos1_index < pos2_index else players_in_hand[0]

    hero_id = ip_player_id if row['hero_position'] == 'IP' else oop_player_id
    villain_id = oop_player_id if row['hero_position'] == 'IP' else ip_player_id

    players = [{"id": pos, "name": pos} for pos in ['UTG', 'HJ', 'CO', 'BTN', 'SB', 'BB']]
    actions = []
    pot_size = 1.5  # SB (0.5) + BB (1.0)

    # 1. Pre-flop Actions
    for i in range(0, len(preflop_actions_raw), 2):
        if i + 1 < len(preflop_actions_raw):
            action_str = preflop_actions_raw[i+1]
            amount_match = re.search(r'([0-9.]+)', action_str)
            if amount_match:
                pot_size += float(amount_match.group(1))
            actions.append({"type": "action", "player": preflop_actions_raw[i], "action": action_str, "pot_size": round(pot_size, 2)})

    # 2. Post-flop Actions
    flop_cards = re.findall('..?', str(row['board_flop']))
    actions.append({"type": "street", "street": "flop", "board": flop_cards, "pot_size": round(pot_size, 2)})

    postflop_sequence = row['postflop_action'].split('/')
    current_street = 'flop'

    for action_str in postflop_sequence:
        if not action_str: continue

        if action_str == 'dealcards':
            board_card = ""
            if current_street == 'flop':
                current_street = 'turn'
                board_card = row['board_turn']
            elif current_street == 'turn':
                current_street = 'river'
                board_card = row['board_river']
            actions.append({"type": "street", "street": current_street, "board": [board_card], "pot_size": round(pot_size, 2)})
        else:
            parts = action_str.split('_')
            if len(parts) < 2: continue
            
            actor_label = parts[0]
            player_id = ip_player_id if actor_label == 'IP' else oop_player_id
            move = parts[1].lower()
            amount = float(parts[2]) if len(parts) > 2 else 0
            pot_size += amount
            
            actions.append({"type": "action", "player": player_id, "action": move, "amount": amount, "pot_size": round(pot_size, 2)})

    return {
        "players": players,
        "heroId": hero_id,
        "hand": row['holding'],
        "actions": actions,
        "available_moves": json.loads(row['available_moves'].replace("'", '"')),
        "correct_decision": row['correct_decision']
    }

@app.route('/')
def replayer():
    return render_template('replayer.html')

@app.route('/api/hand')
def get_hand():
    try:
        df = pd.read_csv(POSTFLOP_CSV_PATH)
        hand_data = df.sample(1).iloc[0]
        parsed_hand = parse_hand_history(hand_data)
        return jsonify(parsed_hand)
    except Exception as e:
        print(f"Error processing hand: {e}")
        return jsonify({"error": "Failed to parse hand history.", "details": str(e)}), 500

if __name__ == '__main__':
    if not os.path.exists('templates'):
        os.makedirs('templates')
    if not os.path.exists('static'):
        os.makedirs('static')
    app.run(debug=True, port=5001)