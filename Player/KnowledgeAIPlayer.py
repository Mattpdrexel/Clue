from Player.Player import Player
from Knowledge.KnowledgeBase import KnowledgeBase
import random


class KnowledgeAIPlayer(Player):
    """
    Base class for AI players that use a knowledge base to make decisions.
    Extends the Player class with AI-specific functionality.
    """

    def __init__(self, player_id, character_name):
        """Initialize the KnowledgeAIPlayer."""
        super().__init__(player_id, character_name)
        self.is_ai = True
        self.kb = None  # Will be initialized when game is available

        # Track whether player needs to exit room after making a suggestion
        self.must_exit_next_turn = False
        self.last_suggestion_room = None

        # Track turn count
        self.turn_count = 0

        # Track previous suggestions to avoid repeating
        self.previous_suggestions = set()

    def initialize_knowledge_base(self, game):
        """Initialize the knowledge base with game information."""
        self.kb = KnowledgeBase(game, self.player_id)
        self.kb.initialize_with_hand(self.hand)

    def make_move(self, game, available_moves, die_roll):
        """
        Make a move decision based on available moves and game state.

        Args:
            game: The Game instance
            available_moves: List of available moves
            die_roll: The value rolled on the die

        Returns:
            The chosen move
        """
        # Initialize knowledge base if needed
        if self.kb is None:
            self.initialize_knowledge_base(game)

        # Increment turn counter
        self.turn_count += 1

        # If we need to exit room, prioritize hallway moves
        if self.must_exit_next_turn and available_moves:
            # Split moves into rooms and corridors
            room_moves = [m for m in available_moves if isinstance(m, str)]
            corridor_moves = [m for m in available_moves if not isinstance(m, str)]

            if corridor_moves:
                self.must_exit_next_turn = False
                return random.choice(corridor_moves)

        # Each subclass should implement its own strategy
        # This is the default random selection
        if available_moves:
            return random.choice(available_moves)
        return None

    def add_card(self, card):
        """
        Add a card to the player's hand.

        Args:
            card: A tuple (card_type, card_name)
        """
        super().add_card(card)

        # Also update knowledge base if initialized
        if self.kb is not None:
            self.kb.set_holder(card[1], self.player_id)

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
        # Set flag to exit room next turn
        self.must_exit_next_turn = True
        self.last_suggestion_room = room

        # Choose which suspect and weapon to suggest
        suggestion = self.choose_suggestion(game, room)
        suspect, weapon = suggestion

        # Record this suggestion to avoid repeating
        self.previous_suggestions.add((suspect, weapon, room))

        print(f"{self.character_name} suggests: {suspect} in the {room} with the {weapon}")
        return (suspect, weapon, room)

    def choose_suggestion(self, game, room):
        """
        Choose which suspect and weapon to suggest based on knowledge.

        Args:
            game: The Game instance
            room: The current room

        Returns:
            tuple: (suspect, weapon) for the suggestion
        """
        # Initialize knowledge base if not done already
        if self.kb is None:
            self.initialize_knowledge_base(game)

        # Get envelope candidates
        envelope = self.kb.envelope_candidates()

        # Prioritize suspects and weapons that could be in the envelope
        possible_suspects = list(envelope["suspects"])
        possible_weapons = list(envelope["weapons"])

        # If no candidates remain, fall back to all options
        if not possible_suspects:
            possible_suspects = game.character_names
        if not possible_weapons:
            possible_weapons = game.weapon_names

        # Try to find a combination we haven't suggested yet
        novel_suggestions = []
        for s in possible_suspects:
            for w in possible_weapons:
                if (s, w, room) not in self.previous_suggestions:
                    novel_suggestions.append((s, w))

        # If we have novel suggestions, use one of those
        if novel_suggestions:
            suspect, weapon = random.choice(novel_suggestions)
        # Otherwise fall back to any possible suspect/weapon
        else:
            suspect = random.choice(possible_suspects)
            weapon = random.choice(possible_weapons)

        return (suspect, weapon)

    def respond_to_suggestion(self, suggestion):
        """
        Respond to another player's suggestion if possible.

        Args:
            suggestion (tuple): (room, suspect, weapon)

        Returns:
            tuple or None: The card being shown, or None if can't disprove
        """
        # The base respond_to_suggestion is fine for now
        return super().respond_to_suggestion(suggestion)

    def see_refutation(self, card):
        """
        Called when another player shows a card to refute suggestion.
        Updates knowledge about known cards.

        Args:
            card: The card that was shown
        """
        # If knowledge base is initialized, eliminate this card from envelope
        if self.kb is not None:
            self.kb.eliminate(card, "ENVELOPE")

    def update_knowledge_from_suggestion(self, suggesting_player, suggestion, responding_player, revealed_card=None):
        """
        Update knowledge based on a suggestion and its response.

        Args:
            suggesting_player (int): Player ID who made the suggestion
            suggestion (tuple): (room, suspect, weapon)
            responding_player (int): Player ID who responded (or None)
            revealed_card (tuple, optional): Card that was revealed to suggesting_player
        """
        # Initialize knowledge base if needed
        if self.kb is None:
            return

        room, suspect, weapon = suggestion

        # Reformat to match knowledge base expectation (suspect, weapon, room)
        kb_suggestion = (suspect, weapon, room)

        # Update knowledge base
        self.kb.update_from_suggestion(suggesting_player, kb_suggestion,
                                      responding_player,
                                      revealed_card[1] if revealed_card else None)

    def should_make_accusation(self, game):
        """
        Determine if the AI has enough information to make an accusation.

        Args:
            game: The Game instance

        Returns:
            bool: True if AI should make an accusation
        """
        # Initialize knowledge base if needed
        if self.kb is None:
            self.initialize_knowledge_base(game)

        # Check if solution is known
        if self.kb.is_solution_known():
            # Need to be in the Clue room
            current_position = self.character.position
            in_clue_room = False

            if isinstance(current_position, str) and current_position == "Clue":
                in_clue_room = True
            elif isinstance(current_position, tuple) and len(current_position) == 3 and current_position[0] == "Clue":
                in_clue_room = True

            return in_clue_room

        # By default, don't make an accusation
        return False

    def handle_accusation(self, game):
        """
        Handle making an accusation.

        Args:
            game: The Game instance

        Returns:
            bool: True if accusation was made, False otherwise
        """
        from Game.GameLogic import process_accusation

        # Initialize knowledge base if needed
        if self.kb is None:
            self.initialize_knowledge_base(game)

        # Check if should make an accusation
        if not self.should_make_accusation(game):
            return False

        # Get the solution from knowledge base
        solution = self.kb.get_solution()

        if solution:
            suspect, weapon, room = solution

            print(f"{self.character_name} makes an accusation: {suspect} in the {room} with the {weapon}")

            # Submit the accusation
            result = process_accusation(game, self, suspect, weapon, room)

            if result:
                print(f"{self.character_name} was correct!")
            else:
                print(f"{self.character_name} was wrong and is eliminated.")

            return True

        return False