# tests/test_ai_player.py
import unittest
import sys
import os
from collections import deque
import random

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from Player.AIPlayer import AIPlayer
from Player.Player import Player


class MockCharacter:
    """Mock character for testing AI player position logic"""

    def __init__(self, position):
        self.position = position


class MockGame:
    """Mock game object for testing"""

    def __init__(self):
        # Define all game elements
        self.character_names = ["Miss Scarlet", "Colonel Mustard", "Mrs. White",
                                "Reverend Green", "Mrs. Peacock", "Professor Plum"]
        self.weapon_names = ["Candlestick", "Knife", "Lead Pipe",
                             "Revolver", "Rope", "Wrench"]
        self.room_names = ["Study", "Hall", "Lounge", "Library", "Billiard Room",
                           "Dining Room", "Conservatory", "Ballroom", "Kitchen", "Clue"]

        # Create player list with mock players
        self.players = []
        for i in range(3):
            mock_player = type('MockPlayer', (), {'player_id': i, 'character_name': f"Player {i}"})()
            self.players.append(mock_player)


class TestAIPlayer(unittest.TestCase):
    def setUp(self):
        """Set up the test environment"""
        # Create a mock game
        self.game = MockGame()

        # Create an AI player
        self.ai_player = AIPlayer(player_id=1, character_name="Miss Scarlet")

        # Initialize knowledge
        self.ai_player.initialize_knowledge(self.game)

        # Test cards
        self.suspect_card = ("suspect", "Colonel Mustard")
        self.weapon_card = ("weapon", "Knife")
        self.room_card = ("room", "Kitchen")

    def test_initialization(self):
        """Test that the AI player is initialized correctly"""
        # Check core attributes
        self.assertEqual(self.ai_player.player_id, 1)
        self.assertEqual(self.ai_player.character_name, "Miss Scarlet")
        self.assertTrue(self.ai_player.is_ai)

        # Check AI-specific attributes
        self.assertFalse(self.ai_player._must_exit_next_turn)
        self.assertEqual(len(self.ai_player.last_positions), 0)
        self.assertEqual(len(self.ai_player._visited_rooms), 0)
        self.assertEqual(len(self.ai_player._previous_suggestions), 0)
        self.assertEqual(self.ai_player._turn_counter, 0)

    def test_make_move_room_preference(self):
        """Test that AI prefers unvisited rooms"""
        # Setup available moves
        available_moves = ["Study", "Hall", "Lounge"]

        # Make move and see which room was chosen
        chosen_move = self.ai_player.make_move(self.game, available_moves, 5)

        # Verify the move is one of the available options
        self.assertIn(chosen_move, available_moves)

        # Add the chosen room to visited rooms
        self.ai_player._visited_rooms.add(chosen_move)

        # Make multiple moves to check probability of choosing unvisited rooms
        unvisited_chosen = 0
        for _ in range(10):
            move = self.ai_player.make_move(self.game, available_moves, 5)
            if move != chosen_move:  # If it chooses an unvisited room
                unvisited_chosen += 1

        # AI should prefer unvisited rooms, so should choose them frequently
        self.assertGreaterEqual(unvisited_chosen, 5)  # Should choose unvisited in most cases

    def test_make_move_after_suggestion(self):
        """Test that AI exits a room after making a suggestion"""
        # Setup that AI just made a suggestion
        self.ai_player._must_exit_next_turn = True

        # Available moves include both rooms and corridors
        available_moves = ["Study", (1, 2), (3, 4)]

        # AI should choose a corridor move
        move = self.ai_player.make_move(self.game, available_moves, 5)

        # Verify it's a corridor move (not a string)
        self.assertFalse(isinstance(move, str))

        # Verify the flag was reset
        self.assertFalse(self.ai_player._must_exit_next_turn)

    def test_handle_suggestion(self):
        """Test AI's suggestion handling"""
        room = "Hall"

        # Make a suggestion
        suggestion = self.ai_player.handle_suggestion(self.game, room)

        # Verify format (room, suspect, weapon)
        self.assertEqual(len(suggestion), 3)
        self.assertEqual(suggestion[0], room)
        self.assertIn(suggestion[1], self.game.character_names)
        self.assertIn(suggestion[2], self.game.weapon_names)

        # Verify room was added to visited rooms
        self.assertIn(room, self.ai_player._visited_rooms)

        # Verify exit flag was set
        self.assertTrue(self.ai_player._must_exit_next_turn)

        # Verify suggestion was recorded
        self.assertTrue((suggestion[1], suggestion[2], room) in self.ai_player._previous_suggestions)

    def test_choose_suspect_weapon(self):
        """Test choosing suspects and weapons for suggestions"""
        room = "Study"

        # Add some cards to AI's hand to eliminate them as candidates
        self.ai_player.add_card(self.suspect_card)  # Colonel Mustard
        self.ai_player.add_card(self.weapon_card)  # Knife

        # Make multiple suggestions and verify they tend to use cards still in solution
        for _ in range(5):
            suspect, weapon = self.ai_player._choose_suspect_weapon(room, self.game)

            # The suspect and weapon should be valid game elements
            self.assertIn(suspect, self.game.character_names)
            self.assertIn(weapon, self.game.weapon_names)

            # Cards in hand should not be chosen (they're eliminated from solution)
            self.assertNotEqual(suspect, "Colonel Mustard")
            self.assertNotEqual(weapon, "Knife")

    def test_should_make_accusation(self):
        """Test AI's decision to make an accusation"""
        # Initially, AI shouldn't make accusation (not enough knowledge)
        self.assertFalse(self.ai_player.should_make_accusation(self.game))

        # Set up a scenario where AI knows the solution
        # First, narrow down the solution possibilities
        self.ai_player.knowledge.possible_solution["suspects"] = {"Mrs. White"}
        self.ai_player.knowledge.possible_solution["weapons"] = {"Rope"}
        self.ai_player.knowledge.possible_solution["rooms"] = {"Hall"}

        # But AI is not in the Clue room, so still shouldn't accuse
        self.ai_player.character = MockCharacter("Study")
        self.assertFalse(self.ai_player.should_make_accusation(self.game))

        # Now put AI in the Clue room
        self.ai_player.character = MockCharacter("Clue")
        # Now it should be ready to accuse
        self.assertTrue(self.ai_player.should_make_accusation(self.game))

        # Try with a tuple position format
        self.ai_player.character = MockCharacter(("Clue", 5, 5))
        self.assertTrue(self.ai_player.should_make_accusation(self.game))

    def test_make_accusation(self):
        """Test AI making an accusation"""
        # Set up a scenario where AI knows the solution
        self.ai_player.knowledge.possible_solution["suspects"] = {"Mrs. White"}
        self.ai_player.knowledge.possible_solution["weapons"] = {"Rope"}
        self.ai_player.knowledge.possible_solution["rooms"] = {"Hall"}

        # Get the accusation
        accusation = self.ai_player.make_accusation(self.game)

        # Verify it matches the solution
        self.assertEqual(accusation, ("Hall", "Mrs. White", "Rope"))

    def test_room_name_helper(self):
        """Test the _room_name helper method"""
        # Test with string room
        self.assertEqual(self.ai_player._room_name("Study"), "Study")

        # Test with tuple room position
        self.assertEqual(self.ai_player._room_name(("Hall", 5, 8)), "Hall")

        # Test with non-room position
        self.assertIsNone(self.ai_player._room_name((5, 8)))

    def test_multiple_suggestions_avoid_repetition(self):
        """Test that AI avoids repeating the same suggestions"""
        room = "Study"

        # Make several suggestions and record them
        previous_suggestions = set()
        for _ in range(5):
            suggestion = self.ai_player.handle_suggestion(self.game, room)
            suspect, weapon = suggestion[1], suggestion[2]

            # Convert to the format used in _previous_suggestions
            suggestion_key = (suspect, weapon, room)

            # It should not repeat suggestions unless all options exhausted
            if len(previous_suggestions) < len(self.game.character_names) * len(self.game.weapon_names):
                self.assertNotIn(suggestion_key, previous_suggestions)

            previous_suggestions.add(suggestion_key)

    def test_ai_make_move_to_clue_room(self):
        """Test that AI prioritizes the Clue room when ready to accuse"""
        # Set up a scenario where AI knows the solution
        self.ai_player.knowledge.possible_solution["suspects"] = {"Mrs. White"}
        self.ai_player.knowledge.possible_solution["weapons"] = {"Rope"}
        self.ai_player.knowledge.possible_solution["rooms"] = {"Hall"}

        # Add character to make _ready_to_accuse() work
        self.ai_player.character = MockCharacter("Study")  # Not in Clue room

        # Available moves include the Clue room
        available_moves = ["Study", "Clue", "Kitchen"]

        # AI should prioritize the Clue room when ready to accuse
        move = self.ai_player.make_move(self.game, available_moves, 5)
        self.assertEqual(move, "Clue")

    def test_incrementing_turn_counter(self):
        """Test that the turn counter increments with each move"""
        initial_count = self.ai_player._turn_counter

        # Make moves and check counter
        self.ai_player.make_move(self.game, ["Study"], 5)
        self.assertEqual(self.ai_player._turn_counter, initial_count + 1)

        self.ai_player.make_move(self.game, ["Hall"], 5)
        self.assertEqual(self.ai_player._turn_counter, initial_count + 2)


if __name__ == "__main__":
    unittest.main()