from Player.Player import Player

class AIPlayer(Player):
    """
    A AI player that makes decisions based on its knowledge base.

    """

    def __init__(self, player_id, character_name):
        """Initialize the SimpleAIPlayer with additional AI-specific attributes."""
        super().__init__(player_id, character_name)
        self.is_ai = True

        # Track whether we need to exit a room after making a suggestion
        self.must_exit_next_turn = False

        # Track which room we just made a suggestion in
        self.last_suggestion_room = None

        # Track visited rooms
        self.visited_rooms = set()

        # Track previous suggestions to avoid repeating them
        self.previous_suggestions = set()

        # Track turn count to increase risk-taking over time
        self.turn_count = 0

