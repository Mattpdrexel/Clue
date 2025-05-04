# tests/test_knowledge_base.py
import unittest
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from Knowledge.KnowledgeBase import KnowledgeBase


class MockGame:
    def __init__(self):
        self.players = [MockPlayer(0), MockPlayer(1), MockPlayer(2)]


class MockPlayer:
    def __init__(self, player_id):
        self.player_id = player_id


class TestKnowledgeBase(unittest.TestCase):

    def setUp(self):
        # Create a mock game
        self.game = MockGame()

        # Create knowledge base for player 0
        self.kb = KnowledgeBase(self.game, 0)

    def test_initialization(self):
        """Test that KB initializes correctly"""
        # Check that all cards are possible in all positions
        self.assertEqual(len(self.kb.envelope_suspects), 6)
        self.assertEqual(len(self.kb.envelope_weapons), 6)
        self.assertEqual(len(self.kb.envelope_rooms), 10)

        # Check holders
        self.assertEqual(self.kb.holders, {0, 1, 2, "ENVELOPE"})

    def test_initialize_with_hand(self):
        """Test initialization with player's hand"""
        # Initialize with some cards
        hand = [
            ("suspect", "Miss Scarlet"),
            ("weapon", "Knife"),
            ("room", "Hall")
        ]

        self.kb.initialize_with_hand(hand)

        # Check that these cards are marked as held by player 0
        self.assertEqual(self.kb.possible_holders("Miss Scarlet"), {0})
        self.assertEqual(self.kb.possible_holders("Knife"), {0})
        self.assertEqual(self.kb.possible_holders("Hall"), {0})

        # These cards should be removed from envelope candidates
        self.assertNotIn("Miss Scarlet", self.kb.envelope_suspects)
        self.assertNotIn("Knife", self.kb.envelope_weapons)
        self.assertNotIn("Hall", self.kb.envelope_rooms)

    def test_eliminate(self):
        """Test eliminating possibilities"""
        # Initially all cards could be with all holders
        self.assertTrue("ENVELOPE" in self.kb.possible_holders("Miss Scarlet"))

        # Eliminate possibility
        self.kb.eliminate("Miss Scarlet", "ENVELOPE")

        # Check that it's removed
        self.assertFalse("ENVELOPE" in self.kb.possible_holders("Miss Scarlet"))

    def test_set_holder(self):
        """Test setting a definite holder"""
        # Set a holder
        self.kb.set_holder("Miss Scarlet", 1)

        # Should be the only possibility
        self.assertEqual(self.kb.possible_holders("Miss Scarlet"), {1})

        # Should be removed from envelope candidates
        self.assertNotIn("Miss Scarlet", self.kb.envelope_suspects)

    def test_suggestion_update_case_a(self):
        """Test updating from suggestion - Case A (card shown)"""
        # Player 0 suggests, Player 1 shows Miss Scarlet
        self.kb.update_from_suggestion(0, ("Miss Scarlet", "Knife", "Hall"), 1, "Miss Scarlet")

        # Miss Scarlet should be with Player 1
        self.assertEqual(self.kb.possible_holders("Miss Scarlet"), {1})

        # Should be removed from envelope candidates
        self.assertNotIn("Miss Scarlet", self.kb.envelope_suspects)

    def test_suggestion_update_case_b(self):
        """Test updating from suggestion - Case B (player responded but card unknown)"""
        # Initialize with known cards
        self.kb.set_holder("Colonel Mustard", 0)  # Player 0 has Colonel Mustard

        # Player 0 suggests, Player 2 responds (skipping Player 1)
        self.kb.update_from_suggestion(0, ("Miss Scarlet", "Knife", "Hall"), 2, None)

        # Player 1 shouldn't have any of these cards
        self.assertFalse(1 in self.kb.possible_holders("Miss Scarlet"))
        self.assertFalse(1 in self.kb.possible_holders("Knife"))
        self.assertFalse(1 in self.kb.possible_holders("Hall"))

    def test_suggestion_update_case_c(self):
        """Test updating from suggestion - Case C (no one responded)"""
        # Player 0 suggests, no one responds
        self.kb.update_from_suggestion(0, ("Miss Scarlet", "Knife", "Hall"), None, None)

        # All three cards should be in the envelope
        self.assertEqual(self.kb.possible_holders("Miss Scarlet"), {"ENVELOPE"})
        self.assertEqual(self.kb.possible_holders("Knife"), {"ENVELOPE"})
        self.assertEqual(self.kb.possible_holders("Hall"), {"ENVELOPE"})

        # Should be the only envelope candidates
        self.assertEqual(self.kb.envelope_suspects, {"Miss Scarlet"})
        self.assertEqual(self.kb.envelope_weapons, {"Knife"})
        self.assertEqual(self.kb.envelope_rooms, {"Hall"})

        # Solution should be known
        self.assertTrue(self.kb.is_solution_known())
        self.assertEqual(self.kb.get_solution(), ("Miss Scarlet", "Knife", "Hall"))

    def test_solution_discovery(self):
        """Test discovering the solution through elimination"""
        # Eliminate all but one suspect
        for suspect in self.kb.envelope_suspects:
            if suspect != "Miss Scarlet":
                self.kb.eliminate(suspect, "ENVELOPE")

        # Eliminate all but one weapon
        for weapon in self.kb.envelope_weapons:
            if weapon != "Knife":
                self.kb.eliminate(weapon, "ENVELOPE")

        # Eliminate all but one room
        for room in self.kb.envelope_rooms:
            if room != "Hall":
                self.kb.eliminate(room, "ENVELOPE")

        # Solution should be known
        self.assertTrue(self.kb.is_solution_known())
        self.assertEqual(self.kb.get_solution(), ("Miss Scarlet", "Knife", "Hall"))

    def test_cards_possibly_with(self):
        """Test getting cards possibly with a holder"""
        # Initially all cards could be with all holders
        all_cards = self.kb.cards_possibly_with(1)
        self.assertEqual(len(all_cards), 6 + 6 + 10)  # All suspects, weapons, rooms

        # Eliminate some possibilities
        self.kb.eliminate("Miss Scarlet", 1)
        self.kb.eliminate("Knife", 1)

        # Should have two fewer cards
        updated_cards = self.kb.cards_possibly_with(1)
        self.assertEqual(len(updated_cards), 6 + 6 + 10 - 2)
        self.assertNotIn("Miss Scarlet", updated_cards)
        self.assertNotIn("Knife", updated_cards)

    def test_envelope_candidates(self):
        """Test getting envelope candidates"""
        # Initialize with some cards in player's hand
        hand = [
            ("suspect", "Miss Scarlet"),
            ("weapon", "Knife"),
            ("room", "Hall")
        ]

        self.kb.initialize_with_hand(hand)

        # Get envelope candidates
        candidates = self.kb.envelope_candidates()

        # Cards in hand should be excluded
        self.assertNotIn("Miss Scarlet", candidates["suspects"])
        self.assertNotIn("Knife", candidates["weapons"])
        self.assertNotIn("Hall", candidates["rooms"])

        # Other cards should still be included
        self.assertIn("Colonel Mustard", candidates["suspects"])
        self.assertIn("Rope", candidates["weapons"])
        self.assertIn("Study", candidates["rooms"])


if __name__ == "__main__":
    unittest.main()