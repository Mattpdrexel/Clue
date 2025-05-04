# tests/test_smarter_ai_player.py
import unittest
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from Player.SmarterAIPlayer import SmarterAIPlayer


class MockCharacter:
    def __init__(self, name):
        self.name = name
        self.position = "Hall"


class MockGame:
    def __init__(self):
        self.players = []
        self.character_names = ["Miss Scarlet", "Colonel Mustard", "Mrs. White",
                                "Reverend Green", "Mrs Peacock", "Professor Plum"]
        self.weapon_names = ["Candlestick", "Lead Pipe", "Wrench",
                             "Knife", "Revolver", "Rope"]
        self.room_names = ["Study", "Hall", "Lounge", "Dining Room", "Kitchen",
                           "Ball Room", "Conservatory", "Billiard Room", "Library", "Clue"]
        self.solution = ("Miss Scarlet", "Knife", "Hall")


class TestSmarterAIPlayer(unittest.TestCase):

    def setUp(self):
        # Create the AI player
        self.ai_player = SmarterAIPlayer(0, "Colonel Mustard")
        self.ai_player.character = MockCharacter("Colonel Mustard")

        # Create mock game
        self.game = MockGame()
        self.game.players = [self.ai_player]

        # Initialize KB
        self.ai_player.initialize_knowledge_base(self.game)

        # Add some cards to player's hand
        self.ai_player.add_card(("suspect", "Colonel Mustard"))
        self.ai_player.add_card(("weapon", "Rope"))
        self.ai_player.add_card(("room", "Study"))

    def test_room_selection_strategy(self):
        """Test that AI prefers rooms it hasn't visited recently."""
        # Set up previous rooms history
        self.ai_player.previous_rooms = ["Kitchen", "Lounge"]

        # Create available moves with both visited and unvisited rooms
        available_moves = ["Kitchen", "Lounge", "Study", "Hall"]

        # Make move decision
        chosen_move = self.ai_player._choose_best_room(available_moves)

        # Should prefer rooms that haven't been visited recently
        self.assertIn(chosen_move, ["Study", "Hall"])
        self.assertNotIn(chosen_move, ["Kitchen", "Lounge"])

    def test_knowledge_update_from_suggestion(self):
        """Test that suggestion updates knowledge correctly."""
        # Initial knowledge state - all cards possible in envelope
        self.assertEqual(len(self.ai_player.kb.envelope_suspects), 5)  # All except Colonel Mustard
        self.assertEqual(len(self.ai_player.kb.envelope_weapons), 5)  # All except Rope
        self.assertEqual(len(self.ai_player.kb.envelope_rooms), 9)  # All except Study

        # Simulate a suggestion and response
        # Player suggests Miss Scarlet with Knife in Hall, player 1 shows Miss Scarlet
        self.ai_player.update_knowledge_from_suggestion(
            0,  # Suggesting player ID
            ("Hall", "Miss Scarlet", "Knife"),  # Suggestion (room, suspect, weapon)
            1,  # Responding player ID
            ("suspect", "Miss Scarlet")  # Revealed card
        )

        # Miss Scarlet should no longer be in envelope candidates
        self.assertNotIn("Miss Scarlet", self.ai_player.kb.envelope_suspects)

        # Other cards unchanged
        self.assertEqual(len(self.ai_player.kb.envelope_weapons), 5)
        self.assertEqual(len(self.ai_player.kb.envelope_rooms), 9)

    def test_suggestion_strategy(self):
        """Test that suggestion strategy prioritizes envelope candidates."""
        # Set envelope to have few candidates
        self.ai_player.kb.envelope_suspects = {"Miss Scarlet", "Mrs Peacock"}
        self.ai_player.kb.envelope_weapons = {"Knife", "Candlestick"}

        # Make suggestion
        suggestion = self.ai_player.choose_suggestion(self.game, "Hall")

        # Should suggest from envelope candidates
        self.assertIn(suggestion[0], {"Miss Scarlet", "Mrs Peacock"})
        self.assertIn(suggestion[1], {"Knife", "Candlestick"})

        # Should avoid repeating previous suggestions
        first_suggestion = suggestion
        self.ai_player.previous_suggestions.add((first_suggestion[0], first_suggestion[1], "Hall"))

        # Make another suggestion in same room
        second_suggestion = self.ai_player.choose_suggestion(self.game, "Hall")

        # Should be different from first suggestion
        self.assertNotEqual(
            (first_suggestion[0], first_suggestion[1]),
            (second_suggestion[0], second_suggestion[1])
        )

    def test_accusation_logic(self):
        """Test that AI makes accusation when appropriate."""
        # Initially shouldn't make accusation due to uncertainty
        self.assertFalse(self.ai_player.should_make_accusation(self.game))

        # Simulate being in Clue room
        self.ai_player.character.position = "Clue"

        # Still shouldn't accuse since we don't know solution
        self.assertFalse(self.ai_player.should_make_accusation(self.game))

        # Narrow down to single solution
        self.ai_player.kb.envelope_suspects = {"Miss Scarlet"}
        self.ai_player.kb.envelope_weapons = {"Knife"}
        self.ai_player.kb.envelope_rooms = {"Hall"}

        # Propagate knowledge to mark solution as known
        self.ai_player.kb._propagate()

        # Now should make accusation since in Clue room and solution known
        self.assertTrue(self.ai_player.should_make_accusation(self.game))

        # Move out of Clue room
        self.ai_player.character.position = "Hall"

        # Shouldn't accuse when not in Clue room
        self.assertFalse(self.ai_player.should_make_accusation(self.game))

    def test_patience_mechanism(self):
        """Test that AI gets impatient after many turns without progress."""
        # Set initial knowledge state
        self.ai_player.last_knowledge_state = (5, 5, 9)  # (suspects, weapons, rooms)
        self.ai_player.no_progress_turns = 0

        # Simulate many turns with no knowledge progress
        for _ in range(self.ai_player.patience_threshold + 1):
            # Make a move but knowledge doesn't change
            self.ai_player.make_move(self.game, ["Hall", "Study"], 5)

        # AI should be impatient now
        self.assertTrue(self.ai_player.no_progress_turns >= self.ai_player.patience_threshold)

        # If in Clue room, should try accusation
        self.ai_player.character.position = "Clue"
        self.assertTrue(self.ai_player.should_make_accusation(self.game))

        # Simulate learning new information
        self.ai_player.kb.envelope_suspects = {"Miss Scarlet", "Professor Plum"}  # Removed some suspects

        # Make another move after knowledge changes
        self.ai_player.make_move(self.game, ["Hall", "Study"], 5)

        # Should reset patience counter
        self.assertEqual(self.ai_player.no_progress_turns, 0)


if __name__ == "__main__":
    unittest.main()