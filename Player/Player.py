from Objects.Board import MansionBoard
from Data.Constants import CHARACTERS, WEAPONS, ROOMS
from Actions.Movement import get_available_moves as movement_get_available_moves
import random


class Player:
    """
    Base Player class for the Clue game.

    This class represents a player in the game, tracks their knowledge about
    cards, manages their character's position, and provides methods for
    game actions like moving, suggesting, and accusing.
    """

    def __init__(self, player_id, character_name):
        """
        Initialize a new Player.

        Args:
            player_id (int): Unique identifier for the player
            character_name (str): The character this player will control
        """
        self.player_id = player_id
        self.character_name = character_name
        self.character = None  # Will be set by the game when it starts
        self.hand = []  # Cards in the player's hand

        # Knowledge tracking
        self.possible_suspects = set(CHARACTERS)
        self.possible_weapons = set(WEAPONS)
        self.possible_rooms = set(ROOMS)

        # Definitely not in the solution (seen cards)
        self.confirmed_not_suspects = set()
        self.confirmed_not_weapons = set()
        self.confirmed_not_rooms = set()

        # For more advanced play: track what other players have seen
        self.player_knowledge = {}  # player_id -> {cards they've revealed to this player}

        # Store suggestions history
        self.suggestion_history = []

    def set_character(self, character):
        """Set the character object for this player."""
        self.character = character

    def add_card(self, card):
        """Add a card to the player's hand and update knowledge."""
        self.hand.append(card)
        self._update_knowledge_from_card(card)

    def _update_knowledge_from_card(self, card):
        """Update knowledge based on seeing a card."""
        card_type, card_name = card

        if card_type == "suspect":
            self.confirmed_not_suspects.add(card_name)
            self.possible_suspects.discard(card_name)
        elif card_type == "weapon":
            self.confirmed_not_weapons.add(card_name)
            self.possible_weapons.discard(card_name)
        elif card_type == "room":
            self.confirmed_not_rooms.add(card_name)
            self.possible_rooms.discard(card_name)

    def get_available_moves(self, board, character_board, die_roll):
        """
        Get all available moves for this player based on die roll.

        Args:
            board (MansionBoard): The game board
            character_board (CharacterBoard): Board tracking character positions
            die_roll (int): Result of die roll

        Returns:
            list: List of valid positions (row, col) the player can move to
        """
        if not self.character:
            return []

        # Use the character's position or room
        character_position = self.character.position

        # Use the Movement module's implementation
        return movement_get_available_moves(character_position, board, character_board, die_roll)

    def move(self, new_position):
        """Move the player's character to a new position."""
        if self.character:
            self.character.move_to(new_position)

    def make_suggestion(self, room, suspect, weapon):
        """
        Make a suggestion about the crime.

        Args:
            room (str): The room where the suggestion is being made
            suspect (str): The suspected character
            weapon (str): The suspected weapon

        Returns:
            tuple: (room, suspect, weapon)
        """
        # Record this suggestion in history
        self.suggestion_history.append({
            "room": room,
            "suspect": suspect,
            "weapon": weapon,
            "disproven_by": None,  # Will be filled in later
            "disproven_with": None  # Will be filled in if revealed to this player
        })

        return (room, suspect, weapon)

    def make_accusation(self, room, suspect, weapon):
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

    def update_knowledge_from_suggestion(self, suggesting_player, suggestion, responding_player, revealed_card=None):
        """
        Update knowledge based on a suggestion and its response.

        Args:
            suggesting_player (int): Player ID who made the suggestion
            suggestion (tuple): (room, suspect, weapon)
            responding_player (int): Player ID who responded (or None)
            revealed_card (tuple, optional): Card that was revealed to suggesting_player
        """
        room, suspect, weapon = suggestion

        # Update suggestion history if this was our suggestion
        if suggesting_player == self.player_id and self.suggestion_history:
            self.suggestion_history[-1]["disproven_by"] = responding_player
            self.suggestion_history[-1]["disproven_with"] = revealed_card

        # If player couldn't disprove, they don't have any of these cards
        if responding_player is not None and responding_player != self.player_id and revealed_card is None:
            if responding_player not in self.player_knowledge:
                self.player_knowledge[responding_player] = {"not_cards": set()}

            self.player_knowledge[responding_player]["not_cards"].add(("suspect", suspect))
            self.player_knowledge[responding_player]["not_cards"].add(("weapon", weapon))
            self.player_knowledge[responding_player]["not_cards"].add(("room", room))

        # If we were shown a card, update knowledge
        if suggesting_player == self.player_id and revealed_card:
            self._update_knowledge_from_card(revealed_card)

    def respond_to_suggestion(self, suggestion):
        """
        Respond to another player's suggestion if possible.

        Args:
            suggestion (tuple): (room, suspect, weapon)

        Returns:
            tuple or None: The card being shown, or None if can't disprove
        """
        room, suspect, weapon = suggestion

        # Check if player has any of the suggested cards
        matching_cards = []
        for card in self.hand:
            card_type, card_name = card
            if (card_type == "room" and card_name == room) or \
                    (card_type == "suspect" and card_name == suspect) or \
                    (card_type == "weapon" and card_name == weapon):
                matching_cards.append(card)

        if not matching_cards:
            return None

        # For base player, just return first matching card
        # More sophisticated players might choose strategically
        return matching_cards[0]

    def get_solution_candidates(self):
        """Get the current most likely solution based on knowledge."""
        return {
            "suspects": self.possible_suspects,
            "weapons": self.possible_weapons,
            "rooms": self.possible_rooms
        }