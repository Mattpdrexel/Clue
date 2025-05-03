# Game/GameSetup.py (update)
from Objects.Board import MansionBoard, CharacterBoard
from Objects.Character import Character
from Objects.Weapon import Weapon
from Data.Constants import CHARACTERS, WEAPONS
import pandas as pd


# Initialize the game
def initialize_game():
    # Load and create the mansion board
    mansion_board_layout = pd.read_excel("Data/mansion_board_layout.xlsx", header=None)
    mansion_board = MansionBoard(mansion_board_layout)

    # Create the character board with the same dimensions as mansion board
    character_board = CharacterBoard(mansion_board.rows, mansion_board.cols)

    # Create character instances
    characters = {name: Character(name) for name in CHARACTERS}

    # Create weapon instances
    weapons = {name: Weapon(name) for name in WEAPONS}

    # Place all characters in the Clue room
    setup_characters_in_clue_room(mansion_board, character_board, characters)

    # Place all weapons in the Clue room
    setup_weapons_in_clue_room(weapons)

    return mansion_board, character_board, characters, weapons


def setup_weapons_in_clue_room(weapons):
    """Place all weapons in the Clue room"""
    for name, weapon in weapons.items():
        weapon.move_to("Clue")
        print(f"Placed {name} in the Clue room")


def setup_characters_in_clue_room(mansion_board, character_board, characters):
    """Place all characters in the Clue room"""
    # Get cells for the Clue room
    clue_room_cells = mansion_board.get_room_cells("Clue")

    if not clue_room_cells:
        print("Error: Could not find cells for the Clue room!")
        return

    # Make sure we have enough cells for all characters
    if len(clue_room_cells) < len(characters):
        print(f"Error: Not enough cells in Clue room ({len(clue_room_cells)}) for all characters ({len(characters)})")
        return

    # Place each character in a different cell in the Clue room
    # This is done just so they appear to be in different spots initially
    # All spots in a Room are treated identically
    for (name, character), cell in zip(characters.items(), clue_room_cells):
        row, col = cell

        # Update the character's position
        character.move_to(("Clue", row, col))

        # Place the character on the board
        try:
            character_board.place(name, row, col)
            print(f"Placed {name} in the Clue room at position ({row}, {col})")
        except ValueError as e:
            print(f"Error placing {name}: {e}")
            character_board.positions[name] = "Clue"

    print(f"All characters have been placed in the Clue room")


def print_game_state(mansion_board, character_board, characters, weapons):
    """Print the current state of the game"""
    print("\n===== GAME STATE =====")
    print("Mansion Board Dimensions:", mansion_board.rows, "x", mansion_board.cols)

    print("\nCharacter Positions:")
    for name, character in characters.items():
        print(f"- {name}: {character.position}")

    print("\nWeapon Positions:")
    for name, weapon in weapons.items():
        print(f"- {name}: {weapon.location}")

    print("\nCharacter Board Positions:")
    for name, position in character_board.positions.items():
        print(f"- {name}: {position}")