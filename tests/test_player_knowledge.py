# tests/test_player_knowledge.py
import unittest
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from Player.Player import Player
from Knowledge.PlayerKnowledge import PlayerKnowledge


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


class TestPlayerKnowledge(unittest.TestCase):
    def setUp(self):
        """Set up the test environment"""
        # Create a mock game
        self.game = MockGame()

        # Create a test player
        self.player = Player(player_id=1, character_name="Miss Scarlet")

        # Initialize knowledge
        self.player.initialize_knowledge(self.game)

        # Test cards
        self.suspect_card = ("suspect", "Colonel Mustard")
        self.weapon_card = ("weapon", "Knife")
        self.room_card = ("room", "Kitchen")

    def test_initialize_knowledge(self):
        """Test that knowledge is initialized correctly"""
        # Check that knowledge exists
        self.assertIsNotNone(self.player.knowledge)

        # Check knowledge system is properly initialized
        self.assertEqual(self.player.knowledge.player_id, 1)
        self.assertEqual(len(self.player.knowledge.possible_solution["suspects"]), 6)
        self.assertEqual(len(self.player.knowledge.possible_solution["weapons"]), 6)
        self.assertEqual(len(self.player.knowledge.possible_solution["rooms"]), 10)

    def test_add_card_updates_knowledge(self):
        """Test that adding a card properly updates knowledge"""
        # Add a card to player's hand
        self.player.add_card(self.suspect_card)

        # Check that card is in player's hand
        self.assertIn(self.suspect_card, self.player.hand)

        # Check that card is removed from possible solution
        self.assertNotIn(self.suspect_card[1], self.player.knowledge.possible_solution["suspects"])

        # Check that card is recorded as known to player
        self.assertIn(self.suspect_card[1], self.player.knowledge.my_cards)
        self.assertIn(self.suspect_card[1], self.player.knowledge.player_cards[1])

    def test_making_and_responding_to_suggestion(self):
        """Test making a suggestion and responding to suggestions"""
        # Make a suggestion
        room, suspect, weapon = "Hall", "Mrs. White", "Rope"
        result = self.player.make_suggestion(room, suspect, weapon)

        # Verify suggestion format
        self.assertEqual(result, (room, suspect, weapon))

        # Add cards to hand for responding to suggestions
        self.player.add_card(self.suspect_card)  # Colonel Mustard
        self.player.add_card(self.weapon_card)  # Knife

        # Test responding when we have one matching card
        response = self.player.respond_to_suggestion(
            ("Library", "Colonel Mustard", "Candlestick")
        )
        self.assertEqual(response, self.suspect_card)

        # Test responding when we have no matching cards
        response = self.player.respond_to_suggestion(
            ("Library", "Mrs. White", "Candlestick")
        )
        self.assertIsNone(response)

    def test_updating_knowledge_from_suggestion(self):
        """Test updating knowledge based on suggestions and responses"""
        # Case 1: We made a suggestion and a card was shown to us
        suggestion = ("Hall", "Mrs. White", "Rope")
        revealed_card = ("suspect", "Mrs. White")

        self.player.update_knowledge_from_suggestion(
            suggesting_player=1,  # self
            suggestion=suggestion,
            responding_player=2,
            revealed_card=revealed_card
        )

        # Check that knowledge is updated - Mrs. White cannot be in the solution
        self.assertNotIn("Mrs. White", self.player.knowledge.possible_solution["suspects"])

        # Case 2: Another player made a suggestion that no one could disprove
        suggestion = ("Library", "Professor Plum", "Candlestick")

        self.player.update_knowledge_from_suggestion(
            suggesting_player=0,
            suggestion=suggestion,
            responding_player=None,
            revealed_card=None
        )

        # These might all be in the solution
        # Let's check that each player's 'not_cards' list includes these cards
        for player_id in self.player.knowledge.player_not_cards:
            self.assertIn("Library", self.player.knowledge.player_not_cards[player_id])
            self.assertIn("Professor Plum", self.player.knowledge.player_not_cards[player_id])
            self.assertIn("Candlestick", self.player.knowledge.player_not_cards[player_id])

    def test_updating_knowledge_from_accusation(self):
        """Test updating knowledge based on accusations"""
        # Case 1: Correct accusation
        accusation = ("Hall", "Mrs. White", "Rope")

        self.player.update_knowledge_from_accusation(
            accusing_player=0,
            accusation=accusation,
            is_correct=True
        )

        # Check that knowledge is updated to reflect the correct solution
        self.assertEqual(len(self.player.knowledge.possible_solution["rooms"]), 1)
        self.assertEqual(len(self.player.knowledge.possible_solution["suspects"]), 1)
        self.assertEqual(len(self.player.knowledge.possible_solution["weapons"]), 1)

        self.assertIn("Hall", self.player.knowledge.possible_solution["rooms"])
        self.assertIn("Mrs. White", self.player.knowledge.possible_solution["suspects"])
        self.assertIn("Rope", self.player.knowledge.possible_solution["weapons"])

        # Case 2: Incorrect accusation
        # Reset player for new test
        self.setUp()

        accusation = ("Library", "Professor Plum", "Candlestick")

        self.player.update_knowledge_from_accusation(
            accusing_player=0,
            accusation=accusation,
            is_correct=False
        )

        # For now, our basic implementation doesn't make deductions from incorrect accusations
        # But we could check that the event was recorded if that's implemented

    def test_get_solution_candidates(self):
        """Test getting the current solution candidates"""
        # Add cards to hand to eliminate them as candidates
        self.player.add_card(self.suspect_card)  # Colonel Mustard
        self.player.add_card(self.weapon_card)  # Knife

        # Get solution candidates
        candidates = self.player.get_solution_candidates()

        # Check that we get the correct types back
        self.assertIn("suspects", candidates)
        self.assertIn("weapons", candidates)
        self.assertIn("rooms", candidates)

        # Check that added cards are eliminated from candidates
        self.assertNotIn("Colonel Mustard", candidates["suspects"])
        self.assertNotIn("Knife", candidates["weapons"])

        # Others should still be present
        self.assertIn("Mrs. White", candidates["suspects"])
        self.assertIn("Rope", candidates["weapons"])

    def test_elimination(self):
        """Test player elimination"""
        # Initially player is not eliminated
        self.assertFalse(self.player.eliminated)
        self.assertFalse(self.player.made_wrong_accusation)

        # Eliminate player
        self.player.eliminate()

        # Check player is now eliminated
        self.assertTrue(self.player.eliminated)
        self.assertTrue(self.player.made_wrong_accusation)


if __name__ == "__main__":
    unittest.main()