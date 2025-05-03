# Game/Interface.py
class Interface:
    @staticmethod
    def print_board(board, character_board):
        """Print a text representation of the board."""
        for r in range(board.rows):
            row_str = ""
            for c in range(board.cols):
                cell_content = character_board.get_cell_content(r, c)
                cell_type = board.get_cell_type(r, c)

                if cell_content:
                    # Show first character of player name
                    row_str += cell_content[0] + " "
                elif isinstance(cell_type, str):
                    if cell_type == "hallway":
                        row_str += ". "
                    elif cell_type == "bonus_card":
                        row_str += "? "
                    elif cell_type == "out_of_bounds":
                        row_str += "  "
                else:
                    # It's a room or room entrance
                    row_str += "R "
            print(row_str)

    @staticmethod
    def print_player_hand(player):
        """Print a player's hand."""
        print(f"\n{player.character_name}'s Hand:")
        for card_type, card_name in player.hand:
            print(f"- {card_type.title()}: {card_name}")

    @staticmethod
    def print_player_knowledge(player):
        """Print a player's current knowledge."""
        print(f"\n{player.character_name}'s Knowledge:")

        print("\nPossible suspects:")
        for suspect in player.possible_suspects:
            print(f"- {suspect}")

        print("\nPossible weapons:")
        for weapon in player.possible_weapons:
            print(f"- {weapon}")

        print("\nPossible rooms:")
        for room in player.possible_rooms:
            print(f"- {room}")

    @staticmethod
    def print_board_status(game):
        """Print a summary of the current board status."""
        print("\n===== BOARD STATUS =====")

        print("\nCharacters:")
        for name, character in game.characters.items():
            print(f"- {name}: {character.position}")

        print("\nWeapons:")
        for name, weapon in game.weapons.items():
            print(f"- {name}: {weapon.location}")