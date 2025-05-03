# /tests/test_player_knowledge.py
import unittest
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from Player.Player import Player
from Objects.Character import Character


class TestPlayerKnowledge(unittest.TestCase):
    def setUp(self):
        # Create a test player
        self.player = Player(1, "Miss Scarlet")

        # Test data
        self.suspect_card = ("suspect", "Colonel Mustard")
        self.weapon_card = ("weapon", "Knife")
        self.room_card = ("room", "Kitchen")

    def test_initial_knowledge_state(self):
        """Test that a new player has correct initial knowledge"""
        # All cards should be possible solutions initially
        self.assertEqual(len(self.player.possible_suspects), 6)  # Assuming 6 suspects
        self.assertEqual(len(self.player.possible_weapons), 6)  # Assuming 6 weapons
        self.assertEqual(len(self.player.possible_rooms), 9)  # Assuming 9 rooms

        # No cards should be confirmed as not in the solution yet
        self.assertEqual(len(self.player.confirmed_not_suspects), 0)
        self.assertEqual(len(self.player.confirmed_not_weapons), 0)
        self.assertEqual(len(self.player.confirmed_not_rooms), 0)

    def test_add_card_updates_knowledge(self):
        """Test that adding a card to hand updates player knowledge"""
        # Add a suspect card
        self.player.add_card(self.suspect_card)

        # The card should be in hand
        self.assertIn(self.suspect_card, self.player.hand)

        # The suspect should be removed from possible solutions
        self.assertNotIn(self.suspect_card[1], self.player.possible_suspects)

        # The suspect should be added to confirmed not in solution
        self.assertIn(self.suspect_card[1], self.player.confirmed_not_suspects)

        # Add a weapon card
        self.player.add_card(self.weapon_card)

        # The weapon should be removed from possible solutions
        self.assertNotIn(self.weapon_card[1], self.player.possible_weapons)

        # Add a room card
        self.player.add_card(self.room_card)

        # The room should be removed from possible solutions
        self.assertNotIn(self.room_card[1], self.player.possible_rooms)

    def test_suggestion_history_tracking(self):
        """Test that suggestions are properly tracked in history"""
        # Make a suggestion
        room, suspect, weapon = "Hall", "Mrs. White", "Rope"
        self.player.make_suggestion(room, suspect, weapon)

        # Check that the suggestion was added to history
        self.assertEqual(len(self.player.suggestion_history), 1)
        self.assertEqual(self.player.suggestion_history[0]["room"], room)
        self.assertEqual(self.player.suggestion_history[0]["suspect"], suspect)
        self.assertEqual(self.player.suggestion_history[0]["weapon"], weapon)
        self.assertIsNone(self.player.suggestion_history[0]["disproven_by"])
        self.assertIsNone(self.player.suggestion_history[0]["disproven_with"])

    def test_update_knowledge_own_suggestion_disproven(self):
        """Test updating knowledge when your own suggestion is disproven"""
        # Make a suggestion first
        room, suspect, weapon = "Hall", "Mrs. White", "Rope"
        self.player.make_suggestion(room, suspect, weapon)

        # Update knowledge with response - player 2 shows us the Hall card
        revealed_card = ("room", "Hall")
        self.player.update_knowledge_from_suggestion(
            suggesting_player=1,  # self
            suggestion=(room, suspect, weapon),
            responding_player=2,
            revealed_card=revealed_card
        )

        # The suggestion history should be updated
        self.assertEqual(self.player.suggestion_history[0]["disproven_by"], 2)
        self.assertEqual(self.player.suggestion_history[0]["disproven_with"], revealed_card)

        # Our knowledge should be updated - Hall can't be part of the solution
        self.assertNotIn("Hall", self.player.possible_rooms)
        self.assertIn("Hall", self.player.confirmed_not_rooms)

    def test_update_knowledge_own_suggestion_not_disproven(self):
        """Test updating knowledge when your suggestion isn't disproven by anyone"""
        # Make a suggestion first
        room, suspect, weapon = "Hall", "Mrs. White", "Rope"
        self.player.make_suggestion(room, suspect, weapon)

        # Update knowledge with no response (no player could disprove)
        self.player.update_knowledge_from_suggestion(
            suggesting_player=1,  # self
            suggestion=(room, suspect, weapon),
            responding_player=None,
            revealed_card=None
        )

        # The suggestion history should be updated
        self.assertEqual(self.player.suggestion_history[0]["disproven_by"], None)

        # Knowledge remains the same - but this is valuable information
        # (In a more advanced player, we might mark these as likely in the solution)
        self.assertIn("Hall", self.player.possible_rooms)
        self.assertIn("Mrs. White", self.player.possible_suspects)
        self.assertIn("Rope", self.player.possible_weapons)

    def test_update_knowledge_other_player_cant_disprove(self):
        """Test updating knowledge when another player can't disprove a suggestion"""
        # Player 2 makes a suggestion and player 3 can't disprove it
        room, suspect, weapon = "Hall", "Mrs. White", "Rope"

        self.player.update_knowledge_from_suggestion(
            suggesting_player=2,  # another player
            suggestion=(room, suspect, weapon),
            responding_player=3,  # not self
            revealed_card=None  # couldn't disprove
        )

        # We should have learned that player 3 doesn't have any of these cards
        self.assertIn(3, self.player.player_knowledge)
        self.assertIn(("room", "Hall"), self.player.player_knowledge[3]["not_cards"])
        self.assertIn(("suspect", "Mrs. White"), self.player.player_knowledge[3]["not_cards"])
        self.assertIn(("weapon", "Rope"), self.player.player_knowledge[3]["not_cards"])

    def test_respond_to_suggestion(self):
        """Test responding to another player's suggestion"""
        # Add cards to hand
        self.player.add_card(self.suspect_card)  # ("suspect", "Colonel Mustard")
        self.player.add_card(self.weapon_card)  # ("weapon", "Knife")
        self.player.add_card(self.room_card)  # ("room", "Kitchen")

        # Test responding when we have one matching card
        response = self.player.respond_to_suggestion(
            ("Library", "Colonel Mustard", "Candlestick")
        )
        self.assertEqual(response, self.suspect_card)

        # Test responding when we have multiple matching cards (should return first match)
        response = self.player.respond_to_suggestion(
            ("Kitchen", "Colonel Mustard", "Knife")
        )
        # Base player returns first match, which depends on the order added
        self.assertIn(response, [self.suspect_card, self.weapon_card, self.room_card])

        # Test responding when we have no matching cards
        response = self.player.respond_to_suggestion(
            ("Library", "Mrs. White", "Candlestick")
        )
        self.assertIsNone(response)

    def test_get_solution_candidates(self):
        """Test getting the current solution candidates"""
        # Initially all cards are candidates
        candidates = self.player.get_solution_candidates()
        self.assertEqual(len(candidates["suspects"]), 6)  # Assuming 6 suspects
        self.assertEqual(len(candidates["weapons"]), 6)  # Assuming 6 weapons
        self.assertEqual(len(candidates["rooms"]), 9)  # Assuming 9 rooms

        # Add some cards to hand to eliminate them as candidates
        self.player.add_card(self.suspect_card)  # ("suspect", "Colonel Mustard")
        self.player.add_card(self.weapon_card)  # ("weapon", "Knife")

        # Now get candidates again
        candidates = self.player.get_solution_candidates()

        # These cards should be eliminated
        self.assertNotIn(self.suspect_card[1], candidates["suspects"])
        self.assertNotIn(self.weapon_card[1], candidates["weapons"])

        # But other cards should remain
        self.assertEqual(len(candidates["suspects"]), 5)  # 6-1=5
        self.assertEqual(len(candidates["weapons"]), 5)  # 6-1=5
        self.assertEqual(len(candidates["rooms"]), 9)  # Still 9



if __name__ == "__main__":
    unittest.main()