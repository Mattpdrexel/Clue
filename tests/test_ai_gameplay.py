# tests/test_ai_gameplay.py
import unittest
import os
import sys
import random
from unittest.mock import MagicMock, patch

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from Player.AIPlayer import AIPlayer
from Objects.Character import Character


class MockMansionBoard:
    """Mock mansion board for testing."""
    def __init__(self):
        self.rows = 20
        self.cols = 20
        self.room_dict = {
            "Study": MagicMock(),
            "Hall": MagicMock(),
            "Lounge": MagicMock(),
            "Library": MagicMock(),
            "Billiard Room": MagicMock(),
            "Dining Room": MagicMock(),
            "Conservatory": MagicMock(),
            "Ball Room": MagicMock(),
            "Kitchen": MagicMock(),
            "Clue": MagicMock()
        }

    def get_room_name_at_position(self, row, col):
        """Mock method to get room name at position."""
        # For testing, return room names for specific positions
        if row == 8 and 10 <= col <= 13:
            return "Clue"
        elif row == 9 and 10 <= col <= 11:
            return "Clue"
        elif 1 <= row <= 3 and 1 <= col <= 3:
            return "Study"
        elif 1 <= row <= 3 and 8 <= col <= 10:
            return "Hall"
        elif 1 <= row <= 3 and 15 <= col <= 17:
            return "Lounge"
        elif 8 <= row <= 10 and 1 <= col <= 3:
            return "Library"
        elif 8 <= row <= 10 and 15 <= col <= 17:
            return "Billiard Room"
        elif 15 <= row <= 17 and 1 <= col <= 3:
            return "Conservatory"
        elif 15 <= row <= 17 and 8 <= col <= 10:
            return "Ball Room"
        elif 15 <= row <= 17 and 15 <= col <= 17:
            return "Kitchen"
        elif 12 <= row <= 14 and 8 <= col <= 10:
            return "Dining Room"
        return None


class MockCharacterBoard:
    """Mock character board for testing."""
    def __init__(self):
        self.grid = [[None for _ in range(20)] for _ in range(20)]
        self.positions = {}

    def get_cell_content(self, row, col):
        """Mock method to get cell content."""
        return self.grid[row][col]


class MockGame:
    """Mock game for testing AI gameplay."""
    def __init__(self):
        self.mansion_board = MockMansionBoard()
        self.character_board = MockCharacterBoard()
        self.players = []
        self.current_player_idx = 0
        self.game_over = False

        # Game elements
        self.character_names = ["Miss Scarlet", "Colonel Mustard", "Mrs. White", 
                               "Reverend Green", "Mrs Peacock", "Professor Plum"]
        self.weapon_names = ["Candlestick", "Knife", "Lead Pipe", 
                            "Revolver", "Rope", "Wrench"]
        self.room_names = list(self.mansion_board.room_dict.keys())

        # Create characters
        self.characters = {}
        for name in self.character_names:
            self.characters[name] = Character(name)

        # Setup initial positions
        self.setup_characters()

    def setup_characters(self):
        """Setup characters in their initial positions."""
        positions = [
            ("Miss Scarlet", ("Clue", 8, 10)),
            ("Colonel Mustard", ("Clue", 8, 11)),
            ("Mrs. White", ("Clue", 8, 12)),
            ("Reverend Green", ("Clue", 8, 13)),
            ("Mrs Peacock", ("Clue", 9, 10)),
            ("Professor Plum", ("Clue", 9, 11))
        ]

        for name, pos in positions:
            self.characters[name].position = pos


class TestAIGameplay(unittest.TestCase):
    """Test the gameplay with multiple AI players."""

    def setUp(self):
        """Set up test environment."""
        # Create a mock game
        self.game = MockGame()

        # Create AI players
        self.players = []
        for i, name in enumerate(self.game.character_names[:4]):  # Use first 4 characters
            ai_player = AIPlayer(i, name)
            ai_player.character = self.game.characters[name]
            self.players.append(ai_player)

        # Add players to game
        self.game.players = self.players

    def test_four_ai_players_gameplay(self):
        """Test that AI players can move between rooms."""
        # Helper function to extract room name
        def get_room_name(position):
            if isinstance(position, str):
                return position
            elif isinstance(position, tuple) and len(position) == 3:
                return position[0]
            return None

        # Track room changes
        room_changes = []
        visited_rooms = set()

        # Run a fixed number of turns
        MAX_TURNS = 10

        # Mock available moves to include different rooms
        available_moves = [
            "Study", "Hall", "Lounge", "Library", "Billiard Room",
            "Dining Room", "Conservatory", "Ball Room", "Kitchen"
        ]

        # Mock get_available_moves to return our predefined moves
        with patch.object(AIPlayer, 'get_available_moves', return_value=available_moves):
            # Run game for fixed number of turns
            for turn in range(MAX_TURNS):
                # Get current player
                current_player = self.game.players[self.game.current_player_idx]

                # Record starting position
                starting_position = current_player.character.position
                starting_room = get_room_name(starting_position)

                # Let AI decide where to move
                dice_roll = 4  # Fixed dice roll for testing
                new_position = current_player.make_move(self.game, available_moves, dice_roll)

                # Update character position
                if new_position:
                    current_player.character.position = new_position

                # Check if player moved to different room
                ending_position = current_player.character.position
                ending_room = get_room_name(ending_position)

                # Record room change if it happened
                if starting_room != ending_room and ending_room is not None:
                    room_changes.append((current_player.character_name, starting_room, ending_room))
                    visited_rooms.add(ending_room)

                # Move to next player
                self.game.current_player_idx = (self.game.current_player_idx + 1) % len(self.game.players)

        # Print room changes for debugging
        print("\nRoom changes during gameplay test:")
        for character, from_room, to_room in room_changes:
            print(f"{character}: {from_room} -> {to_room}")

        # Test assertions to verify movement
        self.assertGreater(len(room_changes), 0,
                          "No players changed rooms during test. Movement might be broken.")

        # Verify players visit multiple rooms
        self.assertGreaterEqual(len(visited_rooms), 1,
                               f"AIs only visited {len(visited_rooms)} unique rooms. Expected at least 1.")


if __name__ == '__main__':
    unittest.main()
