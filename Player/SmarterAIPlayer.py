# Player/SmarterAIPlayer.py
from Player.KnowledgeAIPlayer import KnowledgeAIPlayer
from Knowledge.ImprovedKnowledgeBase import ImprovedKnowledgeBase
import random
from collections import deque


class SmarterAIPlayer(KnowledgeAIPlayer):
    """
    A smarter AI player that uses a more sophisticated knowledge base
    to make better deductions and gameplay decisions.
    """

    def __init__(self, player_id, character_name):
        """Initialize the SmarterAIPlayer."""
        super().__init__(player_id, character_name)
        self.last_positions = deque(maxlen=3)  # Initialize with max length for automatic size management
        self.kb = None
        self.turn_count = 0
        self.previous_suggestions = set()
        self.must_exit_next_turn = False
        self.last_suggestion_room = None
        self.target_room = None
        self.eliminated = False

    def initialize_knowledge_base(self, game):
        """Initialize the improved knowledge base with game information."""
        self.game = game  # Store reference to game
        self.kb = ImprovedKnowledgeBase(game, self.player_id)
        self.kb.initialize_with_hand(self.hand)

    def choose_suggestion(self, game, room):
        """
        Choose which suspect and weapon to suggest based on knowledge.
        Uses expected information gain to choose the most informative suggestion.

        Args:
            game: The Game instance
            room: The current room

        Returns:
            tuple: (suspect, weapon) for the suggestion
        """
        # Check if player is eliminated
        if self.eliminated:
            return None

        # Get all possible suspects and weapons
        envelope = self.kb.envelope_candidates()
        possible_suspects = list(envelope["suspects"])
        possible_weapons = list(envelope["weapons"])

        # If no candidates remain, fall back to all options
        if not possible_suspects:
            possible_suspects = game.character_names
        if not possible_weapons:
            possible_weapons = game.weapon_names

        # Create all possible combinations
        suggestions = []
        for suspect in possible_suspects:
            for weapon in possible_weapons:
                # Skip combinations we've already suggested
                if (suspect, weapon, room) in self.previous_suggestions:
                    continue

                # Calculate information gain - negate to maximize information
                room_card = room  # Ensure we're using the room name as a string
                score = -self.kb.expected_information_gain({suspect, weapon, room_card})
                suggestions.append((score, (suspect, weapon)))

        # If no valid suggestion found, just pick randomly
        if not suggestions:
            suspect = random.choice(possible_suspects)
            weapon = random.choice(possible_weapons)
            return (suspect, weapon)

        # Sort by score (lowest/negative score = highest info gain)
        suggestions.sort()

        # Return the suggestion with highest info gain
        return suggestions[0][1]

    def _get_room_name(self, move):
        """Extract the room name from a move object"""
        if isinstance(move, str):
            return move
        elif isinstance(move, tuple) and len(move) == 3:
            return move[0]
        return None  # For hallway moves (tuples of length 2)

    def make_move(self, game, available_moves, die_roll):
        """
        Make a strategic move based on current knowledge.

        Args:
            game: The Game instance
            available_moves: List of available moves
            die_roll: The value rolled on the die

        Returns:
            The chosen move
        """
        # Check if player is eliminated
        if self.eliminated:
            return None

        # Initialize knowledge base if needed
        if self.kb is None:
            self.initialize_knowledge_base(game)

        # Increment turn counter
        self.turn_count += 1

        if not available_moves:
            return None

        # If we need to exit room, prioritize hallway moves
        if self.must_exit_next_turn:
            hallway_moves = [m for m in available_moves
                             if isinstance(m, tuple) and len(m) == 2]
            if hallway_moves:
                self.must_exit_next_turn = False
                return random.choice(hallway_moves)

        # Separate room moves and hallway moves
        room_moves = []
        hallway_moves = []

        for move in available_moves:
            if isinstance(move, str) or (isinstance(move, tuple) and len(move) == 3):
                room_moves.append(move)
            else:
                hallway_moves.append(move)

        # Strategic priorities:
        # 1. If we can deduce the solution, head to Clue room
        solution_known = self.kb.is_solution_known()
        if solution_known:
            clue_room_move = next((m for m in available_moves if self._get_room_name(m) == "Clue"), None)
            if clue_room_move:
                print(f"{self.character_name} heads to the Clue room to make an accusation!")
                return clue_room_move

        # 2. Prioritize rooms we haven't visited or made suggestions in
        if room_moves:
            # Avoid rooms we've suggested in recently
            unvisited_rooms = [m for m in room_moves
                               if self._get_room_name(m) != self.last_suggestion_room]

            # If we have unvisited rooms, prioritize those in envelope candidates
            if unvisited_rooms:
                envelope_candidates = self.kb.envelope_candidates()["rooms"]
                candidate_room_moves = [m for m in unvisited_rooms
                                        if self._get_room_name(m) in envelope_candidates]

                if candidate_room_moves:
                    return random.choice(candidate_room_moves)
                return random.choice(unvisited_rooms)

            # If all rooms have been visited, just choose any room
            return random.choice(room_moves)

        # 3. If no rooms available, move through hallways
        # Avoid the last few positions if possible to prevent cycles
        filtered_hallway_moves = [m for m in hallway_moves if m not in self.last_positions]
        if filtered_hallway_moves:
            chosen_move = random.choice(filtered_hallway_moves)
        else:
            chosen_move = random.choice(hallway_moves)

        # Update position history - deque with maxlen handles this automatically
        if isinstance(chosen_move, tuple) and len(chosen_move) == 2:
            self.last_positions.append(chosen_move)

        return chosen_move

    def handle_suggestion(self, game, room, required=False):
        """
        Handle making a suggestion when in a room.

        Args:
            game: The Game instance
            room: The current room
            required: Whether a suggestion is required (just entered the room)

        Returns:
            tuple: (suspect, weapon, room) for the suggestion
        """
        # Check if player is eliminated
        if self.eliminated:
            return None

        # Set flag to exit room next turn
        self.must_exit_next_turn = True
        self.last_suggestion_room = room

        # Choose which suspect and weapon to suggest
        suggestion = self.choose_suggestion(game, room)
        if suggestion is None:
            return None

        suspect, weapon = suggestion

        # Record this suggestion to avoid repeating
        self.previous_suggestions.add((suspect, weapon, room))

        print(f"{self.character_name} suggests: {suspect} in the {room} with the {weapon}")
        return (room, suspect, weapon)  # Return in the expected order: room, suspect, weapon

    def update_knowledge_from_suggestion(self, suggesting_player, suggestion, responding_player, revealed_card=None):
        """
        Update knowledge based on a suggestion and its response.

        Args:
            suggesting_player (int): Player ID who made the suggestion
            suggestion (tuple): (room, suspect, weapon)
            responding_player (int): Player ID who responded (or None)
            revealed_card (tuple, optional): Card that was revealed to suggesting_player
        """
        # Check if player is eliminated
        if self.eliminated:
            return

        # Make sure KB is initialized
        if self.kb is None and hasattr(self, 'game'):
            self.initialize_knowledge_base(self.game)

        # Forward to KB to update knowledge
        if self.kb:
            # If we were shown a card, we know exactly who has it
            if revealed_card is not None:
                card_type, card_name = revealed_card
                self.kb.set_holder(card_name, responding_player)

            # No one could refute - all cards might be in envelope
            elif responding_player is None:
                room, suspect, weapon = suggestion
                # Set these cards as possible envelope cards
                self.kb.set_holder(room, "ENVELOPE")
                self.kb.set_holder(suspect, "ENVELOPE")
                self.kb.set_holder(weapon, "ENVELOPE")

            # Someone refuted but we don't know which card
            else:
                room, suspect, weapon = suggestion
                cards_in_suggestion = {room, suspect, weapon}

                # That player has at least one of these cards
                self.kb.record_atleast_one(responding_player, cards_in_suggestion)

            # If we were observing another player's suggestion
            if suggesting_player != self.player_id and responding_player is not None:
                # Handle the player elimination by exclusion logic
                # Any player who was skipped during suggestion response doesn't have any of the cards
                room, suspect, weapon = suggestion

                # Find all players between suggester and responder who were skipped
                current_id = (suggesting_player + 1) % len(self.game.players)
                while current_id != responding_player:
                    # This player was skipped, so they don't have any of the suggestion cards
                    self.kb.eliminate(room, current_id)
                    self.kb.eliminate(suspect, current_id)
                    self.kb.eliminate(weapon, current_id)
                    current_id = (current_id + 1) % len(self.game.players)

    def handle_accusation(self, game):
        """
        Handle making an accusation.

        Args:
            game: The Game instance

        Returns:
            tuple: (room, suspect, weapon) for the accusation
        """
        # Check if player is eliminated
        if self.eliminated:
            return None

        # Get the most likely solution
        envelope = self.kb.envelope_candidates()

        # If we have perfect knowledge, use it
        if (len(envelope["suspects"]) == 1 and
                len(envelope["weapons"]) == 1 and
                len(envelope["rooms"]) == 1):
            suspect = list(envelope["suspects"])[0]
            weapon = list(envelope["weapons"])[0]
            room = list(envelope["rooms"])[0]
        else:
            # Otherwise take our best guess
            suspect = random.choice(list(envelope["suspects"]))
            weapon = random.choice(list(envelope["weapons"]))
            room = random.choice(list(envelope["rooms"]))

        print(f"{self.character_name} makes an accusation: {suspect} in the {room} with the {weapon}")
        return (room, suspect, weapon)

    def update_knowledge_from_failed_accusation(self, player_id, accusation):
        """
        Update knowledge when an accusation fails.

        Args:
            player_id (int): ID of player who made the failed accusation
            accusation (tuple): (room, suspect, weapon) of the accusation
        """
        # Check if player is eliminated
        if self.eliminated:
            return

        # At least one of the cards is not in the envelope
        if self.kb:
            room, suspect, weapon = accusation
            cards = {suspect, weapon, room}
            # Record that at least one of these cards is not in the envelope
            self.kb.record_atleast_one_not_in_envelope(cards)