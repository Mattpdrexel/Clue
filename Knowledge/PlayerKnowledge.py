
# Knowledge/PlayerKnowledge.py
from Data.Constants import CHARACTERS, WEAPONS, SUSPECT_ROOMS


class PlayerKnowledge:
    """
    A comprehensive knowledge base that tracks all game events from a player's perspective.
    Each player owns their own instance of this class.
    """

    def __init__(self, player_id, game):
        """Initialize the knowledge base for a player"""
        self.player_id = player_id
        self.game = game

        # Define categories
        self.categories = {
            "suspects": CHARACTERS.copy(),
            "weapons": WEAPONS.copy(),
            "rooms": SUSPECT_ROOMS.copy()
        }

        # Raw knowledge events - storing the actual gameplay data
        self.events = []

        # Cards in player's hand
        self.my_cards = set()

        # Cards known to be held by specific players (player_id -> set of cards)
        self.player_cards = {p.player_id: set() for p in game.players}

        # Cards definitely not held by specific players
        self.player_not_cards = {p.player_id: set() for p in game.players}

        # Cards that might be in the solution envelope
        self.possible_solution = {
            "suspects": set(CHARACTERS.copy()),
            "weapons": set(WEAPONS.copy()),
            "rooms": set(SUSPECT_ROOMS.copy())
        }

        # Event types
        self.EVENT_CARD_SEEN = "card_seen"
        self.EVENT_SUGGESTION = "suggestion"
        self.EVENT_ACCUSATION = "accusation"
        self.EVENT_RESPONSE = "response"

    def add_card_to_hand(self, card_type, card_name):
        """Record a card that is in this player's hand"""
        # Store the card
        self.my_cards.add(card_name)
        self.player_cards[self.player_id].add(card_name)

        # Record this event
        self.events.append({
            "type": self.EVENT_CARD_SEEN,
            "card": card_name,
            "card_type": card_type,
            "holder": self.player_id
        })

        # Update possible solution - this card cannot be in the envelope
        self._remove_from_solution(card_type, card_name)

        # No other player can have this card
        for pid in self.player_not_cards:
            if pid != self.player_id:
                self.player_not_cards[pid].add(card_name)

    def record_suggestion(self, suggesting_player, suggestion, responding_player, revealed_card=None):
        """
        Record a suggestion and its result.

        Args:
            suggesting_player: Player ID who made the suggestion
            suggestion: Tuple of (room, suspect, weapon)
            responding_player: Player ID who responded, or None if nobody responded
            revealed_card: Card that was revealed (only if this player was involved)
        """
        room, suspect, weapon = suggestion

        # Record this event
        event = {
            "type": self.EVENT_SUGGESTION,
            "suggesting_player": suggesting_player,
            "suggestion": suggestion,
            "responding_player": responding_player
        }

        if revealed_card:
            event["revealed_card"] = revealed_card

        self.events.append(event)

        # Update knowledge based on the suggestion outcome

        # Case 1: No one could respond - possible solution cards
        if responding_player is None:
            # These cards might be in the solution
            self._mark_possible_solution(room)
            self._mark_possible_solution(suspect)
            self._mark_possible_solution(weapon)

            # No player has these cards
            for pid in self.player_not_cards:
                self.player_not_cards[pid].add(room)
                self.player_not_cards[pid].add(suspect)
                self.player_not_cards[pid].add(weapon)

        # Case 2: We made the suggestion and saw a card
        elif suggesting_player == self.player_id and revealed_card:
            card_type, card_name = revealed_card
            # Create player entry if doesn't exist
            if responding_player not in self.player_cards:
                self.player_cards[responding_player] = set()
            # We now know who has this card 
            self.player_cards[responding_player].add(card_name)
            # Update possible solution - this card cannot be in the envelope
            self._remove_from_solution(card_type, card_name)

            # Players who were skipped don't have any of the cards
            current_id = (suggesting_player + 1) % len(self.game.players)
            while current_id != responding_player:
                self.player_not_cards[current_id].add(room)
                self.player_not_cards[current_id].add(suspect)
                self.player_not_cards[current_id].add(weapon)
                current_id = (current_id + 1) % len(self.game.players)

        # Case 3: We were shown a card by another player
        elif responding_player == self.player_id and revealed_card:
            # We only need to update our own knowledge in this case
            # (This is already handled by add_card_to_hand)
            pass

        # Case 4: We saw someone respond but don't know what card
        elif responding_player is not None:
            # We know the responding player has at least one of the cards
            # Players who were skipped don't have any of the cards
            current_id = (suggesting_player + 1) % len(self.game.players)
            while current_id != responding_player:
                self.player_not_cards[current_id].add(room)
                self.player_not_cards[current_id].add(suspect)
                self.player_not_cards[current_id].add(weapon)
                current_id = (current_id + 1) % len(self.game.players)

    def record_accusation(self, accusing_player, accusation, is_correct):
        """
        Record an accusation and whether it was correct.

        Args:
            accusing_player: Player ID who made the accusation
            accusation: Tuple of (room, suspect, weapon)
            is_correct: Whether the accusation was correct
        """
        room, suspect, weapon = accusation

        # Record this event
        self.events.append({
            "type": self.EVENT_ACCUSATION,
            "accusing_player": accusing_player,
            "accusation": accusation,
            "is_correct": is_correct
        })

        # If correct, we know the solution
        if is_correct:
            # Clear possible solutions and add only these cards
            for category in self.possible_solution:
                self.possible_solution[category].clear()

            self.possible_solution["rooms"].add(room)
            self.possible_solution["suspects"].add(suspect)
            self.possible_solution["weapons"].add(weapon)
        # If incorrect, at least one card is not in the solution
        else:
            # We don't know which one, so we can't eliminate any specific card yet
            # More advanced deduction could happen later
            pass

    def _remove_from_solution(self, card_type, card_name):
        """Remove a card from possible solution candidates"""
        if card_type == "suspect":
            if card_name in self.possible_solution["suspects"]:
                self.possible_solution["suspects"].remove(card_name)
        elif card_type == "weapon":
            if card_name in self.possible_solution["weapons"]:
                self.possible_solution["weapons"].remove(card_name)
        elif card_type == "room":
            if card_name in self.possible_solution["rooms"]:
                self.possible_solution["rooms"].remove(card_name)

    def _mark_possible_solution(self, card_name):
        """Mark a card as a potential solution candidate"""
        # First determine which category this card belongs to
        for category, items in self.categories.items():
            if card_name in items:
                # Add to possible solution if not already eliminated
                if card_name in self.possible_solution[category]:
                    # This is already a possibility, no need to do anything
                    pass
                break

    def best_guess_solution(self):
        """Return the current best guess at the solution based on knowledge"""
        if self.is_solution_known():
            # We know the exact solution
            return {
                "suspect": next(iter(self.possible_solution["suspects"])),
                "weapon": next(iter(self.possible_solution["weapons"])),
                "room": next(iter(self.possible_solution["rooms"]))
            }
        else:
            # Return a best guess from remaining possibilities
            return {
                "suspects": self.possible_solution["suspects"].copy(),
                "weapons": self.possible_solution["weapons"].copy(),
                "rooms": self.possible_solution["rooms"].copy()
            }

    def is_solution_known(self):
        """Check if the solution is definitively known"""
        return (len(self.possible_solution["suspects"]) == 1 and
                len(self.possible_solution["weapons"]) == 1 and
                len(self.possible_solution["rooms"]) == 1)

    def apply_deductions(self):
        """
        Apply logical deductions to derive additional knowledge.
        This is where more sophisticated reasoning would happen.
        """
        # Apply various deduction rules:

        # Rule 1: If a card is known to be held by a player, remove from solution
        for player_id, cards in self.player_cards.items():
            for card in cards:
                # Find card type and category mapping
                card_category_map = {
                    "suspects": "suspects",
                    "weapons": "weapons",
                    "rooms": "rooms"
                }

                for category, items in self.categories.items():
                    if card in items:
                        # Remove from possible solution using the correct category key
                        if card in self.possible_solution[category]:
                            self.possible_solution[category].remove(card)
                        break

        # Rule 2: If all but one card in a category is eliminated, the last one must be the solution
        self._check_last_remaining()

        # Rule 3: If a player doesn't have any cards from a suggestion, and another player showed a card,
        # we can deduce which card was shown based on what we know about the first player's cards
        self._deduce_shown_cards_from_skipped_players()

        # Rule 4: If we know all but one card in a player's hand, we can deduce the last one
        self._deduce_complete_hands()

        # Rule 5: If a player has shown a card from a suggestion, and we know they don't have the other cards,
        # we can deduce which card they showed
        self._deduce_shown_cards_from_known_negatives()

        # Rule 6: If we know the total number of cards each player has, and we know all but one card,
        # we can deduce the last card
        self._deduce_from_card_counts()

    def _check_last_remaining(self):
        """Check if only one card remains in any category"""
        for category, items in self.possible_solution.items():
            if len(items) == 1:
                # This is the only possibility for this category
                # We might want to log this or take other actions
                pass

    def _deduce_shown_cards_from_skipped_players(self):
        """
        If a player doesn't have any cards from a suggestion, and another player showed a card,
        we can deduce which card was shown based on what we know about the first player's cards.
        """
        for event in self.events:
            if event["type"] == self.EVENT_SUGGESTION and event["responding_player"] is not None:
                # Get the suggestion details
                suggesting_player = event["suggesting_player"]
                room, suspect, weapon = event["suggestion"]
                responding_player = event["responding_player"]

                # Check players who were skipped (they don't have any of the cards)
                current_id = (suggesting_player + 1) % len(self.game.players)
                skipped_players = []

                while current_id != responding_player:
                    skipped_players.append(current_id)
                    current_id = (current_id + 1) % len(self.game.players)

                # If we know a skipped player doesn't have two of the cards, the responding player must have shown the third
                for skipped_id in skipped_players:
                    not_cards = self.player_not_cards[skipped_id]

                    # Check if the skipped player doesn't have two of the three cards
                    missing_count = sum(1 for card in [room, suspect, weapon] if card in not_cards)

                    if missing_count == 2:
                        # The responding player must have shown the third card
                        shown_card = next(card for card in [room, suspect, weapon] if card not in not_cards)

                        # Add this card to the responding player's known cards
                        self.player_cards[responding_player].add(shown_card)

                        # Remove from possible solution
                        for category, items in self.categories.items():
                            if shown_card in items:
                                self.possible_solution[category].discard(shown_card)
                                break

    def _deduce_complete_hands(self):
        """
        If we know all but one card in a player's hand, and we know how many cards they have,
        we can deduce the last one.
        """
        # This would require knowing the total number of cards each player has
        # For now, we'll skip this implementation
        pass

    def _deduce_shown_cards_from_known_negatives(self):
        """
        If a player has shown a card from a suggestion, and we know they don't have the other cards,
        we can deduce which card they showed.
        """
        for event in self.events:
            if event["type"] == self.EVENT_SUGGESTION and event["responding_player"] is not None:
                # Get the suggestion details
                room, suspect, weapon = event["suggestion"]
                responding_player = event["responding_player"]

                # If we know the responding player doesn't have two of the cards, they must have shown the third
                not_cards = self.player_not_cards[responding_player]

                # Check if the responding player doesn't have two of the three cards
                cards_not_held = [card for card in [room, suspect, weapon] if card in not_cards]

                if len(cards_not_held) == 2:
                    # The responding player must have shown the third card
                    shown_card = next(card for card in [room, suspect, weapon] if card not in cards_not_held)

                    # Add this card to the responding player's known cards
                    self.player_cards[responding_player].add(shown_card)

                    # Remove from possible solution
                    for category, items in self.categories.items():
                        if shown_card in items and shown_card in self.possible_solution[category]:
                            self.possible_solution[category].remove(shown_card)
                            break

    def _deduce_from_card_counts(self):
        """
        If we know the total number of cards each player has, and we know all but one card,
        we can deduce the last card.
        """
        # This would require knowing the total number of cards each player has
        # For now, we'll skip this implementation
        pass