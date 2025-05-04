import unittest
import os
import pandas as pd
from Objects.Board import MansionBoard, CharacterBoard
from Actions.Movement import get_pathfinding_distance

# Find the project root directory
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestPathfindingDistance(unittest.TestCase):
    def setUp(self):
        # Load the game board
        excel_path = os.path.join(project_root, "Data", "mansion_board_layout.xlsx")
        board_data = pd.read_excel(excel_path, header=None)
        self.mansion_board = MansionBoard(board_data)

        # Create character board
        self.character_board = CharacterBoard(self.mansion_board.rows, self.mansion_board.cols)

    def test_distances_from_clue_room(self):
        """Test that distances from Clue room to nearby rooms are correct"""
        # Test distances from Clue to nearby rooms - all should be exactly 3
        nearby_rooms = [
            ("Clue", "Hall", 3),
            ("Clue", "Dining Room", 3),
            ("Clue", "Ball Room", 3)
        ]

        for source, target, expected in nearby_rooms:
            distance = get_pathfinding_distance(source, target, self.mansion_board)
            self.assertEqual(distance, expected,
                             f"Distance from {source} to {target} should be exactly {expected}, got {distance}")

    def test_clue_to_all_rooms(self):
        """Test distances from Clue to all rooms on the board"""
        # Expected distances from Clue to all rooms
        expected_distances = {
            "Clue": 0,  # Same room
            "Hall": 3,
            "Dining Room": 3,
            "Ball Room": 3,
            "Study": 11,  # Hall -> Study
            "Lounge": 9,  # Hall -> Lounge
        }

        # Test each room
        for room, expected in expected_distances.items():
            distance = get_pathfinding_distance("Clue", room, self.mansion_board)
            self.assertEqual(distance, expected,
                             f"Distance from Clue to {room} should be {expected}, got {distance}")

    def test_blocked_paths(self):
        """Test that blocked paths increase distances"""
        # First get baseline distance
        baseline = get_pathfinding_distance("Clue", "Hall", self.mansion_board)
        self.assertEqual(baseline, 3, "Baseline distance from Clue to Hall should be 3")

        # Now block all hallway cells between Clue and Hall
        # Typical exits from Clue toward Hall
        blockages = [(7, 11), (7, 12), (6, 11), (6, 12)]

        # Place blockers
        char_board = CharacterBoard(self.mansion_board.rows, self.mansion_board.cols)
        for i, pos in enumerate(blockages):
            char_board.place(f"Blocker{i}", pos[0], pos[1])

        # Measure distance with blockers
        blocked_distance = get_pathfinding_distance("Clue", "Hall", self.mansion_board, char_board)

        # Either distance should increase or path becomes impossible
        self.assertGreaterEqual(blocked_distance, baseline,
                                "Blocked path should increase distance")


if __name__ == '__main__':
    unittest.main()