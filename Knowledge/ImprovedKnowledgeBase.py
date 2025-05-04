# Knowledge/ImprovedKnowledgeBase.py
import numpy as np
from collections import defaultdict


class ImprovedKnowledgeBase:
    """
    An improved knowledge base for the Clue game that uses a Boolean matrix and
    disjunction constraints to track possibilities for each card.
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

        # Track all players and the envelope
        self.holders = [p.player_id for p in game.players]
        self.ENVELOPE = "ENVELOPE"
        self.holders.append(self.ENVELOPE)

        # Create index mappings
        self.holder_to_idx = {h: i for i, h in enumerate(self.holders)}

        # Maps from card name to index in matrix
        self.cards = []
        self.card_to_idx = {}

        # Track card categories
        self.categories = {
            "suspect": game.character_names,
            "weapon": game.weapon_names,
            "room": game.room_names
        }

        # Add all cards to our index
        idx = 0
        for category, card_list in self.categories.items():
            for card in card_list:
                self.cards.append(card)
                self.card_to_idx[card] = idx
                idx += 1

        # Initialize possibility matrix - all True (everything possible)
        self.num_cards = len(self.cards)
        self.num_holders = len(self.holders)
        self.poss = np.ones((self.num_cards, self.num_holders), dtype=np.bool_)

        # Disjunction constraints
        self.atleast_one = []  # List of (holder, set_of_cards)

        # Internal state tracking
        self.changed = False
        self.solution_known = False
        self._solution = None

    def initialize_with_hand(self, hand):
        """
        Initialize knowledge base with cards in player's hand.

        Args:
            hand: List of (card_type, card_name) tuples
        """
        for card_type, card_name in hand:
            self.set_holder(card_name, self.player_id)

    def set_holder(self, card, holder):
        """
        Set a card as definitely held by a specific holder.
        This eliminates all other possibilities for this card.

        Args:
            card: The card name
            holder: The holder ID or "ENVELOPE"
        """
        if card not in self.card_to_idx:
            return  # Invalid card

        card_idx = self.card_to_idx[card]
        holder_idx = self.holder_to_idx[holder]

        # Set all possibilities to False except for this holder
        self.poss[card_idx, :] = False
        self.poss[card_idx, holder_idx] = True

        self.changed = True
        self._propagate()

    def eliminate(self, card, holder):
        """
        Mark that a card is definitely NOT held by a specific holder.

        Args:
            card: The card name
            holder: The holder ID or "ENVELOPE"
        """
        if card not in self.card_to_idx or holder not in self.holder_to_idx:
            return  # Invalid card or holder

        card_idx = self.card_to_idx[card]
        holder_idx = self.holder_to_idx[holder]

        # If already eliminated, nothing to do
        if not self.poss[card_idx, holder_idx]:
            return

        # Mark this option as impossible
        self.poss[card_idx, holder_idx] = False
        self.changed = True
        self._propagate()

    def record_atleast_one(self, holder, card_set):
        """
        Record a disjunction constraint: holder must have at least one card from card_set.

        Args:
            holder: The holder ID
            card_set: Set of card names
        """
        # Convert card names to indices for faster processing
        card_indices = {self.card_to_idx[c] for c in card_set if c in self.card_to_idx}

        # Store constraint using indices
        if card_indices:
            self.atleast_one.append((holder, card_indices))
            self.changed = True
            self._propagate()

    def _propagate(self):
        """
        Apply logical deduction rules to propagate constraints.
        """
        while self.changed:
            self.changed = False

            # Rule 1: Single remaining possibility
            self._apply_single_possibility_rule()

            # Rule 2: Process disjunction constraints
            self._process_atleast_one_constraints()

            # Rule 3: Category exclusivity in envelope
            self._apply_envelope_exclusivity()

            # Check if solution is known
            self._check_solution()

    def _apply_single_possibility_rule(self):
        """
        If a card has only one possible holder, assign it.
        """
        for card_idx in range(self.num_cards):
            possibilities = np.where(self.poss[card_idx])[0]
            if len(possibilities) == 1 and not self._is_assigned(card_idx):
                holder_idx = possibilities[0]
                holder = self.holders[holder_idx]
                card = self.cards[card_idx]

                # Set this as the definite holder (already marked in matrix)
                # Just need to check for further implications
                self.changed = True

    def _process_atleast_one_constraints(self):
        """
        Process atleast_one constraints:
        - If all but one card is impossible, the last one must be true
        - If any card is already assigned to the holder, remove the constraint
        """
        remaining_constraints = []

        for holder, card_indices in self.atleast_one:
            holder_idx = self.holder_to_idx[holder]

            # Count cards still possible
            possible_cards = [c for c in card_indices if self.poss[c, holder_idx]]

            if len(possible_cards) == 0:
                # Contradiction - impossible situation
                pass  # In a real system, we might flag this as an error
            elif len(possible_cards) == 1:
                # Only one card is possible - must be this one
                card_idx = possible_cards[0]
                # Set this card to this holder
                self.poss[card_idx, :] = False
                self.poss[card_idx, holder_idx] = True
                self.changed = True
                # Don't keep this constraint
            else:
                # Check if any card is already definitely assigned to this holder
                satisfied = False
                for card_idx in card_indices:
                    # If this card is definitely assigned to this holder
                    if self._is_assigned_to(card_idx, holder_idx):
                        satisfied = True
                        break

                # If not satisfied, keep the constraint
                if not satisfied:
                    remaining_constraints.append((holder, card_indices))

        # Update the list of constraints
        self.atleast_one = remaining_constraints

    def _apply_envelope_exclusivity(self):
        """
        In each category, if all cards except one are proven to not be in the envelope,
        then the remaining card must be in the envelope.
        """
        envelope_idx = self.holder_to_idx[self.ENVELOPE]

        for category, card_list in self.categories.items():
            # Get indices for cards in this category
            card_indices = [self.card_to_idx[c] for c in card_list]

            # Count possible envelope cards
            possible_envelope_cards = [c for c in card_indices if self.poss[c, envelope_idx]]

            if len(possible_envelope_cards) == 1:
                card_idx = possible_envelope_cards[0]
                # If not already assigned, assign it to envelope
                if not self._is_assigned(card_idx):
                    self.poss[card_idx, :] = False
                    self.poss[card_idx, envelope_idx] = True
                    self.changed = True

    def _is_assigned(self, card_idx):
        """Check if a card has been definitively assigned to a holder."""
        return np.sum(self.poss[card_idx]) == 1

    def _is_assigned_to(self, card_idx, holder_idx):
        """Check if a card is definitively assigned to a specific holder."""
        return self._is_assigned(card_idx) and self.poss[card_idx, holder_idx]

    def _check_solution(self):
        """Check if the solution is fully determined."""
        envelope_idx = self.holder_to_idx[self.ENVELOPE]

        # Get suspects, weapons, and rooms in the envelope
        envelope_suspects = []
        envelope_weapons = []
        envelope_rooms = []

        for category, card_list in self.categories.items():
            for card in card_list:
                card_idx = self.card_to_idx[card]
                if self._is_assigned_to(card_idx, envelope_idx):
                    if category == "suspect":
                        envelope_suspects.append(card)
                    elif category == "weapon":
                        envelope_weapons.append(card)
                    elif category == "room":
                        envelope_rooms.append(card)

        # If exactly one of each category, we know the solution
        if len(envelope_suspects) == 1 and len(envelope_weapons) == 1 and len(envelope_rooms) == 1:
            self.solution_known = True
            self._solution = (envelope_suspects[0], envelope_weapons[0], envelope_rooms[0])

    def possible_holders(self, card):
        """
        Return the set of possible holders for a card.

        Args:
            card: The card name

        Returns:
            set: Possible holders for this card
        """
        if card not in self.card_to_idx:
            return set()

        card_idx = self.card_to_idx[card]
        return {self.holders[i] for i in range(self.num_holders) if self.poss[card_idx, i]}

    def card_owner(self, card):
        """
        Return the definite owner of a card, if known.

        Args:
            card: The card name

        Returns:
            holder or None: The holder if known, otherwise None
        """
        possible = self.possible_holders(card)
        if len(possible) == 1:
            return next(iter(possible))
        return None

    def envelope_candidates(self):
        """
        Return sets of cards that could be in the envelope.

        Returns:
            dict: Dictionary with keys 'suspects', 'weapons', 'rooms', each with a set of card names
        """
        envelope_idx = self.holder_to_idx[self.ENVELOPE]

        result = {
            "suspects": set(),
            "weapons": set(),
            "rooms": set()
        }

        for category, card_list in self.categories.items():
            for card in card_list:
                card_idx = self.card_to_idx[card]
                if self.poss[card_idx, envelope_idx]:
                    if category == "suspect":
                        result["suspects"].add(card)
                    elif category == "weapon":
                        result["weapons"].add(card)
                    elif category == "room":
                        result["rooms"].add(card)

        return result

    def solution_if_forced(self):
        """
        Return the solution if it's been deduced completely.

        Returns:
            tuple or None: (suspect, weapon, room) if known, otherwise None
        """
        if self.solution_known:
            return self._solution
        return None

    def is_solution_known(self):
        """Check if the solution has been deduced completely."""
        return self.solution_known

    def get_solution(self):
        """Return the deduced solution if known."""
        return self._solution if self.solution_known else None

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
        cards_in_suggestion = {suspect, weapon, room}

        # Case 1: We saw a specific card
        if shown_card is not None:
            # We know exactly which card was shown and who has it
            self.set_holder(shown_card, responding_player_id)
            return

        # Case 2: A player responded but we don't know which card
        if responding_player_id is not None:
            # Record that this player has at least one of the cards
            self.record_atleast_one(responding_player_id, cards_in_suggestion)

            # Process players who passed (they don't have any of the cards)
            # Find index of suggesting player and responding player
            player_ids = [p.player_id for p in self.game.players]
            suggester_idx = player_ids.index(suggesting_player_id)
            responder_idx = player_ids.index(responding_player_id)

            # Get players between suggester and responder
            current_idx = (suggester_idx + 1) % len(player_ids)
            while current_idx != responder_idx:
                # This player doesn't have any of the cards
                for card in cards_in_suggestion:
                    self.eliminate(card, player_ids[current_idx])
                current_idx = (current_idx + 1) % len(player_ids)

        # Case 3: Nobody could respond - all cards must be in envelope
        else:
            for card in cards_in_suggestion:
                self.set_holder(card, self.ENVELOPE)

    def expected_information_gain(self, card_set):
        """
        Calculate the expected information gain from a suggestion.

        Args:
            card_set: Set of cards in the suggestion

        Returns:
            float: A score representing expected information gain
        """
        # Simple heuristic: smaller total possible-holders = higher value
        total = sum(len(self.possible_holders(c)) - 1 for c in card_set)
        return total