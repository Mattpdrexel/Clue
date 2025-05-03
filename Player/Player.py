# Player/Player.py
from Objects.Board import MansionBoard
from Objects.Character import character_dict
from Data.Constants import CHARACTERS, WEAPONS, SUSPECT_ROOMS
from Actions.Movement import get_available_moves as movement_get_available_moves
import Actions.Suggestions as suggestion_actions
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
        self.character = character_dict[character_name]
        self.hand = []  # Cards in the player's hand

        # Knowledge tracking
        self.possible_suspects = set(CHARACTERS)
        self.possible_weapons = set(WEAPONS)
        self.possible_rooms = set(SUSPECT_ROOMS)

        # Definitely not in the solution (seen cards)
        self.confirmed_not_suspects = set()
        self.confirmed_not_weapons = set()
        self.confirmed_not_rooms = set()

        # For more advanced play: track what other players have seen
        self.player_knowledge = {}  # player_id -> {cards they've revealed to this player}

        # Store suggestions history
        self.suggestion_history = []

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
        return suggestion_actions.make_suggestion(self, room, suspect, weapon)

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
        return suggestion_actions.make_accusation(room, suspect, weapon)

    def update_knowledge_from_suggestion(self, suggesting_player, suggestion, responding_player, revealed_card=None):
        """
        Update knowledge based on a suggestion and its response.

        Args:
            suggesting_player (int): Player ID who made the suggestion
            suggestion (tuple): (room, suspect, weapon)
            responding_player (int): Player ID who responded (or None)
            revealed_card (tuple, optional): Card that was revealed to suggesting_player
        """
        suggestion_actions.update_knowledge_from_suggestion(
            self, suggesting_player, suggestion, responding_player, revealed_card
        )

    def respond_to_suggestion(self, suggestion):
        """
        Respond to another player's suggestion if possible.

        Args:
            suggestion (tuple): (room, suspect, weapon)

        Returns:
            tuple or None: The card being shown, or None if can't disprove
        """
        return suggestion_actions.respond_to_suggestion(self, suggestion)

    def get_solution_candidates(self):
        """Get the current most likely solution based on knowledge."""
        return {
            "suspects": self.possible_suspects,
            "weapons": self.possible_weapons,
            "rooms": self.possible_rooms
        }