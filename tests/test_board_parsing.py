# /tests/test_board_parsing.py
import unittest
import pandas as pd
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
print(project_root)

from Objects.Board import MansionBoard


class TestBoardParsing(unittest.TestCase):
    def setUp(self):
        # Create a simple test board layout
        # In a real implementation, you would load the actual board layout
        # For this test, we'll create a mock DataFrame
        excel_path = os.path.join(project_root, "Data", "mansion_board_layout.xlsx")
        self.board_data = pd.read_excel(excel_path, header=None)
        self.mansion_board = MansionBoard(self.board_data)


    def test_board_dimensions(self):
        """Test that the board has the correct dimensions (22 x 23)"""
        self.assertEqual(self.mansion_board.rows, 22)
        self.assertEqual(self.mansion_board.cols, 23)

    def test_study_room_cells(self):
        """Test that the Study room cells are correctly identified (0,0 to 3,6)"""
        study_cells = self.mansion_board.get_room_cells("Study")

        # Check if all expected cells are present
        expected_cells = [(r, c) for r in range(0, 4) for c in range(0, 7)]
        for cell in expected_cells:
            self.assertIn(cell, study_cells, f"Cell {cell} should be in Study room")

        # Check that there are no extra cells
        self.assertEqual(len(study_cells), len(expected_cells))

    def test_room_entrances(self):
        """Test that all room entrances are correctly identified"""
        # Define expected entrances for each room
        expected_entrances = {
            "Study": [(1, 6), (2, 6)],
            "Library": [(5, 2), (5, 3)],
            "Billiard Room": [(11, 1), (11, 2)],
            "Conservatory": [(17, 1), (17, 2)],
            "Hall": [(5, 10), (5, 11)],
            "Ball Room": [(16, 11), (16, 12)],
            "Dining Room": [(10, 16), (11, 16)],
            "Kitchen": [(17, 20), (17, 21)],
            "Lounge": [(2, 16), (3, 16)],
            "Clue": [(8, 11), (8, 12), (10, 10), (11, 10), (10, 13), (11, 13), (13, 11), (13, 12)]
        }

        # Check each room's entrances
        for room_name, entrances in expected_entrances.items():
            actual_entrances = self.mansion_board.get_room_entrances(room_name)

            # Sort both lists to ensure consistent comparison
            expected_sorted = sorted(entrances)
            actual_sorted = sorted(actual_entrances)

            self.assertEqual(
                actual_sorted,
                expected_sorted,
                f"Room entrances for {room_name} do not match. Expected: {expected_sorted}, Got: {actual_sorted}"
            )

    def test_secret_passages(self):
        """Test that secret passages are correctly configured"""
        # Check secret passage from Study to Kitchen
        study_room = self.mansion_board.get_room("Study")
        self.assertIn("Kitchen", study_room.secret_passage_to)

        # Check secret passage from Kitchen to Study
        kitchen_room = self.mansion_board.get_room("Kitchen")
        self.assertIn("Study", kitchen_room.secret_passage_to)

        # Check secret passage from Lounge to Conservatory
        lounge_room = self.mansion_board.get_room("Lounge")
        self.assertIn("Conservatory", lounge_room.secret_passage_to)

        # Check secret passage from Conservatory to Lounge
        conservatory_room = self.mansion_board.get_room("Conservatory")
        self.assertIn("Lounge", conservatory_room.secret_passage_to)


if __name__ == "__main__":
    unittest.main()