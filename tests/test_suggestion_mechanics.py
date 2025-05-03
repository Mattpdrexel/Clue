# /tests/test_suggestion_mechanics.py
import unittest
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from Player.Player import Player
from Objects.Character import Character


class TestSuggestionMechanics(unittest.TestCase):
    def setUp(self):
        # Create players for testing
        self.player1 = Player(1, "Miss Scarlet")

        self.player2 = Player(2, "Colonel Mustard")

        self.player3 = Player(3, "Mrs. White")

        # Give players some cards
        self.player1.add_card(("suspect", "Professor Plum"))
        self.player1.add_card(("weapon", "Knife"))
        self.player1.add_card(("room", "Hall"))

        self.player2.add_card(("suspect", "Mrs. Peacock"))
        self.player2.add_card(("weapon", "Rope"))
        self.player2.add_card(("room", "Study"))

        self.player3.add_card(("suspect", "Miss Scarlet"))
        self.player3.add_card(("weapon", "Candlestick"))
        self.player3.add_card(("room", "Library"))

    def test_make_suggestion(self):
        """Test making a suggestion with location constraints"""
        # First, move the player to the correct room
        self.player1.character.move_to("Kitchen")

        # Player 1 makes a suggestion
        suggestion = self.player1.make_suggestion("Kitchen", "Colonel Mustard", "Revolver")

        # Check that suggestion returns the expected tuple
        self.assertEqual(suggestion, ("Kitchen", "Colonel Mustard", "Revolver"))

        # Check it was recorded in history
        self.assertEqual(len(self.player1.suggestion_history), 1)
        self.assertEqual(self.player1.suggestion_history[0]["room"], "Kitchen")
        self.assertEqual(self.player1.suggestion_history[0]["suspect"], "Colonel Mustard")
        self.assertEqual(self.player1.suggestion_history[0]["weapon"], "Revolver")

        # Test that player can't suggest about a room they're not in
        self.player1.character.move_to("Library")
        with self.assertRaises(ValueError):
            self.player1.make_suggestion("Kitchen", "Colonel Mustard", "Revolver")

        # Test the helper method
        self.player1.character.move_to("Hall")
        self.assertTrue(self.player1.can_make_suggestion("Hall"))
        self.assertFalse(self.player1.can_make_suggestion("Kitchen"))

    def test_respond_to_suggestion_with_matching_card(self):
        """Test responding to a suggestion with a matching card"""
        # Player 1 has Hall card and should show it
        response = self.player1.respond_to_suggestion(("Hall", "Mrs. White", "Revolver"))
        self.assertEqual(response, ("room", "Hall"))

        # Player 1 has Knife card and should show it
        response = self.player1.respond_to_suggestion(("Kitchen", "Mrs. White", "Knife"))
        self.assertEqual(response, ("weapon", "Knife"))

        # Player 1 has Professor Plum card and should show it
        response = self.player1.respond_to_suggestion(("Kitchen", "Professor Plum", "Revolver"))
        self.assertEqual(response, ("suspect", "Professor Plum"))

    def test_respond_to_suggestion_with_multiple_matching_cards(self):
        """Test responding when player has multiple matching cards"""
        # Player 1 has both Hall and Knife cards
        response = self.player1.respond_to_suggestion(("Hall", "Mrs. White", "Knife"))

        # Base Player implementation returns first match
        # (This test may need adjustment if your player implementation prioritizes differently)
        self.assertIn(response, [("room", "Hall"), ("weapon", "Knife")])

    def test_respond_to_suggestion_with_no_matching_card(self):
        """Test responding when player has no matching cards"""
        response = self.player1.respond_to_suggestion(("Kitchen", "Mrs. White", "Revolver"))
        self.assertIsNone(response)

    def test_full_suggestion_round(self):
        """Test a full round of suggestion mechanics with multiple players"""
        # Player 1 makes a suggestion
        suggestion = self.player1.make_suggestion("Library", "Mrs. Peacock", "Rope")

        # Player 2 responds and shows a card (has Mrs. Peacock)
        response_p2 = self.player2.respond_to_suggestion(suggestion)
        self.assertEqual(response_p2, ("suspect", "Mrs. Peacock"))

        # Player 1 updates knowledge based on card shown by Player 2
        self.player1.update_knowledge_from_suggestion(
            suggesting_player=1,
            suggestion=suggestion,
            responding_player=2,
            revealed_card=response_p2
        )

        # Check that Player 1's suggestion history is updated
        self.assertEqual(self.player1.suggestion_history[0]["disproven_by"], 2)
        self.assertEqual(self.player1.suggestion_history[0]["disproven_with"], ("suspect", "Mrs. Peacock"))

        # Check that Player 1's knowledge is updated
        self.assertNotIn("Mrs. Peacock", self.player1.possible_suspects)
        self.assertIn("Mrs. Peacock", self.player1.confirmed_not_suspects)

    def test_suggestion_not_disproven(self):
        """Test when no player can disprove a suggestion"""
        # Give Player 3 the Mrs. White card
        self.player3.add_card(("suspect", "Mrs. White"))

        # Player 1 makes a suggestion
        suggestion = self.player1.make_suggestion("Kitchen", "Mrs. White", "Revolver")

        # Player 2 responds (can't disprove)
        response_p2 = self.player2.respond_to_suggestion(suggestion)
        self.assertIsNone(response_p2)

        # Player 3 responds (can disprove with Mrs. White card)
        response_p3 = self.player3.respond_to_suggestion(suggestion)
        self.assertEqual(response_p3, ("suspect", "Mrs. White"))

        # Player 1 updates knowledge (Player 2 couldn't disprove)
        self.player1.update_knowledge_from_suggestion(
            suggesting_player=1,
            suggestion=suggestion,
            responding_player=2,
            revealed_card=None
        )

        # Check Player 1's knowledge about Player 2
        self.assertIn(2, self.player1.player_knowledge)
        self.assertIn(("room", "Kitchen"), self.player1.player_knowledge[2]["not_cards"])
        self.assertIn(("suspect", "Mrs. White"), self.player1.player_knowledge[2]["not_cards"])
        self.assertIn(("weapon", "Revolver"), self.player1.player_knowledge[2]["not_cards"])

        # Player 1 updates knowledge (Player 3 showed Mrs. White)
        self.player1.update_knowledge_from_suggestion(
            suggesting_player=1,
            suggestion=suggestion,
            responding_player=3,
            revealed_card=response_p3
        )

        # Check Player 1's updated knowledge
        self.assertNotIn("Mrs. White", self.player1.possible_suspects)
        self.assertIn("Mrs. White", self.player1.confirmed_not_suspects)

    def test_observing_other_players(self):
        """Test that a player learns from observing suggestions between other players"""
        # Player 2 makes a suggestion and Player 3 responds
        suggestion = ("Kitchen", "Mrs. White", "Rope")

        # Player 1 observes that Player 3 couldn't disprove
        self.player1.update_knowledge_from_suggestion(
            suggesting_player=2,
            suggestion=suggestion,
            responding_player=3,
            revealed_card=None
        )

        # Check that Player 1 learned Player 3 doesn't have these cards
        self.assertIn(3, self.player1.player_knowledge)
        self.assertIn(("room", "Kitchen"), self.player1.player_knowledge[3]["not_cards"])
        self.assertIn(("weapon", "Rope"), self.player1.player_knowledge[3]["not_cards"])

        # But Player 3 actually has Mrs. White, so the observation is incomplete
        # In a real game, Player 1 wouldn't know if Player 3 showed a card or which one

    def test_accusation_mechanics(self):
        """Test making an accusation"""
        # Player makes an accusation
        accusation = self.player1.make_accusation("Kitchen", "Mrs. White", "Revolver")

        # Basic accusation just returns the tuple
        self.assertEqual(accusation, ("Kitchen", "Mrs. White", "Revolver"))

        # Accusation doesn't get added to suggestion history
        self.assertEqual(len(self.player1.suggestion_history), 0)

    def test_knowledge_tracking_after_multiple_suggestions(self):
        """Test that knowledge tracking works correctly over multiple suggestion rounds"""
        # First suggestion round
        self.player1.make_suggestion("Library", "Mrs. Peacock", "Rope")
        self.player1.update_knowledge_from_suggestion(
            suggesting_player=1,
            suggestion=("Library", "Mrs. Peacock", "Rope"),
            responding_player=2,
            revealed_card=("suspect", "Mrs. Peacock")
        )

        # Second suggestion round
        self.player1.make_suggestion("Hall", "Colonel Mustard", "Knife")
        self.player1.update_knowledge_from_suggestion(
            suggesting_player=1,
            suggestion=("Hall", "Colonel Mustard", "Knife"),
            responding_player=None,
            revealed_card=None
        )

        # Third suggestion round
        self.player1.make_suggestion("Study", "Professor Plum", "Revolver")
        self.player1.update_knowledge_from_suggestion(
            suggesting_player=1,
            suggestion=("Study", "Professor Plum", "Revolver"),
            responding_player=3,
            revealed_card=("room", "Study")
        )

        # Check suggestion history
        self.assertEqual(len(self.player1.suggestion_history), 3)

        # Check knowledge has been updated correctly
        self.assertNotIn("Mrs. Peacock", self.player1.possible_suspects)
        self.assertNotIn("Study", self.player1.possible_rooms)

        # Both these cards were revealed, so shouldn't be considered for solution
        self.assertIn("Mrs. Peacock", self.player1.confirmed_not_suspects)
        self.assertIn("Study", self.player1.confirmed_not_rooms)


if __name__ == "__main__":
    unittest.main()