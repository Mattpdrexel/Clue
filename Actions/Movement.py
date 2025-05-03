from Data.Constants import SUSPECT_ROOMS


def get_room_and_position(character_position, board):
    """
    Get both the room name and coordinates from a character's position.

    Args:
        character_position: Position in any format (string room name, (row, col) tuple, or (room_name, row, col) tuple)
        board: MansionBoard instance

    Returns:
        tuple: (room_name or None, row, col)
    """
    # If position is a tuple with 3 elements, it's (room_name, row, col)
    if isinstance(character_position, tuple) and len(character_position) == 3:
        room_name, row, col = character_position
        return room_name, row, col

    # If it's a tuple with 2 elements, it's (row, col)
    elif isinstance(character_position, tuple) and len(character_position) == 2:
        row, col = character_position
        room_name = board.get_room_at_position(row, col)
        return room_name, row, col

    # If it's a string, it's a room name
    elif isinstance(character_position, str):
        room_name = character_position
        # For a room name, we need a valid position within the room
        # We'll use a cell in the room (doesn't matter which one for most purposes)
        room_cells = board.get_room_cells(room_name)
        if not room_cells:
            raise ValueError(f"No cells found for room '{room_name}'")
        row, col = room_cells[0]  # Take the first cell
        return room_name, row, col

    else:
        raise ValueError(f"Invalid position format: {character_position}")


def is_legal_move(board, character_board, from_pos, to_pos):
    """
    Check if a move from one position to another is legal.

    Args:
        board (MansionBoard): The game board
        character_board (CharacterBoard): The board tracking character positions
        from_pos (tuple): Starting position (row, col)
        to_pos (tuple): Target position (row, col)

    Returns:
        bool: True if the move is legal, False otherwise
    """
    # Unpack positions
    from_row, from_col = from_pos
    to_row, to_col = to_pos

    # Check if target position is within board boundaries
    if not (0 <= to_row < board.rows and 0 <= to_col < board.cols):
        return False

    # Check if target position is occupied by another character
    if character_board.get_cell_content(to_row, to_col) is not None:
        return False

    # Get the current room if we're in one
    current_room = board.get_room_name_at_position(from_row, from_col)
    target_room = board.get_room_name_at_position(to_row, to_col)

    # If moving from a room to a hallway
    if current_room and not target_room:
        # Get the room object
        room_obj = board.get_room(current_room)

        # Check if we're moving from an entrance to an adjacent hallway cell
        for entrance in room_obj.room_entrance_list:
            # Check if the target position is adjacent to this entrance
            if abs(to_row - entrance.row) + abs(to_col - entrance.column) == 1:
                return True

        return False

    # If moving from hallway to a room entrance
    if not current_room and target_room:
        # Get the room object
        target_room_obj = board.get_room(target_room)

        # Check if the target position is a room entrance
        entrance = target_room_obj.get_room_entrance_from_cell(to_row, to_col)
        if entrance:
            return True

        return False

    # If moving in the hallway (from hallway to hallway)
    if not current_room and not target_room:
        # Check if we're making a valid hallway move (adjacent cells with manhattan distance = 1)
        if abs(from_row - to_row) + abs(from_col - to_col) == 1:
            # Make sure the target cell is a valid hallway cell
            cell_type = board.get_cell_type(to_row, to_col)
            return cell_type is None or cell_type in ["hallway", "bonus_card"]

    return False


def find_reachable_rooms(character_position, board, character_board, die_roll):
    """
    Find all rooms that can be reached with the given die roll.

    Args:
        character_position: Starting position in any format
        board: MansionBoard instance
        character_board: CharacterBoard instance
        die_roll: Number of steps available for movement

    Returns:
        dict: Mapping of room names to the cells in those rooms that can be entered
    """
    room_name, row, col = get_room_and_position(character_position, board)
    current_position = (row, col)

    # Dictionary to store reachable rooms and the cells in them
    reachable_rooms = {}

    # If we're already in a room, we can use a secret passage
    if room_name:
        room_obj = board.get_room(room_name)
        if hasattr(room_obj, 'secret_passage_to') and room_obj.secret_passage_to:
            dest_room = room_obj.secret_passage_to
            dest_cells = board.get_room_cells(dest_room)
            reachable_rooms[dest_room] = dest_cells

    # BFS to find all reachable room entrances
    visited = set([current_position])
    # Track (position, steps_taken)
    queue = [(current_position, 0)]

    while queue:
        (r, c), steps = queue.pop(0)

        # If we've used all our steps, we can't go further
        if steps == die_roll:
            continue

        # Try all four directions
        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            new_r, new_c = r + dr, c + dc
            new_pos = (new_r, new_c)

            # Skip if already visited or not a legal move
            if new_pos in visited or not is_legal_move(board, character_board, (r, c), new_pos):
                continue

            visited.add(new_pos)

            # Check if this is a room entrance
            target_room = board.get_room_name_at_position(new_r, new_c)
            if target_room:
                room_obj = board.get_room(target_room)
                entrance = room_obj.get_room_entrance_from_cell(new_r, new_c)

                if entrance:
                    # We can enter this room
                    if target_room not in reachable_rooms:
                        reachable_rooms[target_room] = board.get_room_cells(target_room)
                    # Going through an entrance to another room ends movement
                    continue

            # Add this position to the queue for further exploration
            queue.append((new_pos, steps + 1))

    return reachable_rooms


def get_hallway_moves(character_position, board, character_board, die_roll):
    """
    Get all valid hallway positions a character can move to.

    Args:
        character_position: Starting position in any format
        board: MansionBoard instance
        character_board: CharacterBoard instance
        die_roll: Number of steps available for movement

    Returns:
        list: Valid hallway positions (row, col) the character can move to
    """
    room_name, row, col = get_room_and_position(character_position, board)
    current_position = (row, col)

    # BFS to find all reachable hallway positions
    visited = set([current_position])
    queue = [(current_position, 0)]  # (position, steps_taken)
    valid_moves = []

    while queue:
        (r, c), steps = queue.pop(0)

        # If we've used all our steps, this is a potential final destination
        if steps == die_roll:
            # Make sure this isn't our starting position and it's not in a room
            if (r, c) != current_position and not board.get_room_name_at_position(r, c):
                valid_moves.append((r, c))
            continue

        # Try all four directions
        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            new_r, new_c = r + dr, c + dc
            new_pos = (new_r, new_c)

            # Skip if already visited
            if new_pos in visited:
                continue

            # Skip if not a legal move
            if not is_legal_move(board, character_board, (r, c), new_pos):
                continue

            visited.add(new_pos)

            # Check if this is a room entrance - if so, skip (we'll handle rooms separately)
            new_room = board.get_room_name_at_position(new_r, new_c)
            if new_room:
                room_obj = board.get_room(new_room)
                entrance = room_obj.get_room_entrance_from_cell(new_r, new_c)
                if entrance:
                    continue

            # Add to queue for further exploration
            queue.append((new_pos, steps + 1))

    return valid_moves


def get_available_moves(character_position, board, character_board, die_roll):
    """
    Get all valid moves for a character's current position based on die roll.

    Args:
        character_position: Position in any format
        board (MansionBoard): The game board
        character_board (CharacterBoard): Board tracking character positions
        die_roll (int): Result of die roll (typically 1-6)

    Returns:
        list: List of valid positions (row, col) the character can move to
    """
    if not character_position:
        return []

    # Get room and position information
    try:
        room_name, row, col = get_room_and_position(character_position, board)
    except ValueError:
        return []

    valid_moves = []

    # Find all reachable rooms
    reachable_rooms = find_reachable_rooms(character_position, board, character_board, die_roll)

    # Add all cells from reachable rooms
    for room, cells in reachable_rooms.items():
        valid_moves.extend(cells)

    # If the character is in a hallway, find all valid hallway moves
    if not room_name:
        hallway_moves = get_hallway_moves(character_position, board, character_board, die_roll)
        valid_moves.extend(hallway_moves)
    # If in a room, handle room exits to hallways
    else:
        # For each entrance, find valid moves in the hallway
        room_obj = board.get_room(room_name)
        visited = set()

        for entrance in room_obj.room_entrance_list:
            entrance_pos = (entrance.row, entrance.column)

            # Try all four directions from the entrance
            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                hallway_row, hallway_col = entrance.row + dr, entrance.column + dc
                hallway_pos = (hallway_row, hallway_col)

                # Skip if out of bounds or not a legal move
                if not (0 <= hallway_row < board.rows and 0 <= hallway_col < board.cols):
                    continue
                if hallway_pos in visited:
                    continue
                if not is_legal_move(board, character_board, entrance_pos, hallway_pos):
                    continue

                # Start BFS from this hallway position with one less step
                visited.add(hallway_pos)

                # If we have only 1 step, this is as far as we can go
                if die_roll == 1:
                    valid_moves.append(hallway_pos)
                # Otherwise continue BFS
                else:
                    queue = [(hallway_pos, 1)]  # (position, steps_taken)

                    while queue:
                        (pos_r, pos_c), pos_steps = queue.pop(0)

                        # If we've used all our steps, this is a potential final destination
                        if pos_steps == die_roll:
                            valid_moves.append((pos_r, pos_c))
                            continue

                        # Try all four directions
                        for pos_dr, pos_dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                            next_r, next_c = pos_r + pos_dr, pos_c + pos_dc
                            next_pos = (next_r, next_c)

                            # Skip if already visited
                            if next_pos in visited:
                                continue

                            # Skip if not a legal move
                            if not is_legal_move(board, character_board, (pos_r, pos_c), next_pos):
                                continue

                            visited.add(next_pos)

                            # Check if this is a room entrance
                            next_room = board.get_room_name_at_position(next_r, next_c)
                            if next_room:
                                next_room_obj = board.get_room(next_room)
                                entrance = next_room_obj.get_room_entrance_from_cell(next_r, next_c)
                                if entrance:
                                    # Add all cells in this room to valid moves
                                    room_cells = board.get_room_cells(next_room)
                                    valid_moves.extend(room_cells)
                                    continue

                            # Add to queue for further exploration
                            queue.append((next_pos, pos_steps + 1))

    # Remove duplicates
    return list(set(valid_moves))


def can_use_secret_passage(character_position, board):
    """
    Check if a character can use a secret passage from their current position.

    Args:
        character_position: Position in any format
        board (MansionBoard): The game board

    Returns:
        tuple: (bool, destination_room) - Whether secret passage can be used and destination room
    """
    try:
        room_name, _, _ = get_room_and_position(character_position, board)
    except ValueError:
        return False, None

    # Check if there's a secret passage from this room
    if room_name:
        room_obj = board.get_room(room_name)
        if hasattr(room_obj, 'secret_passage_to') and room_obj.secret_passage_to:
            return True, room_obj.secret_passage_to

    return False, None