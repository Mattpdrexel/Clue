# Player/SimpleAIPlayer.py
from Player.Player import Player
import random


class SimpleAIPlayer(Player):
    """
    A simple AI player that makes random but valid moves.
    """

    def choose_move(self, available_moves):
        """Choose a move from available options."""
        if not available_moves:
            return None
        return random.choice(available_moves)

    def choose_suggestion(self, room):
        """Choose a suggestion to make."""
        suspect = random.choice(list(self.possible_suspects))
        weapon = random.choice(list(self.possible_weapons))
        return (room, suspect, weapon)

    def should_make_accusation(self):
        """Decide whether to make an accusation."""
        # Simple strategy: If we're confident in our solution, make an accusation
        if len(self.possible_suspects) == 1 and len(self.possible_weapons) == 1 and len(self.possible_rooms) == 1:
            return True
        return False

    def choose_accusation(self):
        """Choose an accusation to make."""
        # For a simple AI, just choose the most likely candidates
        suspect = next(iter(self.possible_suspects))
        weapon = next(iter(self.possible_weapons))
        room = next(iter(self.possible_rooms))
        return (room, suspect, weapon)