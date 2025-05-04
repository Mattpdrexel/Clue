# Game/GameLogic.py
"""
Module containing game logic for the Clue game.
"""
from Actions.Suggestions import check_accusation


def process_suggestion(game, suggesting_player, suspect, weapon, room):
    """
    Process a suggestion made by a player.

    Args:
        game: Game instance
        suggesting_player: Player making the suggestion
        suspect: Suspected character
        weapon: Suspected weapon
        room: Room where the suggestion is being made

    Returns:
        tuple: (responding_player, revealed_card)
    """
    # Move the suggested character and weapon to the room
    move_suggested_objects(game, suspect, weapon, room)

    # Find the first player that can disprove the suggestion
    responding_player = None
    revealed_card = None

    # Start with the player to the left of the suggesting player
    current_idx = (suggesting_player.player_id) % len(game.players)

    for _ in range(len(game.players) - 1):  # Check all players except the suggesting player
        current_idx = (current_idx + 1) % len(game.players)
        current_player = game.players[current_idx]

        if current_player.player_id == suggesting_player.player_id:
            continue  # Skip the suggesting player

        # Try to disprove
        card = current_player.respond_to_suggestion((suspect, weapon, room))

        if card:
            responding_player = current_player
            revealed_card = card

            # Update suggesting player's knowledge with this card
            suggesting_player.update_knowledge_from_suggestion(
                suggesting_player=suggesting_player.player_id,
                suggestion=(suspect, weapon, room),
                responding_player=current_player.player_id,
                revealed_card=card
            )

            # Other players update their knowledge about this interaction
            for observer in game.players:
                if observer.player_id != suggesting_player.player_id and observer.player_id != current_player.player_id:
                    observer.update_knowledge_from_suggestion(
                        suggesting_player=suggesting_player.player_id,
                        suggestion=(suspect, weapon, room),
                        responding_player=current_player.player_id,
                        revealed_card=None  # Observers don't see the card
                    )

            # Once one player disproves, we're done
            break

    # If no one could disprove, update all players' knowledge
    if not responding_player:
        for observer in game.players:
            if observer.player_id != suggesting_player.player_id:
                observer.update_knowledge_from_suggestion(
                    suggesting_player=suggesting_player.player_id,
                    suggestion=(suspect, weapon, room),
                    responding_player=None,
                    revealed_card=None
                )

    return responding_player, revealed_card


def move_suggested_objects(game, suspect, weapon, room):
    """Move the suggested character and weapon to the room."""
    # Move the suspected character if they exist
    if suspect in game.characters:
        suspect_char = game.characters[suspect]
        suspect_char.move_to(room)
        print(f"{suspect} was moved to the {room}")

    # Move the suspected weapon if it exists
    if weapon in game.weapons:
        weapon_obj = game.weapons[weapon]
        weapon_obj.move_to(room)
        print(f"The {weapon} was moved to the {room}")


def process_accusation(game, accusing_player, suspect, weapon, room):
    """
    Process an accusation made by a player.

    Args:
        game: The game instance
        accusing_player: Player making the accusation
        suspect (str): The suspected character
        weapon (str): The suspected weapon
        room (str): The room where the crime took place

    Returns:
        bool: True if the accusation is correct, False otherwise
    """
    # Check if the accusation is correct
    solution = game.solution
    is_correct = solution[0] == suspect and solution[1] == weapon and solution[2] == room

    if is_correct:
        # End the game with this player as the winner
        game.end_game(winner=accusing_player)
    else:
        # Player made an incorrect accusation - they're out of the game
        # but should continue to respond to suggestions
        accusing_player.made_wrong_accusation = True

    return is_correct