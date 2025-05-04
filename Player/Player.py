# Player/Player.py
from Knowledge.PlayerKnowledge import PlayerKnowledge


class Player:
    """Base Player class for the Clue game."""

    def __init__(self, player_id, character_name):
        """Initialize a new Player."""
        self.player_id = player_id
        self.character_name = character_name
        self.character = None  # Will be set later
        self.hand = []  # Cards in the player's hand
        self.eliminated = False
        self.made_wrong_accusation = False

        # New unified knowledge system
        self.knowledge = None

    def initialize_knowledge(self, game):
        """Initialize the knowledge base with game information."""
        self.knowledge = PlayerKnowledge(self.player_id, game)

        # Add cards from hand to knowledge base
        for card in self.hand:
            card_type, card_name = card
            self.knowledge.add_card_to_hand(card_type, card_name)

    def add_card(self, card):
        """Add a card to the player's hand."""
        self.hand.append(card)

        # Update knowledge base if it's initialized
        if self.knowledge is not None:
            card_type, card_name = card
            self.knowledge.add_card_to_hand(card_type, card_name)

    def make_suggestion(self, room, suspect, weapon):
        """Make a suggestion."""
        # Record in knowledge - if initialized
        if self.knowledge is not None:
            # Future implementation: record own suggestion in knowledge
            pass

        return (room, suspect, weapon)

    def respond_to_suggestion(self, suggestion):
        """
        Respond to a suggestion by showing a matching card if possible.

        Args:
            suggestion: Tuple of (suspect, weapon, room)

        Returns:
            The card shown as a tuple (card_type, card_name) or None if no matching card
        """
        suspect, weapon, room = suggestion
        matching_cards = []

        # Check if player has any of the suggested cards
        for card_type, card_name in self.hand:
            if (card_type == "suspect" and card_name == suspect) or \
                    (card_type == "weapon" and card_name == weapon) or \
                    (card_type == "room" and card_name == room):
                matching_cards.append((card_type, card_name))

        # If player has matching cards, show one
        if matching_cards:
            # For human players, let them choose which card to show
            if not hasattr(self, 'is_ai') or not self.is_ai:
                # Only offer choice if there's more than one matching card
                if len(matching_cards) > 1:
                    print(f"\nYou need to show one of your cards to disprove the suggestion:")
                    for i, (card_type, card_name) in enumerate(matching_cards, 1):
                        print(f"{i}. {card_name} ({card_type})")

                    while True:
                        try:
                            choice = int(input("Which card would you like to show? "))
                            if 1 <= choice <= len(matching_cards):
                                return matching_cards[choice - 1]
                            else:
                                print("Invalid choice. Please try again.")
                        except ValueError:
                            print("Please enter a number.")
                else:
                    # Only one card to show
                    print(f"\nYou will show your {matching_cards[0][0]} card: {matching_cards[0][1]}")
                    return matching_cards[0]
            else:
                # AI players just return the first matching card
                # More sophisticated AI might choose strategically
                return matching_cards[0]

        return None

    def make_accusation(self, room, suspect, weapon):
        """Make an accusation."""
        return (room, suspect, weapon)

    def update_knowledge_from_suggestion(self, suggesting_player, suggestion, responding_player, revealed_card=None):
        """
        Update knowledge based on a suggestion and its response.

        Args:
            suggesting_player: Player ID who made the suggestion
            suggestion: Tuple of (room, suspect, weapon)
            responding_player: Player ID who responded (or None)
            revealed_card: Card that was revealed to suggesting_player (or None)
        """
        # Update unified knowledge system
        if self.knowledge is not None:
            self.knowledge.record_suggestion(
                suggesting_player, suggestion, responding_player, revealed_card
            )
            self.knowledge.apply_deductions()

    def update_knowledge_from_accusation(self, accusing_player, accusation, is_correct):
        """
        Update knowledge based on an accusation.

        Args:
            accusing_player: Player ID who made the accusation
            accusation: Tuple of (room, suspect, weapon)
            is_correct: Whether the accusation was correct
        """
        # Update unified knowledge system
        if self.knowledge is not None:
            self.knowledge.record_accusation(accusing_player, accusation, is_correct)
            self.knowledge.apply_deductions()

    def should_make_accusation(self, game=None):
        """
        Determine if player should make an accusation.

        Args:
            game: The Game instance (optional)

        Returns:
            bool: True if player should make an accusation
        """
        # Default implementation - don't make accusations automatically
        return False

    def eliminate(self):
        """Mark this player as eliminated from making moves."""
        self.eliminated = True
        self.made_wrong_accusation = True

    def get_solution_candidates(self):
        """
        Get the current solution candidates based on knowledge.

        Returns:
            dict: Dictionary with keys 'suspects', 'weapons', 'rooms' containing sets of candidates
        """
        if self.knowledge is not None:
            return self.knowledge.best_guess_solution()

        # Fallback if knowledge system not initialized
        return {
            "suspects": set(),
            "weapons": set(),
            "rooms": set()
        }

    # Player/Player.py

    def get_available_moves(self, mansion_board, character_board, dice_roll):
        """
        Get available moves for a player based on the current board state and dice roll.

        Args:
            mansion_board: The mansion board
            character_board: The character board with player positions
            dice_roll: The number of steps the player can take

        Returns:
            A list of valid moves the player can make
        """
        from Actions.Movement import get_available_moves

        # Get the character's current position
        current_position = self.character.position

        # Use the movement module to calculate available moves
        return get_available_moves(
            current_position,
            mansion_board,
            character_board,
            dice_roll
        )

    def move(self, position):
        """Move the player's character to a new position."""
        if self.character:
            self.character.position = position
        else:
            print(f"Warning: Character not set for {self.character_name}")
