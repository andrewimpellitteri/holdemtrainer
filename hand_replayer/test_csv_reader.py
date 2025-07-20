import pandas as pd

# --- Constants ---
PREFLOP_CSV_PATH = '../preflop_60k_train_set_game_scenario_information.csv'
POSTFLOP_CSV_PATH = '../postflop_500k_train_set_game_scenario_information.csv'

def analyze_csv(file_path, name):
    """Reads a CSV and prints its schema and a sample row."""
    print(f"--- Analyzing {name} CSV ---")
    try:
        df = pd.read_csv(file_path)
        print("Columns:", df.columns.tolist())
        if not df.empty:
            print("\nSample Row:")
            print(df.head(1).to_dict('records')[0])
        else:
            print("File is empty.")
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
    print("\n")

if __name__ == '__main__':
    analyze_csv(PREFLOP_CSV_PATH, "Pre-flop")
    analyze_csv(POSTFLOP_CSV_PATH, "Post-flop")

