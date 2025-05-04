# Game/TurnManagement.py
"""
Module for handling player turns in the Clue game.
"""
import random
from Game.GameLogic import process_suggestion, process_accusation


def process_turn(game, player):
    """Process a turn for a human player."""
    print(f"\n===== {player.character_name}'s Turn =====")

    # Get the player's starting position and room
    starting_position = player.character.position
    starting_room = get_room_from_position(game.mansion_board, starting_position)

    # Roll the die and get available moves
    die_roll = random.randint(1, 6)
    print(f"{player.character_name} rolled a {die_roll}")

    available_moves = player.get_available_moves(
        game.mansion_board, game.character_board, die_roll)

    # Handle player movement
    new_position = handle_human_movement(game, player, available_moves)

    # Determine the new room (if any)
    new_room = get_room_from_position(game.mansion_board, new_position)

    # Handle room-related actions (suggestion)
    handle_room_actions(game, player, starting_room, new_room)

    # Handle accusation option
    handle_accusation_option(game, player)



def process_ai_turn(game, ai_player):
    """Process a turn for an AI player."""
    print(f"\n===== {ai_player.character_name}'s Turn (AI) =====")

    # Get the AI's starting position and room
    starting_position = ai_player.character.position
    starting_room = get_room_from_position(game.mansion_board, starting_position)

    # Roll the die and get available moves
    die_roll = random.randint(1, 12)
    print(f"{ai_player.character_name} rolled a {die_roll}")

    available_moves = ai_player.get_available_moves(
        game.mansion_board, game.character_board, die_roll)

    # AI decides and makes move
    new_position = ai_player.make_move(game, available_moves, die_roll)
    if new_position:
        ai_player.move(new_position)
        print(f"{ai_player.character_name} moved to {new_position}")
    else:
        print(f"{ai_player.character_name} stays in place")

    # Determine the new room (if any)
    new_room = get_room_from_position(game.mansion_board, new_position)

    # Handle room-related actions (suggestion)
    handle_room_actions(game, ai_player, starting_room, new_room)

    # Handle AI accusation decision
    ai_player.handle_accusation(game)

    # Print knowledge
    ai_player.print_knowledge()
    print()




def get_room_from_position(mansion_board, position):
    """Extract room name from a position in any format."""
    if position is None:
        return None

    if isinstance(position, str):
        return position
    elif isinstance(position, tuple) and len(position) == 3:
        return position[0]
    elif isinstance(position, tuple):
        # (row, col) format
        row, col = position
        return mansion_board.get_room_name_at_position(row, col)
    return None


def handle_human_movement(game, player, available_moves):
    """Handle movement for a human player."""
    if not available_moves:
        print("No valid moves available.")
        return player.character.position

    print("\nAvailable moves:")
    for i, move in enumerate(available_moves, 1):
        print(f"{i}. {move}")

    while True:
        try:
            choice = int(input("Enter the number of your choice: "))
            if 1 <= choice <= len(available_moves):
                new_position = available_moves[choice - 1]
                player.move(new_position)
                print(f"{player.character_name} moved to {new_position}")
                return new_position
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Please enter a number.")


def handle_room_actions(game, player, starting_room, new_room):
    """Handle actions related to being in a room (suggestions) for any player type."""
    if new_room and new_room != "Clue":
        is_ai = hasattr(player, 'is_ai') and player.is_ai

        if starting_room != new_room:
            # Player entered a new room - must make a suggestion
            print(f"{player.character_name} entered the {new_room} and must make a suggestion.")

            # Get suggestion based on player type
            if is_ai:
                suggestion = player.handle_suggestion(game, new_room)
                room, suspect, weapon = suggestion
            else:
                suggestion = handle_human_suggestion(game, player, new_room, required=True)
                suspect, weapon, room = suggestion

            # Display the suggestion clearly for all players
            print(
                f"\n🔍 SUGGESTION: {player.character_name} suggests {suspect} committed the murder in the {room} with the {weapon}")

            # Process the suggestion
            process_suggestion(game, player, suspect, weapon, room)

        elif starting_room == new_room:
            # Player stayed in the same room - suggestion is optional
            should_suggest = False

            if is_ai:
                # For AI players, use their decision logic if available
                should_suggest = hasattr(player, 'should_make_suggestion') and player.should_make_suggestion(game,
                                                                                                             new_room)
            else:
                # For human players, ask if they want to make a suggestion
                print(f"You are in the {new_room}. You may make a suggestion.")
                choice = input("Would you like to make a suggestion? (y/n): ")
                should_suggest = choice.lower().startswith('y')

            if should_suggest:
                if is_ai:
                    suggestion = player.handle_suggestion(game, new_room)
                    room, suspect, weapon = suggestion
                else:
                    suggestion = handle_human_suggestion(game, player, new_room, required=False)
                    suspect, weapon, room = suggestion

                # Display the suggestion clearly for all players
                print(
                    f"\n🔍 SUGGESTION: {player.character_name} suggests {suspect} committed the murder in the {room} with the {weapon}")

                # Process the suggestion
                process_suggestion(game, player, suspect, weapon, room)


def handle_human_suggestion(game, player, room_name, required=False):
    """Handle a human player making a suggestion."""
    print(f"\n{player.character_name} is making a suggestion in the {room_name}.")

    # Select a character
    print("\nSelect a character:")
    for i, character in enumerate(game.character_names, 1):
        print(f"{i}. {character}")

    while True:
        try:
            choice = int(input("Enter character number: "))
            if 1 <= choice <= len(game.character_names):
                character = game.character_names[choice - 1]
                break
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Please enter a number.")

    # Select a weapon
    print("\nSelect a weapon:")
    for i, weapon in enumerate(game.weapon_names, 1):
        print(f"{i}. {weapon}")

    while True:
        try:
            choice = int(input("Enter weapon number: "))
            if 1 <= choice <= len(game.weapon_names):
                weapon = game.weapon_names[choice - 1]
                break
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Please enter a number.")

    return (character, weapon, room_name)


def handle_accusation_option(game, player):
    """Handle a human player's option to make an accusation."""
    print("\nWould you like to make an accusation? (Only possible in the Clue room)")

    # Check if player is in the Clue room
    current_position = player.character.position
    in_clue_room = False

    if isinstance(current_position, str) and current_position == "Clue":
        in_clue_room = True
    elif isinstance(current_position, tuple) and len(current_position) == 3 and current_position[0] == "Clue":
        in_clue_room = True

    if not in_clue_room:
        print("You must be in the Clue room to make an accusation.")
        return

    choice = input("Make an accusation? (y/n): ")
    if choice.lower().startswith('y'):
        handle_human_accusation(game, player)


def handle_human_accusation(game, player):
    """Handle a human player making an accusation."""
    print("\nMaking an accusation:")

    # Select a character
    print("\nSelect the murderer:")
    for i, character in enumerate(game.character_names, 1):
        print(f"{i}. {character}")

    while True:
        try:
            choice = int(input("Enter character number: "))
            if 1 <= choice <= len(game.character_names):
                character = game.character_names[choice - 1]
                break
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Please enter a number.")

    # Select a weapon
    print("\nSelect the murder weapon:")
    for i, weapon in enumerate(game.weapon_names, 1):
        print(f"{i}. {weapon}")

    while True:
        try:
            choice = int(input("Enter weapon number: "))
            if 1 <= choice <= len(game.weapon_names):
                weapon = game.weapon_names[choice - 1]
                break
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Please enter a number.")

    # Select a room
    print("\nSelect the crime scene:")
    for i, room in enumerate(game.room_names, 1):
        print(f"{i}. {room}")

    while True:
        try:
            choice = int(input("Enter room number: "))
            if 1 <= choice <= len(game.room_names):
                room = game.room_names[choice - 1]
                break
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Please enter a number.")

    # Process the accusation
    is_correct = process_accusation(game, player, character, weapon, room)

    if is_correct:
        print(f"\nCongratulations! {player.character_name} made the correct accusation and wins the game!")
    else:
        print(f"\n{player.character_name} made an incorrect accusation and is now out of the game.")
        print("(You can still respond to suggestions, but cannot make suggestions or accusations)")
        player.made_wrong_accusation = True