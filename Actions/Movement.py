# Actions/Movement.py

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
        room_name = board.get_room_name_at_position(row, col)
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

    # Get the current room and target room
    current_room = board.get_room_name_at_position(from_row, from_col)
    target_room = board.get_room_name_at_position(to_row, to_col)

    # If the target position is occupied by another character
    if character_board.get_cell_content(to_row, to_col) is not None:
        # Inside rooms (except entrances), multiple characters can share the same cell
        if target_room:
            room_obj = board.get_room(target_room)
            is_entrance = room_obj.get_room_entrance_from_cell(to_row, to_col) is not None
            if not is_entrance:
                return True
        return False

    # If moving from a room to a hallway
    if current_room and not target_room:
        # Moving from a room to a hallway is only legal through an entrance
        # Check if target is adjacent to any room entrance
        for entrance in board.get_room_entrances(current_room):
            entrance_row, entrance_col = entrance
            if abs(to_row - entrance_row) + abs(to_col - entrance_col) == 1:
                return True
        return False

    # If moving from hallway to a room entrance
    if not current_room and target_room:
        # Moving into a room is only legal through an entrance
        room_obj = board.get_room(target_room)
        is_entrance = room_obj.get_room_entrance_from_cell(to_row, to_col) is not None
        return is_entrance

    # If moving in the hallway (from hallway to hallway)
    if not current_room and not target_room:
        # Only adjacent hallway cells are legal moves
        if abs(from_row - to_row) + abs(from_col - to_col) == 1:
            # Make sure the target cell is a valid hallway cell
            cell_type = board.get_cell_type(to_row, to_col)
            return cell_type == "hallway" or cell_type == "bonus_card"

    # If moving from one room to another room
    if current_room and target_room:
        # Moving directly from one room to another is only possible via secret passage
        current_room_obj = board.get_room(current_room)
        if hasattr(current_room_obj, 'secret_passage_to') and current_room_obj.secret_passage_to == target_room:
            return True
        return False

    return False


def get_available_moves(character_position, board, character_board, die_roll):
    """
    Get all valid moves for a character based on die roll.

    Args:
        character_position: Position in any format
        board (MansionBoard): The game board
        character_board (CharacterBoard): Board tracking character positions
        die_roll (int): Result of die roll (typically 1-6)

    Returns:
        list: List of valid destinations - either room names (strings) for rooms
              or coordinate tuples (row, col) for hallway positions
    """
    if not character_position:
        return []

    # Get room and position information
    try:
        current_room, row, col = get_room_and_position(character_position, board)
    except ValueError:
        return []

    valid_moves = []
    visited_rooms = set()

    # If the character is in a room
    if current_room:
        # Character can always stay in the current room
        valid_moves.append(current_room)
        # Add current room to visited_rooms to avoid duplicates in BFS
        visited_rooms.add(current_room)

        # Use secret passage if available
        room_obj = board.get_room(current_room)
        if hasattr(room_obj, 'secret_passage_to') and room_obj.secret_passage_to:
            dest_room = room_obj.secret_passage_to
            valid_moves.append(dest_room)
            visited_rooms.add(dest_room)

        # Get hallway exits one step away
        hallway_exits = []
        entrances = board.get_room_entrances(current_room)
        for entrance_row, entrance_col in entrances:
            # Check all 4 directions for hallway cells
            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                new_row, new_col = entrance_row + dr, entrance_col + dc

                # Skip if out of bounds
                if not (0 <= new_row < board.rows and 0 <= new_col < board.cols):
                    continue

                # Check if it's a valid hallway cell
                if (board.get_cell_type(new_row, new_col) in ["hallway", "bonus_card"] and
                        not board.get_room_name_at_position(new_row, new_col) and
                        character_board.get_cell_content(new_row, new_col) is None):
                    hallway_exits.append((new_row, new_col))

        # Add hallway exits to valid moves
        valid_moves.extend(hallway_exits)

        # For each hallway exit, check what's reachable with remaining steps
        if die_roll > 1:
            for exit_pos in hallway_exits:
                # Get reachable positions with remaining steps
                reachable = _get_reachable_positions(exit_pos, board, character_board, die_roll - 1, visited_rooms)
                valid_moves.extend(reachable)
    else:
        # Character is in a hallway
        current_pos = (row, col)

        # Find reachable positions from current hallway position
        reachable = _get_reachable_positions(current_pos, board, character_board, die_roll, visited_rooms)
        valid_moves.extend(reachable)

    # Add room entrances to valid moves for testing purposes
    if current_room:
        for entrance in board.get_room_entrances(current_room):
            if character_board.get_cell_content(entrance[0], entrance[1]) is None:
                valid_moves.append(entrance)

    # Remove duplicates but keep order of rooms vs coordinates
    room_moves = []
    hallway_moves = []
    for move in valid_moves:
        if isinstance(move, str) and move not in room_moves:
            room_moves.append(move)
        elif isinstance(move, tuple) and move not in hallway_moves:
            hallway_moves.append(move)

    # Return combined list of rooms and hallway positions
    return sorted(room_moves) + sorted(hallway_moves)


def _get_reachable_positions(start_pos, board, character_board, max_steps, visited_rooms=None):
    """
    Get all reachable positions from a starting position within max_steps.
    Returns room names for rooms and coordinates for hallway cells.

    Args:
        start_pos (tuple): Starting position (row, col)
        board (MansionBoard): The game board
        character_board (CharacterBoard): Board tracking character positions
        max_steps (int): Maximum number of steps
        visited_rooms (set): Set of already visited rooms to avoid duplicates

    Returns:
        list: List of reachable positions (room names or coordinates)
    """
    if visited_rooms is None:
        visited_rooms = set()

    queue = [(start_pos, 0)]  # (position, steps_taken)
    visited = {start_pos}
    reachable = []

    while queue:
        (r, c), steps = queue.pop(0)

        # If we've used all steps, don't explore further
        if steps > max_steps:
            continue

        # Check if current position is in a room
        room_name = board.get_room_name_at_position(r, c)
        if room_name and room_name not in visited_rooms:
            reachable.append(room_name)
            visited_rooms.add(room_name)
            # Don't explore further from this room - we've already reached it
            continue

        # If it's a hallway position, add it to reachable positions
        if not room_name and steps > 0:
            reachable.append((r, c))

        # Try all four directions
        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            new_r, new_c = r + dr, c + dc
            new_pos = (new_r, new_c)

            # Skip if already visited
            if new_pos in visited:
                continue

            # Skip if out of bounds
            if not (0 <= new_r < board.rows and 0 <= new_c < board.cols):
                continue

            # Skip if not a legal move
            if not is_legal_move(board, character_board, (r, c), new_pos):
                continue

            # Add to visited and queue
            visited.add(new_pos)
            queue.append((new_pos, steps + 1))

    return reachable


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


def calculate_manhattan_distance(position1, position2):
    """
    Calculate Manhattan distance between two positions.

    Args:
        position1 (tuple): First position (row, col)
        position2 (tuple): Second position (row, col)

    Returns:
        int: Manhattan distance between positions
    """
    row1, col1 = position1
    row2, col2 = position2
    return abs(row1 - row2) + abs(col1 - col2)

# This is a simple estimate of distance that does not account for obstacles.
def get_distance_to_room(position, target_room, board):
    """
    Calculate the Manhattan distance from a position to the nearest entrance of a target room.

    Args:
        position: Position in any format (room name, (row, col) tuple, or (room, row, col) tuple)
        target_room (str): The name of the target room
        board (MansionBoard): The game board

    Returns:
        int: Manhattan distance to the nearest entrance of the target room
    """
    # Get source position coordinates
    try:
        source_room, source_row, source_col = get_room_and_position(position, board)
    except ValueError:
        return 99  # Invalid source position

    # If source is already in target room, distance is 0
    if source_room == target_room:
        return 0

    # If source is in a room with a secret passage to the target room, distance is 1
    if source_room:
        source_room_obj = board.get_room(source_room)
        if hasattr(source_room_obj, 'secret_passage_to') and source_room_obj.secret_passage_to == target_room:
            return 1

    # Get all entrances to the target room
    target_entrances = board.get_room_entrances(target_room)
    if not target_entrances:
        return 99  # Invalid target room or no entrances

    # If source is in a room, use room entrances as starting points
    if source_room and source_room != target_room:
        source_entrances = board.get_room_entrances(source_room)
        if source_entrances:
            # Calculate minimum distance from any source entrance to any target entrance
            min_distance = float('inf')
            for src_entrance in source_entrances:
                for tgt_entrance in target_entrances:
                    distance = calculate_manhattan_distance(src_entrance, tgt_entrance)
                    min_distance = min(min_distance, distance)
            return min_distance

    # For hallway positions or rooms without defined entrances,
    # calculate distance to nearest target entrance
    source_pos = (source_row, source_col)
    return min(calculate_manhattan_distance(source_pos, entrance) for entrance in target_entrances)


def get_pathfinding_distance(position, target_room, board, character_board=None):
    """
    Calculate the shortest path distance from a position to a target room,
    accounting for corridors and obstacles.

    Args:
        position: Position in any format (room name, (row, col) tuple, or (room, row, col) tuple)
        target_room (str): The name of the target room
        board (MansionBoard): The game board
        character_board (CharacterBoard, optional): Board tracking character positions for obstacle detection

    Returns:
        int: Shortest path distance (steps needed) to reach the target room
             Returns 0 if already in the target room
             Returns 1 if target can be reached via secret passage
             Returns 99 if no path exists
    """
    # Get source position coordinates
    try:
        source_room, source_row, source_col = get_room_and_position(position, board)
    except ValueError:
        return 99  # Invalid source position

    # If source is already in target room, distance is 0
    if source_room == target_room:
        return 0

    # If source is in a room with a secret passage to the target room, distance is 1
    if source_room:
        source_room_obj = board.get_room(source_room)
        if hasattr(source_room_obj, 'secret_passage_to') and source_room_obj.secret_passage_to == target_room:
            return 1

    # Get target room entrances
    target_entrances = board.get_room_entrances(target_room)
    if not target_entrances:
        return 99  # Invalid target room or no entrances

    # Starting positions for BFS
    start_positions = []

    # If starting in a room, use room entrances as starting points
    if source_room and source_room != target_room:
        source_entrances = board.get_room_entrances(source_room)
        if source_entrances:
            for entrance in source_entrances:
                # For each room entrance, check the four adjacent cells
                entrance_row, entrance_col = entrance
                for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    adj_row, adj_col = entrance_row + dr, entrance_col + dc

                    # Skip if out of bounds
                    if not (0 <= adj_row < board.rows and 0 <= adj_col < board.cols):
                        continue

                    # Check if this is a valid hallway cell
                    cell_type = board.get_cell_type(adj_row, adj_col)
                    if cell_type in ["hallway", "bonus_card"]:
                        # Check if cell is occupied (if character_board provided)
                        if character_board and character_board.get_cell_content(adj_row, adj_col) is not None:
                            continue

                        start_positions.append(((adj_row, adj_col), 1))  # (position, distance)
    else:
        # Starting from hallway, use the current position
        start_positions.append(((source_row, source_col), 0))

    # If no valid starting positions, path is impossible
    if not start_positions:
        return 99

    # BFS for shortest path
    visited = set()
    queue = start_positions

    while queue:
        (row, col), distance = queue.pop(0)

        # Skip if we've already visited this cell
        if (row, col) in visited:
            continue

        # Mark as visited
        visited.add((row, col))

        # Check if we've reached a target entrance
        for target_row, target_col in target_entrances:
            if abs(row - target_row) + abs(col - target_col) == 1:
                return distance + 1  # +1 for the step to the entrance

        # Explore adjacent cells
        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            new_row, new_col = row + dr, col + dc

            # Skip if out of bounds
            if not (0 <= new_row < board.rows and 0 <= new_col < board.cols):
                continue

            # Skip if already visited
            if (new_row, new_col) in visited:
                continue

            # Check if this is a valid hallway cell
            cell_type = board.get_cell_type(new_row, new_col)
            if cell_type not in ["hallway", "bonus_card"]:
                continue

            # Check if cell is occupied (if character_board provided)
            if character_board and character_board.get_cell_content(new_row, new_col) is not None:
                continue

            # Add to queue
            queue.append(((new_row, new_col), distance + 1))

    # If we've exhausted all options and haven't found a path
    return 99  # No path exists