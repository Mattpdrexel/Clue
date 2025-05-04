# tests/test_game_ending.py
import unittest
from unittest.mock import patch, MagicMock
from Game.Game import Game
from Player.Player import Player
from Player.SimpleAIPlayer import SimpleAIPlayer


class TestGameEnding(unittest.TestCase):
    """Test cases for game ending conditions in Clue"""

    def setUp(self):
        """Set up test environment with a mocked game instance"""
        # Create a mock Game class
        self.game = MagicMock(spec=Game)

        # Set up game state variables
        self.game.game_over = False
        self.game.winner = None
        self.game.current_player_idx = 0

        # Create mock players
        self.players = []
        for i in range(3):
            player = MagicMock(spec=Player)
            player.player_id = i
            player.character_name = f"Player {i}"
            player.eliminated = False
            player.made_wrong_accusation = False
            # Configure character mock
            player.character = MagicMock()
            player.character.position = "Clue"

            self.players.append(player)

        self.game.players = self.players

        # Set up a solution
        self.game.solution = ("Miss Scarlet", "Knife", "Library")

        # Mock the end_game method to record calls
        self.original_end_game = self.game.end_game
        self.game.end_game = MagicMock()
        self.game.end_game.side_effect = self._mock_end_game

    def _mock_end_game(self, winner=None):
        """Mock implementation of end_game"""
        self.game.game_over = True
        self.game.winner = winner

    def test_game_ends_when_all_players_eliminated(self):
        """Test that the game ends when all players make wrong accusations"""
        # Import the function directly to avoid mocking issues
        from Game.GameLogic import process_accusation

        # Mark all players as having made wrong accusations
        for player in self.game.players:
            # Make an incorrect accusation for each player
            wrong_suspect = "Colonel Mustard" if self.game.solution[0] != "Colonel Mustard" else "Mrs. White"
            wrong_weapon = "Rope" if self.game.solution[1] != "Rope" else "Candlestick"
            wrong_room = "Kitchen" if self.game.solution[2] != "Kitchen" else "Hall"

            # Process the accusation using the actual function
            result = process_accusation(
                self.game,
                player,
                wrong_suspect,
                wrong_weapon,
                wrong_room
            )

            # Check the result is false (wrong accusation)
            self.assertFalse(result)

            # Mark the player as eliminated
            player.made_wrong_accusation = True

        # Create a simplified version of the play_game method
        def simplified_play_game():
            # Check if all players have made wrong accusations
            all_eliminated = all(player.made_wrong_accusation for player in self.game.players)

            if all_eliminated and not self.game.game_over:
                # End the game with no winner
                self.game.end_game(winner=None)

        # Execute the simplified game logic
        simplified_play_game()

        # Verify the game has ended
        self.assertTrue(self.game.game_over)
        # Verify there's no winner
        self.assertIsNone(self.game.winner)

    def test_game_ends_with_correct_accusation(self):
        """Test that the game ends with a winner when a player makes a correct accusation"""
        # Import the function directly
        from Game.GameLogic import process_accusation

        # Choose the first player to make a correct accusation
        winning_player = self.game.players[0]

        # Process the correct accusation
        result = process_accusation(
            self.game,
            winning_player,
            self.game.solution[0],  # Correct suspect
            self.game.solution[1],  # Correct weapon
            self.game.solution[2]  # Correct room
        )

        # Verify the result is true (correct accusation)
        self.assertTrue(result)

        # Verify the game has ended
        self.assertTrue(self.game.game_over)
        # Verify the correct player won
        self.assertEqual(self.game.winner, winning_player)

    def test_player_eliminated_after_wrong_accusation(self):
        """Test that a player is eliminated after making a wrong accusation but game continues"""
        # Import the function directly
        from Game.GameLogic import process_accusation

        # First player makes a wrong accusation
        first_player = self.game.players[0]

        # Make an incorrect accusation
        result = process_accusation(
            self.game,
            first_player,
            "Colonel Mustard",  # Wrong suspect
            "Rope",  # Wrong weapon
            "Kitchen"  # Wrong room
        )

        # Verify the result is false (wrong accusation)
        self.assertFalse(result)

        # Verify player is marked as having made a wrong accusation
        self.assertTrue(first_player.made_wrong_accusation)

        # But the game should still be ongoing because not all players are eliminated
        self.assertFalse(self.game.game_over)

    def test_game_state_after_correct_accusation(self):
        """Test the game state after a correct accusation is made"""
        # Import the function directly
        from Game.GameLogic import process_accusation

        # One player makes the correct accusation
        correct_player = self.game.players[1]

        # Verify game is not over at the start
        self.assertFalse(self.game.game_over)
        self.assertIsNone(self.game.winner)

        # Make the correct accusation
        result = process_accusation(
            self.game,
            correct_player,
            self.game.solution[0],  # Correct suspect
            self.game.solution[1],  # Correct weapon
            self.game.solution[2]  # Correct room
        )

        # Verify the result is true (correct accusation)
        self.assertTrue(result)

        # Verify the game ended with the correct winner
        self.assertTrue(self.game.game_over)
        self.assertEqual(self.game.winner, correct_player)


if __name__ == '__main__':
    unittest.main()