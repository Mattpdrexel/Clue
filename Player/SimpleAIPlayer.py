# Player/SimpleAIPlayer.py
from Player.Player import Player
import random


class SimpleAIPlayer(Player):
    """
    A simple AI player that makes random but valid moves.
    """

    # Player/SimpleAIPlayer.py - update with required flag
    def make_move(self, game, available_moves, die_roll):
        """Make a move decision."""
        # Prioritize entering rooms if possible
        room_moves = []
        hallway_moves = []

        for move in available_moves:
            if isinstance(move, str) or (isinstance(move, tuple) and len(move) == 3):
                # This is a room
                room_moves.append(move)
            else:
                # This is a hallway position
                hallway_moves.append(move)

        # Prefer rooms over hallways
        if room_moves:
            chosen_move = random.choice(room_moves)
        elif hallway_moves:
            chosen_move = random.choice(hallway_moves)
        else:
            return None

        print(f"{self.character_name} moves to {chosen_move}")
        return chosen_move

    def handle_suggestion(self, game, room, required=False):
        """Handle making a suggestion."""
        # Simple AI always makes a suggestion when in a room
        suggestion = self.choose_suggestion(room)
        room, suspect, weapon = suggestion

        print(f"{self.character_name} suggests: {suspect} in the {room} with the {weapon}")
        return suggestion

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

    # Player/SimpleAIPlayer.py - handle_accusation method
    def handle_accusation(self, game):
        """
        Handle making an accusation.

        Args:
            game: Game instance

        Returns:
            bool: True if an accusation was made
        """
        # Check if AI is confident enough to make an accusation
        # This is a simple implementation - a more sophisticated AI would have more logic

        # First check if AI is in the Clue room
        current_position = self.character.position
        in_clue_room = False

        if isinstance(current_position, str) and current_position == "Clue":
            in_clue_room = True
        elif isinstance(current_position, tuple) and len(current_position) == 3 and current_position[0] == "Clue":
            in_clue_room = True

        if not in_clue_room:
            # Not in Clue room, can't make accusation
            return False

        # Simple AI will make an accusation if it's very confident
        # (e.g., only one possibility for each category)
        solution_candidates = self.get_solution_candidates()

        if (len(solution_candidates["suspects"]) == 1 and
                len(solution_candidates["weapons"]) == 1 and
                len(solution_candidates["rooms"]) == 1):
            suspect = list(solution_candidates["suspects"])[0]
            weapon = list(solution_candidates["weapons"])[0]
            room = list(solution_candidates["rooms"])[0]

            # Make the accusation
            accusation = self.make_accusation(room, suspect, weapon)
            print(f"{self.character_name} accuses: {suspect} in the {room} with the {weapon}")

            return True

        return False