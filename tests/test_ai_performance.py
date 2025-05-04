# test_ai_performance.py
from Game.TurnManagement import process_ai_turn
import random
import time
import csv
import os
import sys
import pandas as pd
from datetime import datetime

# Add project root to path for proper imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Patch GameSetup.initialize_game to use the correct file path
from Game.GameSetup import initialize_game
from Objects.Board import MansionBoard, CharacterBoard
from Objects.Character import Character
from Objects.Weapon import Weapon
from Data.Constants import CHARACTERS, WEAPONS
from Game.Game import Game


# Override initialize_game to use correct file paths
def patched_initialize_game():
    """Patched version of initialize_game that uses absolute paths"""
    # Load and create the mansion board with absolute path
    excel_path = os.path.join(project_root, "Data", "mansion_board_layout.xlsx")
    mansion_board_layout = pd.read_excel(excel_path, header=None)
    mansion_board = MansionBoard(mansion_board_layout)

    # Create the character board with the same dimensions as mansion board
    character_board = CharacterBoard(mansion_board.rows, mansion_board.cols)

    # Create character instances
    characters = {name: Character(name) for name in CHARACTERS}

    # Create weapon instances
    weapons = {name: Weapon(name) for name in WEAPONS}

    # Place all characters in the Clue room (with minimal output)
    setup_characters_in_clue_room(mansion_board, character_board, characters)

    # Place all weapons in the Clue room (with minimal output)
    setup_weapons_in_clue_room(weapons)

    return mansion_board, character_board, characters, weapons


def setup_weapons_in_clue_room(weapons):
    """Place all weapons in the Clue room (minimal output version)"""
    for name, weapon in weapons.items():
        weapon.move_to("Clue")


def setup_characters_in_clue_room(mansion_board, character_board, characters):
    """Place all characters in the Clue room (minimal output version)"""
    # Get cells for the Clue room
    clue_room_cells = mansion_board.get_room_cells("Clue")

    if not clue_room_cells:
        print("Error: Could not find cells for the Clue room!")
        return

    # Make sure we have enough cells for all characters
    if len(clue_room_cells) < len(characters):
        print(f"Error: Not enough cells in Clue room ({len(clue_room_cells)}) for all characters ({len(characters)})")
        return

    # Place each character in a different cell in the Clue room
    for (name, character), cell in zip(characters.items(), clue_room_cells):
        row, col = cell
        # Update the character's position
        character.move_to(("Clue", row, col))
        # Place the character on the board
        try:
            character_board.place(name, row, col)
        except ValueError:
            character_board.positions[name] = "Clue"


class PatchedGame(Game):
    """Game class with patched initialize_game method"""

    def __init__(self, num_human_players=1, num_ai_players=2):
        # Use patched initialize_game instead of the original
        self.mansion_board, self.character_board, self.characters, self.weapons = patched_initialize_game()

        # Game state variables
        self.game_over = False
        self.winner = None
        self.current_player_idx = 0

        # Set up players
        self.setup_players(num_human_players, num_ai_players)

        # Create the secret envelope (the solution)
        self.setup_solution()

        # Deal cards to players
        self.deal_cards()

        # Lists of all game elements
        self.character_names = list(self.characters.keys())
        self.weapon_names = list(self.weapons.keys())
        self.room_names = list(self.mansion_board.room_dict.keys())


def run_ai_game(verbose=False):
    """
    Run a complete game with AI players only and return statistics.

    Args:
        verbose (bool): Whether to print detailed game progress

    Returns:
        dict: Game statistics
    """
    # Create a game with 3 AI players using the patched Game class
    game = PatchedGame(0, 3)

    # Get the solution for later reference
    solution = game.solution

    if verbose:
        print("\nSecret solution:", solution)
        print("\nPlayers in the game:")
        for player in game.players:
            print(f"{player.character_name} holds cards: {[card[1] for card in player.hand]}")

    # Set a reasonable turn limit to prevent infinite games
    max_turns = 100
    current_turn = 0

    start_time = time.time()

    while not game.game_over and current_turn < max_turns:
        current_turn += 1

        if verbose:
            print(f"\n--- Turn {current_turn} ---")

        # Get current player
        current_player = game.players[game.current_player_idx]

        # Skip eliminated players
        if current_player.eliminated:
            if verbose:
                print(f"\n{current_player.character_name}'s turn is skipped (eliminated).")
            game.current_player_idx = (game.current_player_idx + 1) % len(game.players)
            continue

        # Process turn for AI player (with minimal output if not verbose)
        if not verbose:
            # Temporarily redirect stdout to suppress output
            import sys, io
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()

        process_ai_turn(game, current_player)

        if not verbose:
            # Restore stdout
            sys.stdout = old_stdout

        # Move to next player
        game.current_player_idx = (game.current_player_idx + 1) % len(game.players)

        # Check if all players have been eliminated
        if all(player.eliminated for player in game.players):
            if verbose:
                print("\nAll players have been eliminated. Game over!")
            game.end_game()
            break

    end_time = time.time()
    game_duration = end_time - start_time

    # Check if we hit the turn limit
    if current_turn >= max_turns and not game.game_over:
        if verbose:
            print(f"\nReached maximum number of turns ({max_turns}). Forcing game end.")
        game.end_game()

    # Game statistics
    stats = {
        "turns": current_turn,
        "duration": game_duration,
        "winner": game.winner.character_name if game.winner else None,
        "all_eliminated": all(player.eliminated for player in game.players),
        "solution": solution,
        "eliminated_count": sum(1 for player in game.players if player.eliminated)
    }

    if verbose:
        print(f"\nGame completed in {current_turn} turns ({game_duration:.2f} seconds)")
        print(f"Solution was: {solution[0]} in the {solution[2]} with the {solution[1]}")

        if game.winner:
            print(f"Winner: {game.winner.character_name}")
        else:
            print("No winner")

        print(f"Eliminated players: {stats['eliminated_count']}/{len(game.players)}")

        print("\nPlayer statuses:")
        for player in game.players:
            status = "Winner" if game.winner == player else "Eliminated" if player.eliminated else "Active"
            print(f"- {player.character_name}: {status}")

    return stats


def run_multiple_games(num_games=10, output_file=None, verbose=False):
    """
    Run multiple games and collect statistics.

    Args:
        num_games (int): Number of games to run
        output_file (str): Path to CSV file to save results
        verbose (bool): Whether to print detailed game progress
    """
    all_stats = []
    winners = {}
    total_turns = 0
    total_time = 0
    total_eliminations = 0
    games_with_winners = 0

    print(f"Running {num_games} AI vs AI games...")

    for i in range(num_games):
        print(f"Game {i + 1}/{num_games}...", end="", flush=True)
        stats = run_ai_game(verbose=verbose)
        all_stats.append(stats)

        # Update aggregate stats
        total_turns += stats["turns"]
        total_time += stats["duration"]
        total_eliminations += stats["eliminated_count"]

        if stats["winner"]:
            games_with_winners += 1
            winners[stats["winner"]] = winners.get(stats["winner"], 0) + 1

        print(f" completed in {stats['turns']} turns ({stats['duration']:.2f}s)")

    # Summary statistics
    print("\n===== SUMMARY STATISTICS =====")
    print(f"Total games: {num_games}")
    print(f"Games with winners: {games_with_winners} ({games_with_winners / num_games * 100:.1f}%)")
    print(f"Average turns per game: {total_turns / num_games:.1f}")
    print(f"Average game duration: {total_time / num_games:.2f} seconds")
    print(f"Average eliminations per game: {total_eliminations / num_games:.1f}")

    print("\nWinner distribution:")
    for character, count in sorted(winners.items(), key=lambda x: x[1], reverse=True):
        print(f"- {character}: {count} wins ({count / num_games * 100:.1f}%)")

    # Export to CSV if requested
    if output_file:
        # Ensure the Output directory exists
        output_dir = os.path.join(project_root, "Output")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Create full path for output file
        output_path = os.path.join(output_dir, os.path.basename(output_file))

        with open(output_path, 'w', newline='') as csvfile:
            fieldnames = ['game', 'turns', 'duration', 'winner', 'all_eliminated',
                          'solution', 'eliminated_count']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for i, stats in enumerate(all_stats):
                row = {
                    'game': i + 1,
                    'turns': stats['turns'],
                    'duration': stats['duration'],
                    'winner': stats['winner'] or 'None',
                    'all_eliminated': stats['all_eliminated'],
                    'solution': ' '.join(str(x) for x in stats['solution']),
                    'eliminated_count': stats['eliminated_count']
                }
                writer.writerow(row)

            print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    # Set random seed for reproducibility
    random.seed(42)

    # Generate a filename based on the current time
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"ai_game_results_{timestamp}.csv"

    # Run games with 3 AI players each
    num_games = 10
    print(f"Running {num_games} games with 3 AI players each")

    # You can enable verbose mode to see detailed game progress
    verbose = False

    # Run the games and save results
    run_multiple_games(num_games, output_file, verbose)

    # If you want to see a detailed playthrough of a single game, uncomment:
    # print("\n\n===== DETAILED GAME PLAYTHROUGH =====")
    # run_ai_game(verbose=True)