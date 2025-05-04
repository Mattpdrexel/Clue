# tests/test_complete_game.py
import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import random
import pandas as pd

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from Game.Game import Game
from Game.GameLogic import process_suggestion, process_accusation
from Game.TurnManagement import get_room_from_position


class TestCompleteGame(unittest.TestCase):
    """Test a complete game of Clue with predefined outcomes"""

    def setUp(self):
        """Set up a complete game with mocked randomness"""
        # Fix the project root path for pandas to find the Excel file
        self.excel_file_path = os.path.join(project_root, "Data", "mansion_board_layout.xlsx")
        self.original_read_excel = pd.read_excel

        # Patch pandas.read_excel to use the absolute path
        def mock_read_excel(path, **kwargs):
            if path == "Data/mansion_board_layout.xlsx":
                return self.original_read_excel(self.excel_file_path, **kwargs)
            return self.original_read_excel(path, **kwargs)

        self.excel_patcher = patch('pandas.read_excel', side_effect=mock_read_excel)
        self.excel_patcher.start()

        # Predefined dice rolls for players
        self.dice_rolls = [4, 6, 3, 5, 2, 4, 6, 5, 3]
        self.dice_roll_iter = iter(self.dice_rolls)

        # Patch random.randint to return our predefined dice rolls
        self.randint_patcher = patch('random.randint', side_effect=lambda min_val, max_val: next(self.dice_roll_iter))
        self.randint_patcher.start()

        # Patch random.choice and random.shuffle to be deterministic
        self.choice_patcher = patch('random.choice', side_effect=lambda seq: seq[0])
        self.choice_patcher.start()

        self.shuffle_patcher = patch('random.shuffle')  # This makes shuffle do nothing
        self.shuffle_patcher.start()

        # Mock user inputs for choices during the game
        self.input_responses = [
            # Player 1, 2, 3 character selection
            "1", "2", "3",

            # Player 1 first turn
            "1",  # Move to Hall
            "y",  # Make suggestion
            "1",  # Miss Scarlet
            "1",  # Candlestick
            "n",  # No accusation

            # Player 2 first turn
            "2",  # Move to Library
            "y",  # Make suggestion
            "2",  # Colonel Mustard
            "2",  # Lead Pipe
            "n",  # No accusation

            # Player 3 first turn
            "1",  # Move to Study
            "y",  # Make suggestion
            "3",  # Mrs. White
            "3",  # Wrench
            "n",  # No accusation

            # Player 1 second turn - accusation
            "3",  # Move to Clue room
            "y",  # Make accusation
            "4",  # Reverend Green
            "4",  # Knife
            "4",  # Dining Room
        ]
        self.input_iter = iter(self.input_responses)

        self.input_patcher = patch('builtins.input', side_effect=lambda prompt: next(self.input_iter))
        self.input_patcher.start()

        # Create the game with 3 human players
        self.game = Game(num_human_players=3, num_ai_players=0)

        # Force a specific solution
        self.game.solution = ("Reverend Green", "Knife", "Dining Room")

        # Give players specific cards for testing
        self.distribute_test_cards()

    def distribute_test_cards(self):
        """Override the random card dealing with a predetermined set"""
        # Clear existing cards
        for player in self.game.players:
            player.hand = []

        # Player 1 gets these cards
        self.game.players[0].add_card(("suspect", "Miss Scarlet"))
        self.game.players[0].add_card(("weapon", "Candlestick"))
        self.game.players[0].add_card(("room", "Hall"))

        # Player 2 gets these cards
        self.game.players[1].add_card(("suspect", "Colonel Mustard"))
        self.game.players[1].add_card(("weapon", "Lead Pipe"))
        self.game.players[1].add_card(("room", "Library"))

        # Player 3 gets these cards
        self.game.players[2].add_card(("suspect", "Mrs. White"))
        self.game.players[2].add_card(("weapon", "Wrench"))
        self.game.players[2].add_card(("room", "Study"))

    def tearDown(self):
        """Clean up patches"""
        self.excel_patcher.stop()
        self.randint_patcher.stop()
        self.choice_patcher.stop()
        self.shuffle_patcher.stop()
        self.input_patcher.stop()

    @patch('builtins.print')  # Suppress print output during the test
    def test_complete_game(self, mock_print):
        """Test a complete game with controlled inputs"""
        # Manually simulate the game turns to avoid the complex logic
        # in TurnManagement.py which is hard to patch completely

        # Player 1's turn
        player1 = self.game.players[0]
        # Move to Hall
        player1.character.move_to("Hall")
        # Make suggestion: Miss Scarlet with Candlestick in Hall
        process_suggestion(self.game, player1, "Miss Scarlet", "Candlestick", "Hall")

        # Player 2's turn
        player2 = self.game.players[1]
        # Move to Library
        player2.character.move_to("Library")
        # Make suggestion: Colonel Mustard with Lead Pipe in Library
        process_suggestion(self.game, player2, "Colonel Mustard", "Lead Pipe", "Library")

        # Player 3's turn
        player3 = self.game.players[2]
        # Move to Study
        player3.character.move_to("Study")
        # Make suggestion: Mrs. White with Wrench in Study
        process_suggestion(self.game, player3, "Mrs. White", "Wrench", "Study")

        # Back to Player 1 for second turn
        # Move to Clue room
        player1.character.move_to("Clue")
        # Make correct accusation: Reverend Green with Knife in Dining Room
        result = process_accusation(self.game, player1, "Reverend Green", "Knife", "Dining Room")

        # Now the game should be over with Player 1 as the winner
        self.assertTrue(result)
        self.assertTrue(self.game.game_over)
        self.assertEqual(self.game.winner, player1)


if __name__ == '__main__':
    unittest.main()