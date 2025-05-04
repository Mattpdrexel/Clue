# Player/SimpleAIPlayer.py
from Player.Player import Player
import random
from Game.GameLogic import process_accusation
from collections import deque


class SimpleAIPlayer(Player):
    """
    A simple AI player that makes decisions based on its knowledge base.

    This AI follows these strategies:
    1. Always leaves a room after making a suggestion
    2. Makes suggestions in rooms to gather information
    3. Makes an accusation when it has eliminated possibilities or after 80 turns
    """

    def __init__(self, player_id, character_name):
        """Initialize the SimpleAIPlayer with additional AI-specific attributes."""
        super().__init__(player_id, character_name)
        self.is_ai = True

        # Track whether we need to exit a room after making a suggestion
        self.must_exit_next_turn = False

        # Track which room we just made a suggestion in
        self.last_suggestion_room = None

        # Track last three positions to avoid getting stuck in loops
        self.last_positions = deque(maxlen=3)

        # Track visited rooms
        self.visited_rooms = set()

        # Track previous suggestions to avoid repeating them
        self.previous_suggestions = set()

        # Track turn count to increase risk-taking over time
        self.turn_count = 0

    def make_move(self, game, available_moves, die_roll):
        """
        Make a move decision based on available moves and game state.

        Args:
            game: The Game instance
            available_moves: List of available moves (rooms or coordinates)
            die_roll: The value rolled on the die

        Returns:
            The chosen move
        """
        # Increment turn counter
        self.turn_count += 1

        if not available_moves:
            return None

        # Get current position and room information
        current_position = self.character.position
        current_room = None

        if isinstance(current_position, str):
            current_room = current_position
        elif isinstance(current_position, tuple) and len(current_position) == 3:
            current_room = current_position[0]

        # Update visited rooms set
        if current_room:
            self.visited_rooms.add(current_room)

        # Handle the must_exit_next_turn flag (crucial for passing tests)
        if self.must_exit_next_turn and current_room:
            self.must_exit_next_turn = False

            # Find hallway moves (non-room moves)
            hallway_moves = [move for move in available_moves if
                             isinstance(move, tuple) and len(move) == 2]

            if hallway_moves:
                # Choose a hallway move to exit the room
                chosen_move = random.choice(hallway_moves)
                print(f"{self.character_name} exits the room")
                return chosen_move

        # Separate room moves and hallway moves
        room_moves = []
        hallway_moves = []

        for move in available_moves:
            if isinstance(move, str) or (isinstance(move, tuple) and len(move) == 3):
                # This is a room
                room_moves.append(move)
            else:
                # This is a hallway position
                hallway_moves.append(move)

        # Always prioritize moving to rooms
        if room_moves:
            # Check if we can go to the Clue room to make an accusation
            if self.turn_count > 80:
                clue_room_move = next((r for r in room_moves if self._get_room_name(r) == "Clue"), None)
                if clue_room_move:
                    print(f"{self.character_name} heads to the Clue room to make an accusation!")
                    return clue_room_move

            # Avoid rooms we just made a suggestion in
            available_room_moves = [r for r in room_moves
                                    if self._get_room_name(r) != self.last_suggestion_room]

            # If no alternate rooms available, use any room
            if not available_room_moves:
                available_room_moves = room_moves

            # Choose a room
            chosen_move = random.choice(available_room_moves)
            print(f"{self.character_name} moves to {self._get_room_name(chosen_move)}")

        # If no rooms are available, use hallways
        elif hallway_moves:
            # Avoid the last few positions if possible
            filtered_hallway_moves = [m for m in hallway_moves if m not in self.last_positions]
            if filtered_hallway_moves:
                hallway_moves = filtered_hallway_moves

            chosen_move = random.choice(hallway_moves)

        # No valid moves
        else:
            return None

        # Update our position history if this is a hallway move
        if isinstance(chosen_move, tuple) and len(chosen_move) == 2:
            self.last_positions.append(chosen_move)

        return chosen_move

    def _get_room_name(self, move):
        """Extract the room name from a move object"""
        if isinstance(move, str):
            return move
        elif isinstance(move, tuple) and len(move) == 3:
            return move[0]
        return None

    def handle_suggestion(self, game, room, required=False):
        """
        Make a suggestion when in a room, based on knowledge base.

        Args:
            game: The Game instance
            room: The room the player is currently in
            required: Whether a suggestion is required (just entered the room)

        Returns:
            tuple: (suspect, weapon, room) - The suggestion
        """
        # Set the flag to exit the room on next turn
        self.must_exit_next_turn = True
        self.last_suggestion_room = room

        # Always make suggestions when possible to gather information
        suggestion = self.choose_suggestion(game, room)
        suspect, weapon = suggestion[0], suggestion[1]  # room is already fixed

        # Record this suggestion to avoid repeating
        suggestion_key = (suspect, weapon, room)
        self.previous_suggestions.add(suggestion_key)

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
        # Get suspects and weapons still in our list of possibilities
        possible_suspects = list(self.possible_suspects) if self.possible_suspects else game.character_names
        possible_weapons = list(self.possible_weapons) if self.possible_weapons else game.weapon_names

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

    def see_refutation(self, card):
        """
        Called when another player shows a card to refute suggestion.
        Updates knowledge about known cards.

        Args:
            card: The card that was shown
        """
        # Remove the card from our lists of possible solutions
        if card in self.possible_suspects:
            self.possible_suspects.remove(card)
        if card in self.possible_weapons:
            self.possible_weapons.remove(card)
        if card in self.possible_rooms:
            self.possible_rooms.remove(card)

    def should_make_accusation(self, game):
        """
        Determine if we have enough information to make an accusation.

        Args:
            game: The Game instance

        Returns:
            bool: True if we should try to make an accusation
        """
        # The key criteria:
        # 1. We have a single suspect, weapon, and room
        # 2. The game has been going on for a while (80+ turns)

        solution_candidates = self.get_solution_candidates()
        has_unique_solution = (len(solution_candidates["suspects"]) == 1 and
                               len(solution_candidates["weapons"]) == 1 and
                               len(solution_candidates["rooms"]) == 1)

        # If we're in the Clue room after 80 turns, just make an accusation
        current_position = self.character.position
        in_clue_room = False

        if isinstance(current_position, str) and current_position == "Clue":
            in_clue_room = True
        elif isinstance(current_position, tuple) and len(current_position) == 3 and current_position[0] == "Clue":
            in_clue_room = True

        if in_clue_room and self.turn_count > 80:
            return True

        # If we have a unique solution and we're in the Clue room, make an accusation
        if has_unique_solution and in_clue_room:
            return True

        return False

    def handle_accusation(self, game):
        """
        Handle making an accusation when in the Clue room.

        Args:
            game: The Game instance

        Returns:
            bool: True if accusation was made, False otherwise
        """
        # Check if AI should make an accusation
        if not self.should_make_accusation(game):
            return False

        # Get the solution candidates
        solution = self.get_solution_candidates()

        # Pick the most likely candidates
        if solution["suspects"]:
            suspect = next(iter(solution["suspects"]))
        else:
            suspect = random.choice(game.character_names)

        if solution["weapons"]:
            weapon = next(iter(solution["weapons"]))
        else:
            weapon = random.choice(game.weapon_names)

        if solution["rooms"]:
            room = next(iter(solution["rooms"]))
        else:
            room = random.choice(game.room_names)

        print(f"{self.character_name} makes an accusation: {suspect} in the {room} with the {weapon}")

        # Submit the accusation
        result = process_accusation(game, self, suspect, weapon, room)

        if result:
            print(f"{self.character_name} was correct!")
        else:
            print(f"{self.character_name} was wrong and is eliminated.")

        return True

    def get_solution_candidates(self):
        """
        Get the current solution candidates based on the player's knowledge.

        Returns:
            dict: Dictionary with sets of possible suspects, weapons, and rooms
        """
        return {
            "suspects": self.possible_suspects,
            "weapons": self.possible_weapons,
            "rooms": self.possible_rooms
        }