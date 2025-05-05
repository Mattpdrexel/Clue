# tests/test_ai_game_statistics.py
import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import pandas as pd
import numpy as np
import time
import matplotlib.pyplot as plt
from collections import Counter, defaultdict

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Import necessary classes
from Objects.Board import MansionBoard, CharacterBoard
from Game.Game import Game


class AIGameStatisticsTest(unittest.TestCase):
    """Run multiple AI-only games and collect statistics on outcomes."""

    def setUp(self):
        """Set up test environment with Excel path"""
        self.excel_path = os.path.join(project_root, "Data", "mansion_board_layout.xlsx")
        self.stats_dir = os.path.join(project_root, "Output", "stats")
        os.makedirs(self.stats_dir, exist_ok=True)

        # Set the seed for reproducibility
        np.random.seed(42)

    @patch('builtins.print')  # Suppress print output during tests
    def run_ai_game_with_stats(self, num_ai_players=3, mock_print=None):
        """Run a single AI game and return statistics"""
        # Patch pandas.read_excel to use the absolute path
        original_read_excel = pd.read_excel

        def mock_read_excel(path, **kwargs):
            if path == "Data/mansion_board_layout.xlsx":
                return original_read_excel(self.excel_path, **kwargs)
            return original_read_excel(path, **kwargs)

        # Disable print for BoardRenderer during tests to reduce noise
        renderer_patcher = patch('Visualization.BoardRenderer.BoardRenderer')
        mock_renderer = renderer_patcher.start()
        mock_renderer_instance = mock_renderer.return_value
        mock_renderer_instance.save_board_frame = MagicMock()
        mock_renderer_instance.create_game_animation = MagicMock()

        # Disable ScoreSheet file creation
        scoresheet_patcher = patch('Knowledge.ScoreSheet.ScoreSheet')
        mock_scoresheet = scoresheet_patcher.start()
        mock_scoresheet_instance = mock_scoresheet.return_value
        mock_scoresheet_instance.save_to_file = MagicMock()
        mock_scoresheet_instance.render_text = MagicMock(return_value="Mock Scoresheet")

        excel_patcher = patch('pandas.read_excel', side_effect=mock_read_excel)
        excel_patcher.start()

        # Record game stats
        game_stats = {}

        try:
            # Create a game with specified number of AI players
            game = Game(num_human_players=0, num_ai_players=num_ai_players)

            # Run the auto game loop but collect statistics
            from main import play_game_auto

            # Start timer to measure game duration
            start_time = time.time()

            # Run the game
            play_game_auto(game)

            # Record the end time
            end_time = time.time()

            # Collect game statistics
            game_stats = {
                'total_players': len(game.players),
                'winner': game.winner.character_name if game.winner else None,
                'game_over': game.game_over,
                'total_rounds': getattr(game, 'current_round', 0),
                'eliminated_players': sum(1 for p in game.players if p.eliminated),
                'duration_seconds': end_time - start_time,
                'has_winner': game.winner is not None,
                'player_statuses': {
                    p.character_name: 'Winner' if game.winner == p else 'Eliminated' if p.eliminated else 'Active'
                    for p in game.players
                }
            }

        finally:
            # Stop all patches
            excel_patcher.stop()
            renderer_patcher.stop()
            scoresheet_patcher.stop()

        return game_stats

    def test_multiple_ai_games(self):
        """Run multiple AI games and analyze the statistics"""
        # Configuration
        num_games = 20
        num_ai_players = 3

        # Storage for all games' statistics
        all_stats = []

        # Run multiple games
        for i in range(num_games):
            print(f"Running game {i + 1}/{num_games}...")
            game_stats = self.run_ai_game_with_stats(num_ai_players)
            all_stats.append(game_stats)
            print(f"Game {i + 1} complete - Rounds: {game_stats['total_rounds']}, Winner: {game_stats['winner']}")

        # Analyze the results
        # 1. Calculate how often a winner is identified
        games_with_winner = sum(1 for stats in all_stats if stats['has_winner'])
        winner_percentage = (games_with_winner / num_games) * 100

        # 2. Calculate distribution of winners
        winner_counts = Counter(stats['winner'] for stats in all_stats if stats['has_winner'])

        # 3. Calculate average rounds to completion
        rounds_data = [stats['total_rounds'] for stats in all_stats]
        avg_rounds = np.mean(rounds_data)
        std_rounds = np.std(rounds_data)

        # 4. Calculate elimination statistics
        avg_eliminations = np.mean([stats['eliminated_players'] for stats in all_stats])

        # 5. Calculate average game duration
        avg_duration = np.mean([stats['duration_seconds'] for stats in all_stats])

        # Print summary statistics
        print("\n===== GAME STATISTICS SUMMARY =====")
        print(f"Total games played: {num_games}")
        print(f"AI players per game: {num_ai_players}")
        print(f"Games with a winner: {games_with_winner}/{num_games} ({winner_percentage:.1f}%)")
        print(f"Average rounds to completion: {avg_rounds:.2f} ± {std_rounds:.2f}")
        print(f"Average eliminations per game: {avg_eliminations:.2f}")
        print(f"Average game duration: {avg_duration:.2f} seconds")

        print("\nWinner distribution:")
        for character, count in winner_counts.items():
            percentage = (count / games_with_winner) * 100 if games_with_winner > 0 else 0
            print(f"  {character}: {count} wins ({percentage:.1f}% of games with winners)")

        # Generate visualizations
        self.generate_visualizations(all_stats)

        # Create a detailed report
        self.create_statistics_report(all_stats, num_games, num_ai_players)

        # Verify basic expectations about the games
        self.assertTrue(num_games > 0, "No games were played")
        self.assertGreaterEqual(games_with_winner, 0, "Games with winner count is invalid")

        # Calculate confidence intervals for the rounds
        ci_factor = 1.96  # 95% confidence level
        rounds_ci = ci_factor * (std_rounds / np.sqrt(num_games))

        print(f"\n95% Confidence Interval for average rounds: "
              f"{avg_rounds:.2f} ± {rounds_ci:.2f} ({avg_rounds - rounds_ci:.2f} to {avg_rounds + rounds_ci:.2f})")

    def generate_visualizations(self, all_stats):
        """Generate visualizations of the game statistics"""
        # Create output directory
        os.makedirs(os.path.join(self.stats_dir, "plots"), exist_ok=True)

        # 1. Distribution of game rounds
        plt.figure(figsize=(10, 6))
        rounds_data = [stats['total_rounds'] for stats in all_stats]
        plt.hist(rounds_data, bins=max(5, min(20, len(all_stats) // 2)), alpha=0.7, color='blue')
        plt.axvline(np.mean(rounds_data), color='red', linestyle='dashed', linewidth=2)
        plt.title('Distribution of Game Rounds')
        plt.xlabel('Number of Rounds')
        plt.ylabel('Frequency')
        plt.text(0.95, 0.95, f'Mean: {np.mean(rounds_data):.2f}\nStd Dev: {np.std(rounds_data):.2f}',
                 transform=plt.gca().transAxes, horizontalalignment='right',
                 verticalalignment='top', bbox=dict(facecolor='white', alpha=0.8))
        plt.savefig(os.path.join(self.stats_dir, "plots", "rounds_distribution.png"))
        plt.close()

        # 2. Winner distribution pie chart
        if any(stats['has_winner'] for stats in all_stats):
            plt.figure(figsize=(10, 6))
            winner_counts = Counter(stats['winner'] for stats in all_stats if stats['has_winner'])
            labels = list(winner_counts.keys())
            sizes = list(winner_counts.values())
            plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
            plt.axis('equal')
            plt.title('Distribution of Winners')
            plt.savefig(os.path.join(self.stats_dir, "plots", "winner_distribution.png"))
            plt.close()

        # 3. Player status distribution
        plt.figure(figsize=(12, 6))
        # Collect all player statuses
        all_statuses = defaultdict(lambda: {'Winner': 0, 'Eliminated': 0, 'Active': 0})
        for stats in all_stats:
            for player, status in stats['player_statuses'].items():
                all_statuses[player][status] += 1

        # Prepare data for stacked bar chart
        players = list(all_statuses.keys())
        winners = [all_statuses[p]['Winner'] for p in players]
        eliminated = [all_statuses[p]['Eliminated'] for p in players]
        active = [all_statuses[p]['Active'] for p in players]

        # Create stacked bar chart
        ind = np.arange(len(players))
        width = 0.35
        plt.bar(ind, winners, width, label='Winner', color='green')
        plt.bar(ind, eliminated, width, bottom=winners, label='Eliminated', color='red')
        plt.bar(ind, active, width, bottom=np.array(winners) + np.array(eliminated), label='Active', color='blue')

        plt.ylabel('Count')
        plt.title('Player Status Distribution')
        plt.xticks(ind, players, rotation=45)
        plt.legend(loc="upper right")
        plt.tight_layout()
        plt.savefig(os.path.join(self.stats_dir, "plots", "player_status_distribution.png"))
        plt.close()

    def create_statistics_report(self, all_stats, num_games, num_ai_players):
        """Create a detailed statistics report as a text file"""
        report_path = os.path.join(self.stats_dir, "game_statistics_report.txt")

        with open(report_path, 'w') as f:
            f.write("======================================================\n")
            f.write("           CLUE AI GAME STATISTICS REPORT             \n")
            f.write("======================================================\n\n")

            f.write(f"Number of games analyzed: {num_games}\n")
            f.write(f"AI players per game: {num_ai_players}\n\n")

            # Winner statistics
            games_with_winner = sum(1 for stats in all_stats if stats['has_winner'])
            winner_percentage = (games_with_winner / num_games) * 100
            f.write("WINNER STATISTICS:\n")
            f.write(f"- Games with a winner: {games_with_winner}/{num_games} ({winner_percentage:.1f}%)\n")
            f.write(
                f"- Games with no winner: {num_games - games_with_winner}/{num_games} ({100 - winner_percentage:.1f}%)\n\n")

            if games_with_winner > 0:
                winner_counts = Counter(stats['winner'] for stats in all_stats if stats['has_winner'])
                f.write("Winner distribution:\n")
                for character, count in winner_counts.items():
                    percentage = (count / games_with_winner) * 100
                    f.write(f"  {character}: {count} wins ({percentage:.1f}% of games with winners)\n")
                f.write("\n")

            # Rounds statistics
            rounds_data = [stats['total_rounds'] for stats in all_stats]
            avg_rounds = np.mean(rounds_data)
            std_rounds = np.std(rounds_data)
            min_rounds = min(rounds_data)
            max_rounds = max(rounds_data)
            median_rounds = np.median(rounds_data)

            ci_factor = 1.96  # 95% confidence level
            rounds_ci = ci_factor * (std_rounds / np.sqrt(num_games))

            f.write("ROUNDS STATISTICS:\n")
            f.write(f"- Average rounds to completion: {avg_rounds:.2f} ± {std_rounds:.2f}\n")
            f.write(
                f"- 95% Confidence Interval: {avg_rounds:.2f} ± {rounds_ci:.2f} ({avg_rounds - rounds_ci:.2f} to {avg_rounds + rounds_ci:.2f})\n")
            f.write(f"- Median rounds: {median_rounds}\n")
            f.write(f"- Min rounds: {min_rounds}\n")
            f.write(f"- Max rounds: {max_rounds}\n\n")

            # Game duration statistics
            duration_data = [stats['duration_seconds'] for stats in all_stats]
            avg_duration = np.mean(duration_data)
            std_duration = np.std(duration_data)

            f.write("GAME DURATION STATISTICS:\n")
            f.write(f"- Average game duration: {avg_duration:.2f} seconds\n")
            f.write(f"- Standard deviation: {std_duration:.2f} seconds\n\n")

            # Player elimination statistics
            eliminated_data = [stats['eliminated_players'] for stats in all_stats]
            avg_eliminations = np.mean(eliminated_data)

            f.write("PLAYER ELIMINATION STATISTICS:\n")
            f.write(f"- Average eliminations per game: {avg_eliminations:.2f}\n")
            elimination_counts = Counter(eliminated_data)
            f.write("- Elimination distribution:\n")
            for count, frequency in sorted(elimination_counts.items()):
                percentage = (frequency / num_games) * 100
                f.write(f"  {count} eliminations: {frequency} games ({percentage:.1f}%)\n")
            f.write("\n")

            # Detailed game statistics
            f.write("DETAILED GAME RESULTS:\n")
            for i, stats in enumerate(all_stats):
                f.write(f"Game {i + 1}:\n")
                f.write(f"  - Rounds: {stats['total_rounds']}\n")
                f.write(f"  - Winner: {stats['winner'] if stats['has_winner'] else 'None'}\n")
                f.write(f"  - Eliminated players: {stats['eliminated_players']}/{stats['total_players']}\n")
                f.write(f"  - Duration: {stats['duration_seconds']:.2f} seconds\n")
                f.write("  - Player statuses:\n")
                for player, status in stats['player_statuses'].items():
                    f.write(f"    * {player}: {status}\n")
                f.write("\n")

            f.write("\n======================================================\n")
            f.write("                    END OF REPORT                     \n")
            f.write("======================================================\n")

        print(f"Detailed statistics report saved to: {report_path}")


if __name__ == '__main__':
    unittest.main()



===== GAME STATISTICS SUMMARY =====
Total games played: 20
AI players per game: 3
Games with a winner: 17/20 (85.0%)
Average rounds to completion: 98.35 ± 131.11
Average eliminations per game: 0.30
Average game duration: 5.27 seconds
