from flask import Flask, render_template, jsonify
import pandas as pd
import json
import os
import re

app = Flask(__name__)

# --- Constants ---
POSTFLOP_CSV_PATH = '../postflop_500k_train_set_game_scenario_information.csv'
POSITIONS = ['UTG', 'HJ', 'CO', 'BTN', 'SB', 'BB']

def get_villain_from_preflop(preflop_actions, hero_id):
    """Find the other player involved in the pot pre-flop."""
    participants = {preflop_actions[i] for i in range(0, len(preflop_actions), 2)}
    villains = participants - {hero_id}
    # In a heads-up post-flop scenario, there should be only one villain.
    return villains.pop() if villains else None

def parse_hand_history(row):
    """Parses a postflop CSV row into a detailed, structured action sequence."""
    hero_id = row['hero_position']
    preflop_actions_raw = row['preflop_action'].split('/')
    villain_id = get_villain_from_preflop(preflop_actions_raw, hero_id)

    players = [{"id": pos, "name": pos} for pos in POSITIONS]
    actions = []

    # 1. Pre-flop Actions
    for i in range(0, len(preflop_actions_raw), 2):
        if i + 1 < len(preflop_actions_raw):
            actor, move = preflop_actions_raw[i], preflop_actions_raw[i+1]
            actions.append({"type": "action", "player": actor, "action": move})

    # 2. Post-flop Actions by Street
    postflop_sequence = row['postflop_action'].split('/')
    board = []
    
    # Flop
    flop_cards = row['board_flop'].split()
    board.extend(flop_cards)
    actions.append({"type": "street", "street": "flop", "board": flop_cards})

    # Process actions until the turn card is dealt
    turn_card_index = postflop_sequence.index('dealcards') if 'dealcards' in postflop_sequence else len(postflop_sequence)
    for action_str in postflop_sequence[:turn_card_index]:
        parts = action_str.split('_')
        actor_id = hero_id if parts[0] == row['aggressor_position'] else villain_id
        actions.append({"type": "action", "player": actor_id, "action": f"{parts[1].lower()} {parts[2] if len(parts) > 2 else ''}".strip()})

    # Turn
    if 'dealcards' in postflop_sequence:
        turn_card = row['board_turn']
        board.append(turn_card)
        actions.append({"type": "street", "street": "turn", "board": [turn_card]})
        
        # Process actions between turn and river
        river_card_index = postflop_sequence.index('dealcards', turn_card_index + 1) if 'dealcards' in postflop_sequence[turn_card_index+1:] else len(postflop_sequence)
        for action_str in postflop_sequence[turn_card_index + 2:river_card_index]:
            parts = action_str.split('_')
            actor_id = hero_id if parts[0] == row['aggressor_position'] else villain_id
            actions.append({"type": "action", "player": actor_id, "action": f"{parts[1].lower()} {parts[2] if len(parts) > 2 else ''}".strip()})

    # River
    if 'board_river' in row and pd.notna(row['board_river']):
        river_card = row['board_river']
        if river_card not in board:
            board.append(river_card)
            actions.append({"type": "street", "street": "river", "board": [river_card]})
            # Process final actions
            for action_str in postflop_sequence[river_card_index + 2:]:
                parts = action_str.split('_')
                actor_id = hero_id if parts[0] == row['aggressor_position'] else villain_id
                actions.append({"type": "action", "player": actor_id, "action": f"{parts[1].lower()} {parts[2] if len(parts) > 2 else ''}".strip()})

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
    except (FileNotFoundError, KeyError) as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    if not os.path.exists('templates'):
        os.makedirs('templates')
    if not os.path.exists('static'):
        os.makedirs('static')
    app.run(debug=True, port=5001)
