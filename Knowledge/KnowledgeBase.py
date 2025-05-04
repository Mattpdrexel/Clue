# Player/Knowledge/KnowledgeBase.py
from collections import defaultdict
from copy import deepcopy
from Data.Constants import CHARACTERS, WEAPONS, ROOMS


class KnowledgeBase:
    """
    A knowledge base for the Clue game that tracks possibilities for each card.
    This implements a Boolean matrix (score sheet) with rows = cards and columns = holders.
    """

    def __init__(self, game, player_id):
        """
        Initialize the knowledge base with all possibilities.

        Args:
            game: The Game instance
            player_id: The ID of the player owning this knowledge base
        """
        self.player_id = player_id
        self.game = game

        # Track the number of players
        self.num_players = len(game.players)

        # Get player IDs for all players
        self.player_ids = [p.player_id for p in game.players]

        # Track envelope as special "player"
        self.ENVELOPE = "ENVELOPE"

        # Create holders set (all players + envelope)
        self.holders = set(self.player_ids + [self.ENVELOPE])

        # Initialize the possibility matrix as defaultdict of sets
        # Each card maps to a set of possible holders
        self.possibility_matrix = defaultdict(lambda: set(self.holders))

        # Categorized lists of cards
        self.suspects = set(CHARACTERS)
        self.weapons = set(WEAPONS)
        self.rooms = set(ROOMS)

        # Solutions candidates - cards that might be in the envelope
        self.envelope_suspects = set(CHARACTERS)
        self.envelope_weapons = set(WEAPONS)
        self.envelope_rooms = set(ROOMS)

        # Known cards (cards in player's hand)
        self.known_cards = set()

        # Flag to track if solution is known
        self.solution_known = False
        self.solution = (None, None, None)  # (suspect, weapon, room)

    def initialize_with_hand(self, hand):
        """
        Initialize knowledge base with cards in player's hand.

        Args:
            hand: List of (card_type, card_name) tuples
        """
        for card_type, card_name in hand:
            # This card is definitely with the player
            self.set_holder(card_name, self.player_id)
            self.known_cards.add(card_name)

    def set_holder(self, card, holder):
        """
        Set a card as definitely held by a specific holder.
        This eliminates all other possibilities for this card.

        Args:
            card: The card name
            holder: The holder ID or "ENVELOPE"
        """
        # Set this as the only possibility for this card
        self.possibility_matrix[card] = {holder}

        # Update envelope candidates if needed
        if holder == self.ENVELOPE:
            # If card is set as definitely in the envelope, update envelope candidates
            if card in self.suspects:
                # Clear all other suspects from envelope candidates
                self.envelope_suspects = {card}
            elif card in self.weapons:
                # Clear all other weapons from envelope candidates
                self.envelope_weapons = {card}
            elif card in self.rooms:
                # Clear all other rooms from envelope candidates
                self.envelope_rooms = {card}
        else:
            # Card is with a player, so remove from envelope candidates
            self._remove_from_envelope_candidates(card)

        # Check for ripple effects
        self._propagate()

    def eliminate(self, card, holder):
        """
        Mark that a card is definitely NOT held by a specific holder.

        Args:
            card: The card name
            holder: The holder ID or "ENVELOPE"
        """
        # Remove this holder from the possibilities for this card
        if holder in self.possibility_matrix[card]:
            self.possibility_matrix[card].remove(holder)

            # If holder was ENVELOPE, update envelope candidates
            if holder == self.ENVELOPE:
                self._remove_from_envelope_candidates(card)

            # If only one possibility remains, we know the definite holder
            if len(self.possibility_matrix[card]) == 1:
                definite_holder = next(iter(self.possibility_matrix[card]))
                # Don't call set_holder here to avoid recursion, just update envelope candidates
                if definite_holder != self.ENVELOPE:
                    self._remove_from_envelope_candidates(card)

            # Check for ripple effects
            self._propagate()

    def _remove_from_envelope_candidates(self, card):
        """Remove a card from envelope candidates if applicable."""
        if card in self.envelope_suspects:
            self.envelope_suspects.remove(card)
            # Check if we've narrowed down to one suspect
            if len(self.envelope_suspects) == 1 and len(self.envelope_weapons) == 1 and len(self.envelope_rooms) == 1:
                self._update_solution()
        elif card in self.envelope_weapons:
            self.envelope_weapons.remove(card)
            # Check if we've narrowed down to one weapon
            if len(self.envelope_suspects) == 1 and len(self.envelope_weapons) == 1 and len(self.envelope_rooms) == 1:
                self._update_solution()
        elif card in self.envelope_rooms:
            self.envelope_rooms.remove(card)
            # Check if we've narrowed down to one room
            if len(self.envelope_suspects) == 1 and len(self.envelope_weapons) == 1 and len(self.envelope_rooms) == 1:
                self._update_solution()

    def _update_solution(self):
        """Update the solution if we have exactly one card of each type."""
        suspect = next(iter(self.envelope_suspects))
        weapon = next(iter(self.envelope_weapons))
        room = next(iter(self.envelope_rooms))

        self.solution = (suspect, weapon, room)
        self.solution_known = True

    def _propagate(self):
        """Apply logical deduction rules to propagate constraints."""
        # Check if we have only one candidate for each envelope category
        if len(self.envelope_suspects) == 1 and len(self.envelope_weapons) == 1 and len(self.envelope_rooms) == 1:
            self._update_solution()

    def update_from_suggestion(self, suggesting_player_id, suggestion, responding_player_id, shown_card=None):
        """
        Update knowledge based on a suggestion and the response.

        Args:
            suggesting_player_id: ID of player who made the suggestion
            suggestion: Tuple of (suspect, weapon, room)
            responding_player_id: ID of player who responded, or None if nobody could
            shown_card: Card that was shown (only known to suggester), or None
        """
        suspect, weapon, room = suggestion

        # Case A: We saw a specific card (as suggester or responder)
        if shown_card is not None:
            self.set_holder(shown_card, responding_player_id)
            return

        # Case B: Someone responded but we don't know which card
        if responding_player_id is not None:
            # We know responding player has at least one of the three cards

            # For all players who couldn't respond (between suggester and responder)
            # we know they don't have any of these cards
            start_idx = self.player_ids.index(suggesting_player_id)
            end_idx = self.player_ids.index(responding_player_id)

            # Get players in between, considering the circular order
            players_between = []
            current_idx = (start_idx + 1) % self.num_players
            while current_idx != end_idx:
                players_between.append(self.player_ids[current_idx])
                current_idx = (current_idx + 1) % self.num_players

            # These players don't have any of the cards
            for player_id in players_between:
                self.eliminate(suspect, player_id)
                self.eliminate(weapon, player_id)
                self.eliminate(room, player_id)

        # Case C: Nobody could refute
        else:
            # All three cards must be in the envelope - clear other candidates
            self.set_holder(suspect, self.ENVELOPE)
            self.set_holder(weapon, self.ENVELOPE)
            self.set_holder(room, self.ENVELOPE)

    def possible_holders(self, card):
        """Return the set of possible holders for a card."""
        return deepcopy(self.possibility_matrix[card])

    def cards_possibly_with(self, holder):
        """Return the set of cards that could be with a specific holder."""
        result = set()
        for card in self.suspects | self.weapons | self.rooms:
            if holder in self.possibility_matrix[card]:
                result.add(card)
        return result

    def envelope_candidates(self):
        """Return sets of cards that could be in the envelope."""
        return {
            "suspects": deepcopy(self.envelope_suspects),
            "weapons": deepcopy(self.envelope_weapons),
            "rooms": deepcopy(self.envelope_rooms)
        }

    def is_solution_known(self):
        """Check if we have logically deduced the solution."""
        return self.solution_known

    def get_solution(self):
        """Return the logically deduced solution if known."""
        if self.solution_known:
            return self.solution
        return None