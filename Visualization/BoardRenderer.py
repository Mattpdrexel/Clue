# Visualization/BoardRenderer.py
"""
Module for rendering the Clue game board as image files.
"""
import os
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import matplotlib.patches as patches


class BoardRenderer:
    """Class to handle rendering the Clue game board as image files."""

    # Define colors for different elements
    COLORS = {
        'wall': '#000000',  # Black
        'empty': '#FFFFFF',  # White
        'corridor': '#EEEEEE',  # Light Gray
        'entrance': '#FF8C00',  # Dark Orange
        'character': {
            'Miss Scarlet': '#FF0000',  # Red
            'Colonel Mustard': '#FFD700',  # Gold
            'Mrs. White': '#E0E0E0',  # Light Gray
            'Reverend Green': '#32CD32',  # Lime Green
            'Mrs Peacock': '#1E90FF',  # Dodger Blue
            'Professor Plum': '#9400D3',  # Dark Violet
        },
        'weapon': '#C0C0C0',  # Silver
        'room': {
            'Study': '#9370DB',  # Medium Purple
            'Hall': '#FF6347',  # Tomato
            'Lounge': '#20B2AA',  # Light Sea Green
            'Dining Room': '#DAA520',  # Goldenrod
            'Kitchen': '#87CEFA',  # Light Sky Blue
            'Ballroom': '#FF69B4',  # Hot Pink
            'Conservatory': '#00CED1',  # Dark Turquoise
            'Billiard Room': '#3CB371',  # Medium Sea Green
            'Library': '#F4A460',  # Sandy Brown
            'Clue': '#FFFF00',  # Yellow
        }
    }

    # Character symbols (2-letter abbreviations)
    SYMBOLS = {
        'character': {
            'Miss Scarlet': 'MS',
            'Colonel Mustard': 'CM',
            'Mrs. White': 'MW',
            'Reverend Green': 'RG',
            'Mrs Peacock': 'MP',
            'Professor Plum': 'PP'
        },
        'weapon': {
            'Candlestick': 'Ca',
            'Lead Pipe': 'LP',
            'Wrench': 'Wr',
            'Knife': 'Kn',
            'Revolver': 'Re',
            'Rope': 'Ro'
        }
    }

    def __init__(self, game):
        """Initialize the board renderer with the game state."""
        self.game = game
        self.output_dir = "Output/boards"
        os.makedirs(self.output_dir, exist_ok=True)
        self.frame_counter = 0

    def save_board_frame(self):
        """Generate and save an image of the current game board state."""
        # Increment counter and create filename
        self.frame_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.output_dir}/board_frame_{self.frame_counter:04d}_{timestamp}.png"

        # Generate the image
        self.render_image(filename)

        print(f"Board image saved as {filename}")

    def render_image(self, filename):
        """
        Render the board as an image using matplotlib.
        """
        mansion_board = self.game.mansion_board

        # Get dimensions
        rows = mansion_board.rows
        cols = mansion_board.cols

        # Create numeric matrix for board state and text labels
        board_numeric = np.zeros((rows, cols))
        board_text = np.empty((rows, cols), dtype=object)

        # Define numeric values for different cell types
        cell_type_values = {
            'wall': 1,
            'corridor': 2,
            'entrance': 3,
            'room_base': 4,  # Base value for rooms, specific rooms will be 4, 5, 6, etc.
            'character_base': 14,  # Base value for characters
            'weapon_base': 20,  # Base value for weapons
        }

        # Map room names to numeric values
        room_values = {}
        for i, room_name in enumerate(self.COLORS['room'].keys()):
            room_values[room_name] = cell_type_values['room_base'] + i

        # Map character names to numeric values
        character_values = {}
        for i, char_name in enumerate(self.COLORS['character'].keys()):
            character_values[char_name] = cell_type_values['character_base'] + i

        # Fill in the board with basic cell types
        for r in range(rows):
            for c in range(cols):
                cell_type = mansion_board.get_cell_type(r, c)

                if cell_type == "out_of_bounds":
                    board_numeric[r, c] = cell_type_values['wall']
                    board_text[r, c] = ""
                elif cell_type == "corridor":
                    board_numeric[r, c] = cell_type_values['corridor']
                    board_text[r, c] = ""
                elif hasattr(cell_type, 'name'):  # Room
                    room_name = cell_type.name
                    board_numeric[r, c] = room_values.get(room_name, cell_type_values['room_base'])
                    board_text[r, c] = ""
                elif cell_type is not None and hasattr(cell_type, 'room_name'):  # Entrance
                    board_numeric[r, c] = cell_type_values['entrance']
                    board_text[r, c] = "E"
                else:
                    board_numeric[r, c] = cell_type_values['corridor']
                    board_text[r, c] = ""

        # Add characters to the board
        for character in self.game.characters.values():
            if isinstance(character.position, tuple):
                if len(character.position) == 2:
                    # Position is (row, col)
                    r, c = character.position
                elif len(character.position) == 3:
                    # Position is (room_name, row, col)
                    _, r, c = character.position
                else:
                    continue

                if 0 <= r < rows and 0 <= c < cols:
                    board_numeric[r, c] = character_values.get(character.name, cell_type_values['character_base'])
                    board_text[r, c] = self.SYMBOLS['character'][character.name]

        # Add weapons to the board (approximation)
        for weapon in self.game.weapons.values():
            if hasattr(weapon, 'location') and weapon.location is not None:
                if weapon.location != "Clue":
                    # Find a position in the room to place the weapon
                    room_cells = []
                    for r in range(rows):
                        for c in range(cols):
                            cell_type = mansion_board.get_cell_type(r, c)
                            if hasattr(cell_type, 'name') and cell_type.name == weapon.location:
                                room_cells.append((r, c))

                    if room_cells:
                        # Place weapon in first empty room cell
                        for r, c in room_cells:
                            if board_text[r, c] == "":
                                board_numeric[r, c] = cell_type_values['weapon_base']
                                board_text[r, c] = self.SYMBOLS['weapon'][weapon.name]
                                break

        # Create a colormap for the board
        colors = ['white']  # 0: Empty (should not be used)
        colors.append('black')  # 1: Wall
        colors.append('#EEEEEE')  # 2: Corridor
        colors.append('orange')  # 3: Entrance

        # Add colors for rooms
        for room_name in self.COLORS['room'].keys():
            colors.append(self.COLORS['room'][room_name])

        # Add colors for characters
        for char_name in self.COLORS['character'].keys():
            colors.append(self.COLORS['character'][char_name])

        # Add color for weapons
        colors.append(self.COLORS['weapon'])

        # Create colormap
        cmap = mcolors.ListedColormap(colors)

        # Create the plot
        fig, ax = plt.subplots(figsize=(12, 10))

        # Show the board with colors
        im = ax.imshow(board_numeric, cmap=cmap, interpolation='nearest')

        # Add room labels for rooms with more than 5 cells
        room_cells_count = {}
        room_centers = {}

        # Count cells for each room and calculate centers
        for r in range(rows):
            for c in range(cols):
                cell_type = mansion_board.get_cell_type(r, c)
                if hasattr(cell_type, 'name'):
                    room_name = cell_type.name
                    if room_name not in room_cells_count:
                        room_cells_count[room_name] = []
                    room_cells_count[room_name].append((r, c))

        # Calculate centers for each room
        for room_name, cells in room_cells_count.items():
            if len(cells) > 5:  # Only label rooms with enough cells
                avg_r = sum(r for r, _ in cells) / len(cells)
                avg_c = sum(c for _, c in cells) / len(cells)
                room_centers[room_name] = (avg_r, avg_c)

        # Label rooms
        for room_name, (r, c) in room_centers.items():
            ax.text(c, r, room_name, ha='center', va='center', color='black',
                    fontsize=10, fontweight='bold', alpha=0.7)

        # Add text labels for characters and entrances
        for r in range(rows):
            for c in range(cols):
                if board_text[r, c]:
                    # Choose text color based on background
                    bg_value = board_numeric[r, c]
                    text_color = 'white' if bg_value in [1, 14, 15, 16, 17, 18, 19] else 'black'
                    ax.text(c, r, board_text[r, c], ha='center', va='center',
                            color=text_color, fontsize=8, fontweight='bold')

        # Set grid lines
        ax.set_xticks(np.arange(-0.5, cols, 1), minor=True)
        ax.set_yticks(np.arange(-0.5, rows, 1), minor=True)
        ax.grid(which='minor', color='black', linestyle='-', linewidth=0.5)

        # Add row and column labels
        ax.set_xticks(np.arange(0, cols, 1))
        ax.set_yticks(np.arange(0, rows, 1))
        ax.set_xticklabels([str(i) for i in range(cols)], fontsize=8)
        ax.set_yticklabels([str(i) for i in range(rows)], fontsize=8)

        # Add title with frame number
        plt.title(f'Clue Game Board - Frame {self.frame_counter}')

        # Add legend for characters
        legend_elements = []
        for char_name, symbol in self.SYMBOLS['character'].items():
            color = self.COLORS['character'][char_name]
            legend_elements.append(patches.Patch(facecolor=color, edgecolor='black',
                                                 label=f'{symbol}: {char_name}'))

        # Add legend for weapons
        for weapon_name, symbol in self.SYMBOLS['weapon'].items():
            legend_elements.append(patches.Patch(facecolor=self.COLORS['weapon'],
                                                 edgecolor='black', label=f'{symbol}: {weapon_name}'))

        # Add special elements to legend
        legend_elements.append(patches.Patch(facecolor='orange',
                                             edgecolor='black', label='E: Room Entrance'))

        # Place legend outside the plot
        ax.legend(handles=legend_elements, loc='upper left',
                  bbox_to_anchor=(1.05, 1), title="Characters & Weapons")

        plt.tight_layout()

        # Save the image
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close()

        # Also save a game state text file with the same name
        self._save_game_state(filename.replace('.png', '.txt'))

    def _save_game_state(self, filename):
        """Save a text file with the current game state information."""
        with open(filename, 'w') as f:
            f.write(f"===== CLUE GAME STATE - FRAME {self.frame_counter} =====\n\n")

            f.write("Character Positions:\n")
            for name, character in sorted(self.game.characters.items()):
                f.write(f"- {name}: {character.position}\n")

            f.write("\nWeapon Locations:\n")
            for name, weapon in sorted(self.game.weapons.items()):
                if hasattr(weapon, 'location'):
                    f.write(f"- {name}: {weapon.location}\n")

            # Add more game state information if available
            if hasattr(self.game, 'current_player_idx') and hasattr(self.game, 'players'):
                f.write("\nCurrent Player: ")
                if 0 <= self.game.current_player_idx < len(self.game.players):
                    current_player = self.game.players[self.game.current_player_idx]
                    f.write(f"{current_player.character_name}")
                else:
                    f.write("Unknown")

            if hasattr(self.game, 'current_round'):
                f.write(f"\nCurrent Round: {self.game.current_round}")

    # Add to the BoardRenderer class

    def create_game_animation(self):
        """Create a video animation of the board frames if moviepy is installed."""
        try:
            from moviepy.editor import ImageSequenceClip
            import glob

            # Find all PNG files in the output directory
            files = sorted(glob.glob(f"{self.output_dir}/board_frame_*.png"))

            if not files:
                print("No image files found to create animation.")
                return

            # Create clip from images
            clip = ImageSequenceClip(files, fps=1)  # 1 frame per second

            # Write the clip to a file
            clip_file = f"{self.output_dir}/game_animation.mp4"
            clip.write_videofile(clip_file, codec='libx264')

            print(f"Game animation saved to {clip_file}")

        except ImportError:
            print("Warning: moviepy not available. Cannot create animation.")
            print("To create animations, install moviepy: pip install moviepy")