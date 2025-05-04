# tests/test_simple_ai_suggestion_knowledge.py
import unittest
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from Player.SimpleAIPlayer import SimpleAIPlayer
from Player.Player import Player


class TestSimpleAISuggestionKnowledge(unittest.TestCase):

    def setUp(self):
        # Create SimpleAIPlayer for testing
        self.ai_player = SimpleAIPlayer(1, "Mrs Peacock")

        # Create a mock character for the player
        class MockCharacter:
            def __init__(self):
                self.position = (0, 0)
                self.name = "Mrs Peacock"

        self.ai_player.character = MockCharacter()

        # Initialize knowledge base
        self.ai_player.possible_suspects = {"Miss Scarlet", "Colonel Mustard", "Mrs. White",
                                            "Reverend Green", "Mrs Peacock", "Professor Plum"}
        self.ai_player.possible_weapons = {"Candlestick", "Lead Pipe", "Wrench",
                                           "Knife", "Revolver", "Rope"}
        self.ai_player.possible_rooms = {"Study", "Hall", "Lounge", "Dining Room", "Kitchen",
                                         "Ball Room", "Conservatory", "Billiard Room", "Library", "Clue"}

        # Mock game object
        class MockGame:
            def __init__(self):
                self.character_names = ["Miss Scarlet", "Colonel Mustard", "Mrs. White",
                                        "Reverend Green", "Mrs Peacock", "Professor Plum"]
                self.weapon_names = ["Candlestick", "Lead Pipe", "Wrench",
                                     "Knife", "Revolver", "Rope"]
                self.room_names = ["Study", "Hall", "Lounge", "Dining Room", "Kitchen",
                                   "Ball Room", "Conservatory", "Billiard Room", "Library", "Clue"]

        self.game = MockGame()

    def test_see_refutation_updates_knowledge(self):
        """Test that see_refutation correctly updates player knowledge"""
        # Initial knowledge state
        self.assertIn("Miss Scarlet", self.ai_player.possible_suspects)
        self.assertIn("Knife", self.ai_player.possible_weapons)
        self.assertIn("Hall", self.ai_player.possible_rooms)

        # Update knowledge with refutations
        self.ai_player.see_refutation("Miss Scarlet")
        self.ai_player.see_refutation("Knife")
        self.ai_player.see_refutation("Hall")

        # Check that knowledge is updated
        self.assertNotIn("Miss Scarlet", self.ai_player.possible_suspects)
        self.assertNotIn("Knife", self.ai_player.possible_weapons)
        self.assertNotIn("Hall", self.ai_player.possible_rooms)

        # Other items should still be in the sets
        self.assertIn("Colonel Mustard", self.ai_player.possible_suspects)
        self.assertIn("Rope", self.ai_player.possible_weapons)
        self.assertIn("Kitchen", self.ai_player.possible_rooms)

    def test_choose_suggestion_uses_knowledge(self):
        """Test that choose_suggestion uses player knowledge"""
        # Initial knowledge
        all_suspects = len(self.ai_player.possible_suspects)
        all_weapons = len(self.ai_player.possible_weapons)

        # Make a suggestion
        suggestion = self.ai_player.choose_suggestion(self.game, "Hall")

        # Should get back a tuple of (suspect, weapon)
        self.assertEqual(len(suggestion), 2)

        # The suggested suspect and weapon should be in our possible sets
        self.assertIn(suggestion[0], self.ai_player.possible_suspects)
        self.assertIn(suggestion[1], self.ai_player.possible_weapons)

        # Remove some items from possibility sets
        self.ai_player.see_refutation("Miss Scarlet")
        self.ai_player.see_refutation("Colonel Mustard")
        self.ai_player.see_refutation("Knife")
        self.ai_player.see_refutation("Candlestick")

        # Make another suggestion
        suggestion2 = self.ai_player.choose_suggestion(self.game, "Hall")

        # The suggestion should not include items we've marked as impossible
        self.assertNotIn(suggestion2[0], ["Miss Scarlet", "Colonel Mustard"])
        self.assertNotIn(suggestion2[1], ["Knife", "Candlestick"])

    def test_handle_suggestion_sets_flags(self):
        """Test that handle_suggestion sets the right flags"""
        # Make a suggestion
        self.ai_player.handle_suggestion(self.game, "Hall")

        # The AI should be set to exit the room next turn
        self.assertTrue(self.ai_player.must_exit_next_turn)

        # The last suggestion room should be set
        self.assertEqual(self.ai_player.last_suggestion_room, "Hall")

    def test_avoid_duplicate_suggestions(self):
        """Test that AI avoids making duplicate suggestions"""
        # Make an initial suggestion
        suggestion1 = self.ai_player.choose_suggestion(self.game, "Hall")

        # Record this suggestion
        self.ai_player.previous_suggestions.add((suggestion1[0], suggestion1[1], "Hall"))

        # We should still have plenty of options
        remaining_combinations = (len(self.ai_player.possible_suspects) *
                                  len(self.ai_player.possible_weapons) - 1)

        # If we have enough combinations left, we should get a different suggestion
        if remaining_combinations > 0:
            # Make another suggestion in the same room
            suggestion2 = self.ai_player.choose_suggestion(self.game, "Hall")

            # Record this suggestion
            self.ai_player.previous_suggestions.add((suggestion2[0], suggestion2[1], "Hall"))

            # The suggestions should be different
            self.assertNotEqual((suggestion1[0], suggestion1[1]),
                                (suggestion2[0], suggestion2[1]))

    def test_exit_room_after_suggestion(self):
        """Test that AI leaves room after making a suggestion"""
        # Set up the flag from a suggestion
        self.ai_player.must_exit_next_turn = True

        # Set current position to be in a room
        self.ai_player.character.position = "Hall"

        # Create mock available moves - a mix of hallway and room moves
        hallway_moves = [(1, 2), (3, 4)]
        room_moves = ["Study", "Lounge"]
        available_moves = hallway_moves + room_moves

        # Make a move
        move = self.ai_player.make_move(self.game, available_moves, 5)

        # The move should be a hallway move, not a room
        self.assertIn(move, hallway_moves)

        # The flag should be reset
        self.assertFalse(self.ai_player.must_exit_next_turn)


if __name__ == "__main__":
    unittest.main()