
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
    # Print the suggestion being made
    print(
        f"\n🔍 SUGGESTION: {suggesting_player.character_name} suggests {suspect} committed the murder in the {room} with the {weapon}")

    # Move the suggested character and weapon to the room
    move_suggested_objects(game, suspect, weapon, room)

    # Find the first player that can disprove the suggestion
    responding_player = None
    revealed_card = None

    # Start with the player to the left of the suggesting player
    start_idx = (suggesting_player.player_id + 1) % len(game.players)
    current_idx = start_idx

    print("\nChecking if any player can disprove the suggestion...")

    while True:
        current_player = game.players[current_idx]

        # Skip the suggesting player
        if current_player.player_id == suggesting_player.player_id:
            current_idx = (current_idx + 1) % len(game.players)
            # If we've checked all players and returned to the starter, break
            if current_idx == start_idx:
                break
            continue

        # Skip eliminated players' turns but not their responses
        if not current_player.eliminated or not current_player.made_wrong_accusation:
            print(f"- Asking {current_player.character_name} to respond...")

            # Get response from the current player
            card = current_player.respond_to_suggestion((suspect, weapon, room))

            if card:
                card_type, card_name = card
                responding_player = current_player
                revealed_card = card

                print(f"- {current_player.character_name} shows a card to {suggesting_player.character_name}.")

                # Only the suggesting player sees what card was shown
                if not hasattr(suggesting_player, 'is_ai') or not suggesting_player.is_ai:
                    print(f"\n{current_player.character_name} shows you: {card_name} ({card_type})")

                # Update suggesting player's knowledge with this card
                suggesting_player.update_knowledge_from_suggestion(
                    suggesting_player=suggesting_player.player_id,
                    suggestion=(room, suspect, weapon),
                    responding_player=responding_player.player_id,
                    revealed_card=card
                )

                # Update responding player's knowledge about this interaction
                if current_player.knowledge is not None:
                    current_player.update_knowledge_from_suggestion(
                        suggesting_player=suggesting_player.player_id,
                        suggestion=(room, suspect, weapon),
                        responding_player=current_player.player_id,
                        revealed_card=None  # They know their own card
                    )

                # Update all other players' knowledge
                for observer in game.players:
                    if observer.player_id != suggesting_player.player_id and observer.player_id != current_player.player_id:
                        if observer.knowledge is not None:
                            observer.update_knowledge_from_suggestion(
                                suggesting_player=suggesting_player.player_id,
                                suggestion=(room, suspect, weapon),
                                responding_player=current_player.player_id,
                                revealed_card=None  # Other players don't see the card
                            )

                # Once a card is shown, we're done checking
                break
            else:
                print(f"- {current_player.character_name} cannot disprove the suggestion.")

        # Move to the next player
        current_idx = (current_idx + 1) % len(game.players)

        # If we've checked all players and returned to the starter, break
        if current_idx == start_idx:
            break

    # If no one could disprove, notify and update knowledge
    if not responding_player:
        print("\n❗ No player could disprove the suggestion! These cards might be in the solution envelope.")

        # Update all players' knowledge
        for observer in game.players:
            if observer.knowledge is not None:
                observer.update_knowledge_from_suggestion(
                    suggesting_player=suggesting_player.player_id,
                    suggestion=(room, suspect, weapon),
                    responding_player=None,  # No one responded
                    revealed_card=None  # No card shown
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

    # Update all players' knowledge about this accusation
    for player in game.players:
        if player.knowledge is not None:
            player.update_knowledge_from_accusation(
                accusing_player=accusing_player.player_id,
                accusation=(room, suspect, weapon),
                is_correct=is_correct
            )

    if is_correct:
        # End the game with this player as the winner
        game.end_game(winner=accusing_player)
    else:
        # Player made an incorrect accusation - they're out of the game
        # but should continue to respond to suggestions
        accusing_player.made_wrong_accusation = True
        accusing_player.eliminated = True
        print(f"{accusing_player.character_name} made a wrong accusation and is eliminated!")

        # Check if all players have been eliminated
        active_players = [p for p in game.players if not p.eliminated]
        if not active_players:
            print("All players have been eliminated. Game over!")
            game.end_game()

    return is_correct