from Data.Constants import ROOMS
from Objects.Room import Room


class CharacterBoard:
    def __init__(self, rows, cols):
        self.grid = [[None for _ in range(cols)] for _ in range(rows)]
        self.positions = {}  # name → (row, col) or room name

    # -------- basic API --------
    def place(self, name, row, col):
        if self.grid[row][col] is not None:
            raise ValueError(f"Cell ({row},{col}) already occupied")

        val = str(self.grid[row][col])
        if val in ROOMS:
            # If placing in a room, just store room name
            self.positions[name] = val
        else:
            # Otherwise store grid position
            self.grid[row][col] = name
            self.positions[name] = (row, col)

    def move(self, name, new_row, new_col):
        curr_pos = self.positions[name]
        if isinstance(curr_pos, tuple):
            # Moving from grid position
            old_row, old_col = curr_pos
            self.grid[old_row][old_col] = None

        self.place(name, new_row, new_col)

    def get_cell_content(self, row, col):
        return self.grid[row][col]  # character name or None


class MansionBoard:
    def __init__(self, board_layout: object) -> None:
        self.grid = board_layout.fillna("").to_numpy()
        self.rows, self.cols = self.grid.shape
        self.room_dict = {name: Room(name) for name in ROOMS}
        self.bonus_card_spaces = []  # List of (row, col) tuples for bonus card spaces
        self.room_cells = {name: [] for name in ROOMS}  # Dictionary to store cells for each room
        self._scan_board()
        self._setup_secret_passages()

    def _setup_secret_passages(self):
        """Set up secret passages between rooms"""
        from Data.Constants import SECRET_PASSAGES
        for source_room, dest_room in SECRET_PASSAGES.items():
            if source_room in self.room_dict and dest_room in self.room_dict:
                self.room_dict[source_room].add_secret_passage(dest_room)

    def _scan_board(self):
        """Scan the board for room cells, entrances, and bonus card spaces"""
        for r in range(self.rows):
            for c in range(self.cols):
                val = str(self.grid[r][c])
                if val in ROOMS:
                    # Add to room cells dictionary
                    self.room_cells[val].append((r, c))
                elif val.endswith("_e"):
                    room_name = val.replace("_e", "")
                    if room_name in self.room_dict:
                        self.room_dict[room_name].add_room_entrance(r, c)
                        self.room_cells[room_name].append((r, c))
                elif val == "?":
                    # This is a bonus card space
                    self.bonus_card_spaces.append((r, c))

    def get_cell_type(self, r, c):
        if not (0 <= r < self.rows and 0 <= c < self.cols):
            return "out_of_bounds"

        val = str(self.grid[r][c])

        if val in ROOMS:
            return self.room_dict[val]
        elif val.endswith("_e"):
            room_name = val.replace("_e", "")
            if room_name in self.room_dict:
                room = self.room_dict[room_name]
                return room.get_room_entrance_from_cell(r, c)
        elif val == "?":
            return "bonus_card"
        else:
            return "hallway"

    def is_bonus_card_space(self, r, c):
        """Check if a cell is a bonus card space"""
        return (r, c) in self.bonus_card_spaces
    
    def get_room(self, room_name):
        """Get a room by name"""
        return self.room_dict.get(room_name)
    
    def get_room_cells(self, room_name):
        """Get all cells belonging to a specific room"""
        return self.room_cells.get(room_name, [])
    
    def get_room_entrances(self, room_name):
        """Get all entrances for a specific room"""
        room = self.get_room(room_name)
        if room:
            return [(entrance.row, entrance.column) for entrance in room.room_entrance_list]
        return []

    def get_room_name_at_position(self, row, col):
        """
        Determine which room a given position is in, if any.

        Args:
            row (int): Row coordinate on the board
            col (int): Column coordinate on the board

        Returns:
            str or None: The name of the room at the position, or None if not in a room
        """
        # Check if the position is within board boundaries
        if not (0 <= row < self.rows and 0 <= col < self.cols):
            return None

        # Get the value at this position
        val = str(self.grid[row][col])

        # If it's directly a room name, return it
        if val in ROOMS:
            return val

        # If it's a room entrance, extract the room name
        if val.endswith("_e"):
            room_name = val.replace("_e", "")
            if room_name in ROOMS:
                return room_name

        # For all other cases (hallways, bonus card spaces, etc.), return None
        return None