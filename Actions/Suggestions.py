# Actions/Suggestions.py
"""
Module containing functions for handling suggestions and accusations in the Clue game.
"""


def make_suggestion(player, room, suspect, weapon):
    """
    Make a suggestion about the crime.

    Args:
        player: The player making the suggestion
        room (str): The room where the suggestion is being made
        suspect (str): The suspected character
        weapon (str): The suspected weapon

    Returns:
        tuple: (room, suspect, weapon)
    """
    # Record this suggestion in player's history
    player.suggestion_history.append({
        "room": room,
        "suspect": suspect,
        "weapon": weapon,
        "disproven_by": None,  # Will be filled in later
        "disproven_with": None  # Will be filled in if revealed to this player
    })

    return (room, suspect, weapon)


def make_accusation(room, suspect, weapon):
    """
    Make a final accusation about the crime.

    Args:
        room (str): The room where the crime took place
        suspect (str): The character who committed the crime
        weapon (str): The weapon used

    Returns:
        tuple: (room, suspect, weapon)
    """
    return (room, suspect, weapon)


def respond_to_suggestion(player, suggestion):
    """
    Respond to another player's suggestion if possible.

    Args:
        player: The player responding to the suggestion
        suggestion (tuple): (room, suspect, weapon)

    Returns:
        tuple or None: The card being shown, or None if can't disprove
    """
    room, suspect, weapon = suggestion

    # Check if player has any of the suggested cards
    matching_cards = []
    for card in player.hand:
        card_type, card_name = card
        if (card_type == "room" and card_name == room) or \
                (card_type == "suspect" and card_name == suspect) or \
                (card_type == "weapon" and card_name == weapon):
            matching_cards.append(card)

    if not matching_cards:
        return None

    # For base implementation, just return first matching card
    # More sophisticated players might choose strategically
    return matching_cards[0]


def update_knowledge_from_suggestion(player, suggesting_player, suggestion, responding_player, revealed_card=None):
    """
    Update knowledge based on a suggestion and its response.

    Args:
        player: The player updating their knowledge
        suggesting_player (int): Player ID who made the suggestion
        suggestion (tuple): (room, suspect, weapon)
        responding_player (int): Player ID who responded (or None)
        revealed_card (tuple, optional): Card that was revealed to suggesting_player
    """
    room, suspect, weapon = suggestion

    # Update suggestion history if this was our suggestion
    if suggesting_player == player.player_id and player.suggestion_history:
        player.suggestion_history[-1]["disproven_by"] = responding_player
        player.suggestion_history[-1]["disproven_with"] = revealed_card

    # If player couldn't disprove, they don't have any of these cards
    if responding_player is not None and responding_player != player.player_id and revealed_card is None:
        if responding_player not in player.player_knowledge:
            player.player_knowledge[responding_player] = {"not_cards": set()}

        player.player_knowledge[responding_player]["not_cards"].add(("suspect", suspect))
        player.player_knowledge[responding_player]["not_cards"].add(("weapon", weapon))
        player.player_knowledge[responding_player]["not_cards"].add(("room", room))

    # If we were shown a card, update knowledge
    if suggesting_player == player.player_id and revealed_card:
        player._update_knowledge_from_card(revealed_card)


def check_accusation(accusation, solution):
    """
    Check if an accusation is correct.

    Args:
        accusation (tuple): The accusation (room, suspect, weapon)
        solution (tuple): The correct solution (room, suspect, weapon)

    Returns:
        bool: True if the accusation is correct, False otherwise
    """
    return accusation == solution