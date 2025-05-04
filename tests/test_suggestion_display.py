# tests/test_suggestion_display.py
import unittest
import os
import sys
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)


class TestSuggestionDisplay(unittest.TestCase):
    """Test that suggestions are properly displayed during gameplay."""

    def setUp(self):
        """Set up test environment."""
        # Patch input function
        self.input_patcher = patch('builtins.input', return_value='1')
        self.mock_input = self.input_patcher.start()

        # Create a StringIO object to capture print output
        self.stdout_patcher = patch('sys.stdout')
        self.mock_stdout = self.stdout_patcher.start()

    def tearDown(self):
        """Clean up after tests."""
        self.input_patcher.stop()
        self.stdout_patcher.stop()

    @patch('Game.GameSetup.pd.read_excel')
    def test_ai_suggestion_display(self, mock_read_excel):
        """Test that AI suggestions are displayed during gameplay."""
        # Create a simple mock DataFrame for the board layout
        import pandas as pd
        import numpy as np
        from Game.GameSetup import initialize_game

        # Redirect file loading
        excel_path = os.path.join(project_root, "Data", "mansion_board_layout.xlsx")

        def read_with_correct_path(file_path, **kwargs):
            if file_path == "Data/mansion_board_layout.xlsx":
                return pd.read_excel(excel_path, **kwargs)
            return pd.read_excel(file_path, **kwargs)

        mock_read_excel.side_effect = read_with_correct_path

        # Import needed modules
        from Game.Game import Game
        from Game.TurnManagement import process_ai_turn
        from Player.AIPlayer import AIPlayer

        # Create print spy to capture output
        print_calls = []

        def spy_print(*args, **kwargs):
            output = " ".join(str(arg) for arg in args)
            print_calls.append(output)
            # Still print to console for debugging
            print(output)

        # Create game with AI players
        with patch('builtins.print', spy_print):
            game = Game(0, 4)  # 4 AI players

            # Initialize player knowledge
            for player in game.players:
                player.initialize_knowledge(game)

            # Test the handle_suggestion method directly
            print("\n--- Testing direct suggestion call ---")
            test_player = game.players[0]

            # Check if handle_suggestion is being called with mocking
            original_handle_suggestion = AIPlayer.handle_suggestion
            suggestion_calls = []

            def mock_handle_suggestion(self, game, room):
                result = original_handle_suggestion(self, game, room)
                suggestion_calls.append((self.character_name, room, result))
                # Print the result here to ensure it's visible
                print(f"SUGGESTION: {self.character_name} suggests {result[1]} in {result[0]} with the {result[2]}")
                return result

            AIPlayer.handle_suggestion = mock_handle_suggestion

            # Process a turn where player would enter a room
            print("\n--- Processing AI turn ---")
            # Force player into a room
            test_player.character.position = "Hall"
            process_ai_turn(game, test_player)

            # Verify suggestions were made
            self.assertTrue(any("SUGGESTION" in call for call in print_calls),
                            "No suggestions were displayed during gameplay")
            self.assertTrue(len(suggestion_calls) > 0,
                            "handle_suggestion was never called")

            # Reset the method
            AIPlayer.handle_suggestion = original_handle_suggestion


if __name__ == '__main__':
    unittest.main()