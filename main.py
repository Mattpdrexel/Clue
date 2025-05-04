# main.py
from Game.Game import Game


def main():
    # Ask for game parameters
    print("Welcome to Clue!")
    try:
        num_players = int(input("How many human players? (0-6): "))  # Changed to allow 0 humans
        num_players = max(0, min(6, num_players))  # Ensure between 0-6

        num_ai = int(input("How many AI players? (0-6): "))
        num_ai = max(0, min(6, num_ai))  # Ensure between 0-6

        # Ensure total players is between 3-6
        total_players = num_players + num_ai
        if total_players < 3:
            print("Total players must be at least 3. Adding AI players...")
            num_ai = max(3 - num_players, num_ai)
        if total_players > 6:
            print("Total players cannot exceed 6. Adjusting...")
            if num_players > 0:
                num_ai = max(0, 6 - num_players)
            else:
                num_ai = 6

        print(f"Starting game with {num_players} human players and {num_ai} AI players.")

        # If running in all-AI mode, automatically continue between turns
        auto_continue = num_players == 0

    except ValueError:
        print("Invalid input. Using default: 0 human players, 3 AI players.")
        num_players = 0
        num_ai = 3
        auto_continue = True

    # Create and start the game
    game = Game(num_players, num_ai)

    # Print the initial game state (showing weapon positions)
    from Game.GameSetup import print_game_state
    print_game_state(game.mansion_board, game.character_board, game.characters, game.weapons)

    # Start the game
    if auto_continue:
        # Run the game without waiting for input between turns
        play_game_auto(game)
    else:
        # Normal game with input between turns
        game.play_game()

def play_game_auto(game):
    """Modified game loop that doesn't wait for input between turns"""
    print("\nStarting the game of Clue with all AI players!")

    # Set a reasonable turn limit to prevent infinite games
    max_turns = 100
    current_turn = 0

    while not game.game_over and current_turn < max_turns:
        current_turn += 1
        print(f"\n--- Turn {current_turn} ---")

        # Get current player
        current_player = game.players[game.current_player_idx]

        # Skip eliminated players
        if current_player.eliminated:
            print(f"\n{current_player.character_name}'s turn is skipped (eliminated).")
            game.current_player_idx = (game.current_player_idx + 1) % len(game.players)
            continue

        # Process turn for AI player
        from Game.TurnManagement import process_ai_turn
        process_ai_turn(game, current_player)

        # Move to next player
        game.current_player_idx = (game.current_player_idx + 1) % len(game.players)

        # Check if all players have been eliminated
        if all(player.eliminated for player in game.players):
            print("\nAll players have been eliminated. Game over!")
            game.end_game()
            break

    # Check if we hit the turn limit
    if current_turn >= max_turns and not game.game_over:
        print(f"\nReached maximum number of turns ({max_turns}). Forcing game end.")
        game.end_game()

    # Game is over, show the result
    if game.winner:
        print(f"\nGame over! {game.winner.character_name} wins!")
    else:
        print("\nGame over! No one was able to solve the mystery.")

    # Print game statistics
    print(f"\nGame completed in {current_turn} turns")
    eliminated_count = sum(1 for player in game.players if player.eliminated)
    print(f"Eliminated players: {eliminated_count}/{len(game.players)}")

    # Print player status
    print("\nPlayer statuses:")
    for player in game.players:
        status = "Winner" if game.winner == player else "Eliminated" if player.eliminated else "Active"
        print(f"- {player.character_name}: {status}")


if __name__ == "__main__":
    main()