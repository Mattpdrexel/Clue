# tests/test_movement.py
import unittest
import pandas as pd
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from Objects.Board import MansionBoard, CharacterBoard
from Objects.Character import Character
from Player.Player import Player
from Actions.Movement import is_legal_move


class TestMovement(unittest.TestCase):
    def setUp(self):
        # Load the game board
        excel_path = os.path.join(project_root, "Data", "mansion_board_layout.xlsx")
        board_data = pd.read_excel(excel_path, header=None)
        self.mansion_board = MansionBoard(board_data)

        # Create character board
        self.character_board = CharacterBoard(self.mansion_board.rows, self.mansion_board.cols)

        # Create a test character and player
        self.test_player = Player(1, "Miss Scarlet")
        self.test_character = self.test_player.character

    def test_clue_room_exits(self):
        """Test that all expected exits from the Clue room are valid with die roll of 1"""
        # Place character in the Clue room
        self.test_character.move_to("Clue")

        # Expected exit points from the Clue room with roll of 1
        expected_exits = [(7, 11), (7, 12), (10, 9), (11, 9),
                          (14, 11), (14, 12), (10, 14), (11, 14)]

        # Get available moves with a die roll of 1
        available_moves = self.test_player.get_available_moves(
            self.mansion_board, self.character_board, 1)

        # Check that all expected exits are in available moves
        for exit_pos in expected_exits:
            self.assertIn(exit_pos, available_moves,
                          f"Exit position {exit_pos} should be available from Clue room with roll of 1")

    def test_nearby_rooms_from_clue_with_roll_3(self):
        """Test that nearby rooms are reachable from Clue room with die roll of 3"""
        # Place character in the Clue room
        self.test_character.move_to("Clue")

        # Get available moves with a die roll of 3
        available_moves = self.test_player.get_available_moves(
            self.mansion_board, self.character_board, 3)

        # Check that nearby rooms are in available moves
        expected_rooms = ["Hall", "Dining Room", "Ball Room"]

        for room in expected_rooms:
            self.assertIn(room, available_moves,
                          f"{room} should be reachable from Clue room with roll of 3")

    def test_secret_passage(self):
        """Test that secret passages work correctly"""
        # Place character in the Study (which has a secret passage to Kitchen)
        self.test_character.move_to("Study")

        # Get available moves with any die roll (secret passages don't require movement)
        available_moves = self.test_player.get_available_moves(
            self.mansion_board, self.character_board, 1)

        # Check that Kitchen is in available moves via secret passage
        self.assertIn("Kitchen", available_moves,
                      "Kitchen should be reachable from Study via secret passage")

    def test_legal_move_from_room_to_hallway(self):
        """Test that is_legal_move correctly validates moves from room to hallway"""
        # Get a room entrance from the Clue room
        clue_entrances = self.mansion_board.get_room_entrances("Clue")
        entrance = clue_entrances[0]  # Take the first entrance

        # Get an adjacent hallway cell to this entrance
        entrance_row, entrance_col = entrance
        hallway_cell = None

        # Try all four directions to find an adjacent hallway cell
        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            new_row, new_col = entrance_row + dr, entrance_col + dc
            if (self.mansion_board.get_cell_type(new_row, new_col) == "hallway" and
                    self.mansion_board.get_room_name_at_position(new_row, new_col) is None):
                hallway_cell = (new_row, new_col)
                break

        # Make sure we found an adjacent hallway cell
        self.assertIsNotNone(hallway_cell, "Could not find hallway cell adjacent to Clue room entrance")

        # Test is_legal_move for this move
        is_legal = is_legal_move(
            self.mansion_board, self.character_board, entrance, hallway_cell)

        self.assertTrue(is_legal, f"Move from {entrance} to {hallway_cell} should be legal")

    def test_one_step_exits_from_clue(self):
        """Test that the specific one-step exits from Clue room are available"""
        # Place character in the Clue room
        self.test_character.move_to("Clue")

        # Expected one-step exits based on your specification
        expected_exits = [(7, 11), (7, 12), (10, 9), (11, 9),
                          (14, 11), (14, 12), (10, 14), (11, 14)]

        # Get available moves with roll of 1
        available_moves = self.test_player.get_available_moves(
            self.mansion_board, self.character_board, 1)

        # Check that all expected exits are in available moves
        for exit_pos in expected_exits:
            self.assertIn(exit_pos, available_moves,
                          f"Exit position {exit_pos} should be available from Clue room with roll of 1")

    def test_character_blocking_movement(self):
        """Test that characters block pathways and prevent movement through them"""
        # Place our test character in the Clue room
        self.test_character.move_to("Clue")

        # Create a blocking character and place it at (6, 11) - which is a path to Hall
        blocking_character = Character("Blocking Character")
        self.character_board.place("Blocking Character", 6, 11)

        # Get available moves with a die roll of 3
        available_moves = self.test_player.get_available_moves(
            self.mansion_board, self.character_board, 3)

        # Test that Hall is NOT reachable with the blocking character in place
        self.assertNotIn("Hall", available_moves,
                         "Hall should NOT be reachable from Clue room with roll of 3 when path is blocked")

        # Now remove the blocking character
        self.character_board.grid[6][11] = None

        # Get available moves again with a die roll of 3
        available_moves = self.test_player.get_available_moves(
            self.mansion_board, self.character_board, 3)

        # Verify that Hall is now reachable
        self.assertIn("Hall", available_moves,
                      "Hall should be reachable from Clue room with roll of 3 when path is clear")

    def test_room_representation_in_moves(self):
        """Test that rooms are represented by their names, not coordinates"""
        # Place character in the Study
        self.test_character.move_to("Study")

        # Get available moves
        available_moves = self.test_player.get_available_moves(
            self.mansion_board, self.character_board, 3)

        # Check that rooms are represented by names
        for move in available_moves:
            if isinstance(move, str):
                self.assertTrue(move in self.mansion_board.room_dict.keys(),
                                f"String move {move} should be a valid room name")

        # Check that "Study" is in the moves (can stay in current room)
        self.assertIn("Study", available_moves,
                      "Current room 'Study' should be in available moves")


if __name__ == "__main__":
    unittest.main()