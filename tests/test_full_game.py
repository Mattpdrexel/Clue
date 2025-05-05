# tests/test_full_game.py
import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import io
import pandas as pd

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Import necessary modules
from Objects.Board import MansionBoard, CharacterBoard


class TestFullGameExecution(unittest.TestCase):
    """Test that the game runs to completion via main.py"""

    def setUp(self):
        """Set up a test environment with proper board initialization"""
        # Load the board data explicitly with the absolute path to avoid file not found errors
        self.excel_path = os.path.join(project_root, "Data", "mansion_board_layout.xlsx")
        self.board_data = pd.read_excel(self.excel_path, header=None)

        # Create the necessary mock objects
        self.mock_game = MagicMock()
        self.mock_game.game_over = False
        self.mock_game.players = [MagicMock(), MagicMock(), MagicMock()]
        self.mock_game.current_player_idx = 0
        self.mock_game.current_round = 0

        # Create the mansion board
        self.mansion_board = MansionBoard(self.board_data)
        self.mock_game.mansion_board = self.mansion_board

        # Create character board
        self.character_board = CharacterBoard(self.mansion_board.rows, self.mansion_board.cols)
        self.mock_game.character_board = self.character_board

        # Set up the players
        for i, player in enumerate(self.mock_game.players):
            player.character_name = f"Character {i + 1}"
            player.eliminated = False
            player.knowledge = {}

    @patch('builtins.print')  # Suppress print output during the test
    def test_game_completes(self, mock_print):
        """Test that play_game_auto runs to completion without errors"""
        # Import play_game_auto only after the board is loaded properly
        from main import play_game_auto

        # Create a counter to limit the loop execution
        call_counter = [0]

        # Mock the process_ai_turn function to set game_over to True after a few turns
        def side_effect(game, player):
            call_counter[0] += 1
            if call_counter[0] >= 5:  # After 5 turns, end the game
                game.game_over = True
                game.winner = game.players[0]

        # Apply patches
        with patch('Game.TurnManagement.process_ai_turn', side_effect=side_effect):
            # Mock the visualization renderer
            with patch('Visualization.BoardRenderer.BoardRenderer') as mock_renderer:
                mock_renderer_instance = mock_renderer.return_value
                mock_renderer_instance.save_board_frame = MagicMock()
                mock_renderer_instance.create_game_animation = MagicMock()

                # Mock ScoreSheet
                with patch('Knowledge.ScoreSheet.ScoreSheet') as mock_scoresheet:
                    mock_scoresheet_instance = mock_scoresheet.return_value
                    mock_scoresheet_instance.render_text = MagicMock(return_value="Mock Scoresheet")
                    mock_scoresheet_instance.save_to_file = MagicMock()

                    # Mock os.makedirs to avoid creating directories
                    with patch('os.makedirs'):
                        # Call the function we're testing
                        play_game_auto(self.mock_game)

        # Check that the game completed
        self.assertTrue(self.mock_game.game_over)
        self.assertEqual(self.mock_game.winner, self.mock_game.players[0])

        # Ensure that process_ai_turn was called at least once
        self.assertGreaterEqual(call_counter[0], 1)


class TestMainExecution(unittest.TestCase):
    """Test that main function runs correctly with proper board loading"""

    @patch('builtins.input', side_effect=["0", "3"])  # 0 humans, 3 AI
    @patch('main.play_game_auto')  # Mock the play_game_auto function
    def test_main_execution(self, mock_play_game_auto, mock_input):
        """Test that the main function runs and calls play_game_auto for all-AI games"""
        # Patch pandas.read_excel to use the absolute path
        excel_path = os.path.join(project_root, "Data", "mansion_board_layout.xlsx")
        original_read_excel = pd.read_excel

        def mock_read_excel(path, **kwargs):
            if path == "Data/mansion_board_layout.xlsx":
                return original_read_excel(excel_path, **kwargs)
            return original_read_excel(path, **kwargs)

        # Redirect stdout to capture prints
        captured_output = io.StringIO()
        sys.stdout = captured_output

        try:
            # First patch the pandas excel reading
            with patch('pandas.read_excel', side_effect=mock_read_excel):
                # Then patch the board initialization in GameSetup
                with patch('Game.GameSetup.initialize_game') as mock_init_game:
                    # Create required mock objects
                    mock_mansion = MagicMock()
                    mock_character = MagicMock()
                    mock_characters = MagicMock()
                    mock_weapons = MagicMock()

                    # Setup the return value for initialize_game
                    mock_init_game.return_value = (mock_mansion, mock_character, mock_characters, mock_weapons)

                    # Mock print_game_state
                    with patch('Game.GameSetup.print_game_state'):
                        # Import the main function here to avoid early execution
                        from main import main
                        # Run the main function
                        main()
        finally:
            # Reset stdout
            sys.stdout = sys.__stdout__

        # Check that play_game_auto was called exactly once
        mock_play_game_auto.assert_called_once()

        # Verify output contains expected messages
        output = captured_output.getvalue()
        self.assertIn("Welcome to Clue", output)
        self.assertIn("Starting game with 0 human players and 3 AI players", output)


if __name__ == '__main__':
    unittest.main()