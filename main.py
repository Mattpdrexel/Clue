# main.py
from Game.Game import Game


def main():
    # Ask for game parameters
    print("Welcome to Clue!")
    try:
        num_players = int(input("How many human players? (2-6): "))
        num_players = max(2, min(6, num_players))  # Ensure between 2-6

        num_ai = int(input("How many AI players? (0-6): "))
        num_ai = max(0, min(6, num_ai))  # Ensure between 0-6

        # Ensure total players doesn't exceed 6
        total_players = num_players + num_ai
        if total_players > 6:
            print("Total players cannot exceed 6. Adjusting...")
            num_ai = max(0, 6 - num_players)

        print(f"Starting game with {num_players} human players and {num_ai} AI players.")
    except ValueError:
        print("Invalid input. Using default: 3 human players, 0 AI players.")
        num_players = 3
        num_ai = 0

    # Create and start the game
    game = Game(num_players, num_ai)

    # Print the initial game state (showing weapon positions)
    from Game.GameSetup import print_game_state
    print_game_state(game.mansion_board, game.character_board, game.characters, game.weapons)

    # Start the game
    game.play_game()


if __name__ == "__main__":
    main()