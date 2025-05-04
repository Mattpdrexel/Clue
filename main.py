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


# main.py (modify the play_game_auto function)

def play_game_auto(game):
    """Modified game loop that doesn't wait for input between turns"""
    print("\nStarting the game of Clue with all AI players!")

    # Import necessary modules
    from Knowledge.ScoreSheet import ScoreSheet
    import os

    # Set a reasonable limit to prevent infinite games
    max_turns = 400
    max_rounds = 200
    current_turn = 0
    current_round = 0

    # Track which player started the current round
    first_player_idx = 0

    # Number of active (not eliminated) players
    active_players = len(game.players)

    # Initialize scoresheet
    player_names = [player.character_name for player in game.players]
    scoresheet = ScoreSheet(player_names)
    os.makedirs("Output", exist_ok=True)

    while not game.game_over and current_round < max_rounds:
        # Increment turn counter
        current_turn += 1

        # Check if we've completed a round (all players have had a turn)
        if game.current_player_idx == first_player_idx:
            current_round += 1
            print(f"\n====== Round {current_round} ======")

            # Update and save the scoresheet at the end of each round
            game.current_round = current_round
            # Update scoresheet from all players' knowledge
            for i, player in enumerate(game.players):
                if hasattr(player, 'knowledge') and player.knowledge:
                    scoresheet.update_from_player_knowledge(i, player.knowledge)

            # Save the scoresheet to a file
            scoresheet.save_to_file(f"Output/scoresheet_round_{current_round}.txt")

        # Print turn info
        print(f"\n--- Turn {current_turn} (Round {current_round}) ---")

        # Get current player
        current_player = game.players[game.current_player_idx]

        # Skip eliminated players
        if current_player.eliminated:
            print(f"\n{current_player.character_name}'s turn is skipped (eliminated).")
            game.current_player_idx = (game.current_player_idx + 1) % len(game.players)

            # If this was the last player in a round, update first_player_idx
            if game.current_player_idx == first_player_idx:
                # Find the next non-eliminated player to start the next round
                while game.players[first_player_idx].eliminated and active_players > 0:
                    first_player_idx = (first_player_idx + 1) % len(game.players)

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

    # Check if we hit the round limit
    if current_round >= max_rounds and not game.game_over:
        print(f"\nReached maximum number of rounds ({max_rounds}). Forcing game end.")
        game.end_game()

    # Game is over, show the result
    if game.winner:
        print(f"\nGame over! {game.winner.character_name} wins!")
    else:
        print("\nGame over! No one was able to solve the mystery.")

    # Print game statistics
    print(f"\nGame completed in {current_round} rounds ({current_turn} total turns)")
    eliminated_count = sum(1 for player in game.players if player.eliminated)
    print(f"Eliminated players: {eliminated_count}/{len(game.players)}")

    # Print player status
    print("\nPlayer statuses:")
    for player in game.players:
        status = "Winner" if game.winner == player else "Eliminated" if player.eliminated else "Active"
        print(f"- {player.character_name}: {status}")

    # Print final scoresheet
    print("\nFinal Game Scoresheet:")
    # Update scoresheet from all players' knowledge
    for i, player in enumerate(game.players):
        if hasattr(player, 'knowledge') and player.knowledge:
            scoresheet.update_from_player_knowledge(i, player.knowledge)

    print(scoresheet.render_text())
    scoresheet.save_to_file("Output/scoresheet_final.txt")

if __name__ == "__main__":
    main()