# Game/GameLogic.py
"""
Module containing game logic for the Clue game.
"""
from Actions.Suggestions import check_accusation


def process_suggestion(game, suggesting_player, room, suspect, weapon):
    """
    Process a suggestion made by a player.

    Args:
        game: The game instance
        suggesting_player: Player making the suggestion
        room (str): The room where the suggestion is being made
        suspect (str): The suspected character
        weapon (str): The suspected weapon

    Returns:
        tuple: (responding_player, revealed_card)
    """
    suggestion = (room, suspect, weapon)

    # Make the suggestion
    suggesting_player.make_suggestion(room, suspect, weapon)

    # Check each player in turn order starting after the suggesting player
    players = game.players
    player_count = len(players)
    suggesting_idx = players.index(suggesting_player)

    # Loop through players in order, starting after suggesting player
    for i in range(1, player_count):
        player_idx = (suggesting_idx + i) % player_count
        responding_player = players[player_idx]

        # Check if this player can disprove the suggestion
        revealed_card = responding_player.respond_to_suggestion(suggestion)

        if revealed_card:
            # Update the suggesting player's knowledge
            suggesting_player.update_knowledge_from_suggestion(
                suggesting_player=suggesting_player.player_id,
                suggestion=suggestion,
                responding_player=responding_player.player_id,
                revealed_card=revealed_card
            )

            # Update all other players' knowledge that this player responded
            for player in players:
                if player != suggesting_player and player != responding_player:
                    player.update_knowledge_from_suggestion(
                        suggesting_player=suggesting_player.player_id,
                        suggestion=suggestion,
                        responding_player=responding_player.player_id,
                        revealed_card=None
                    )

            return responding_player, revealed_card

    # No player could disprove
    # Update all players' knowledge
    for player in players:
        if player != suggesting_player:
            player.update_knowledge_from_suggestion(
                suggesting_player=suggesting_player.player_id,
                suggestion=suggestion,
                responding_player=None,
                revealed_card=None
            )

    suggesting_player.update_knowledge_from_suggestion(
        suggesting_player=suggesting_player.player_id,
        suggestion=suggestion,
        responding_player=None,
        revealed_card=None
    )

    return None, None


def process_accusation(game, accusing_player, room, suspect, weapon):
    """
    Process an accusation made by a player.

    Args:
        game: The game instance
        accusing_player: Player making the accusation
        room (str): The room where the crime took place
        suspect (str): The suspected character
        weapon (str): The suspected weapon

    Returns:
        bool: True if the accusation is correct, False otherwise
    """
    accusation = accusing_player.make_accusation(room, suspect, weapon)

    # Check if the accusation is correct
    is_correct = check_accusation(accusation, game.solution)

    if is_correct:
        # End the game with this player as the winner
        game.end_game(winner=accusing_player)
    else:
        # Player made an incorrect accusation - they're out of the game
        # but should continue to respond to suggestions
        accusing_player.made_wrong_accusation = True

    return is_correct