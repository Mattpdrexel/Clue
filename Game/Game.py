# Game/Game.py
from Game.GameSetup import initialize_game, print_game_state
from Game.GameLogic import process_suggestion, process_accusation
from Player.Player import Player
from Data.Constants import CHARACTERS, WEAPONS, SUSPECT_ROOMS
import random


class Game:
    def __init__(self, num_human_players=3, num_ai_players=0):
        """
        Initialize a new Clue game.

        Args:
            num_human_players (int): Number of human players (default: 3)
            num_ai_players (int): Number of AI players (default: 0)
        """
        # Initialize game components
        self.mansion_board, self.character_board, self.characters, self.weapons = initialize_game()

        # Create solution envelope
        self.solution = self.create_solution_envelope()

        # Create players
        self.players = self.create_players(num_human_players, num_ai_players)

        # Distribute remaining cards
        self.distribute_cards()

        # Game state
        self.current_player_idx = 0
        self.game_over = False
        self.winner = None

    def create_solution_envelope(self):
        """Create the solution envelope by selecting one card of each type."""
        suspect = random.choice(CHARACTERS)
        weapon = random.choice(WEAPONS)
        room = random.choice(SUSPECT_ROOMS)

        return (room, suspect, weapon)

    def create_players(self, num_players, num_ai_players):
        """Create and return a list of player objects."""
        players = []

        # Create human players
        for i in range(num_players):
            player_id = i + 1
            character = CHARACTERS[i]
            players.append(Player(player_id, character))

        # TODO: Create AI players
        # This will be implemented when AI players are added

        return players

    def distribute_cards(self):
        """Distribute remaining cards to players."""
        # Create a deck of all cards except those in the solution
        room, suspect, weapon = self.solution
        deck = []

        for character in CHARACTERS:
            if character != suspect:
                deck.append(("suspect", character))

        for item in WEAPONS:
            if item != weapon:
                deck.append(("weapon", item))

        for location in SUSPECT_ROOMS:
            if location != room:
                deck.append(("room", location))

        # Shuffle the deck
        random.shuffle(deck)

        # Deal cards evenly to players
        num_players = len(self.players)
        for i, card in enumerate(deck):
            player_idx = i % num_players
            self.players[player_idx].add_card(card)

    def next_player(self):
        """Move to the next player and return that player."""
        self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
        return self.players[self.current_player_idx]

    def roll_die(self):
        """Roll a die and return the result."""
        return random.randint(1, 6)

    # Game/Game.py - play_game method update
    def play_game(self):
        """Main game loop."""
        print("\nStarting the game of Clue!")

        while not self.game_over:
            # Get current player
            current_player = self.players[self.current_player_idx]

            # Skip eliminated players
            if current_player.eliminated:
                print(f"\n{current_player.character_name}'s turn is skipped (eliminated).")
                self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
                continue

            # Process turn based on player type
            if hasattr(current_player, 'is_ai') and current_player.is_ai:
                self.process_ai_turn(current_player)
            else:
                self.process_turn(current_player)

            # Move to next player
            self.current_player_idx = (self.current_player_idx + 1) % len(self.players)

            input("\nPress Enter to continue to the next player's turn...")

        # Game is over, show the result
        if self.winner:
            print(f"\nGame over! {self.winner.character_name} wins!")
        else:
            print("\nGame over! No one was able to solve the mystery.")

    # TODO: player cannot choose to skip turn arbitrarily, need to fix this
    # Game/Game.py - handle_movement method update
    def handle_movement(self, player, available_moves):
        """Handle player movement."""
        if not available_moves:
            print("No moves available. Turn ends.")
            return None

        # Display available moves
        print("Available moves:")
        for i, move in enumerate(available_moves):
            print(f"{i + 1}. {move}")

        # Get player's choice
        choice = input("Enter the number of your move choice (or 0 to skip): ")
        try:
            choice = int(choice)
            if choice == 0:
                print("Skipping movement.")
                return None

            if 1 <= choice <= len(available_moves):
                new_position = available_moves[choice - 1]

                # If the choice is a room name string (staying in current room)
                if isinstance(new_position, str):
                    print(f"Staying in the {new_position}")
                    return new_position

                # Normal movement to a new position
                player.move(new_position)

                # Update character_board if moving to a specific position
                if isinstance(new_position, tuple):
                    if len(new_position) == 2:
                        row, col = new_position
                        self.character_board.move(player.character_name, row, col)

                        # Check if this is a room entrance position
                        new_room = self.mansion_board.get_room_name_at_position(row, col)
                        if new_room:
                            print(f"Moved to {new_position} (entering {new_room})")
                            return new_room
                        else:
                            print(f"Moved to {new_position}")
                    elif len(new_position) == 3:
                        _, row, col = new_position
                        self.character_board.move(player.character_name, row, col)
                        print(f"Moved to {new_position}")

                        # If it's a 3-tuple with room information
                        return new_position[0]  # Return the room name
                else:
                    print(f"Moved to {new_position}")

                return None
            else:
                print("Invalid choice. Skipping movement.")
                return None
        except ValueError:
            print("Invalid input. Skipping movement.")
            return None

    # Game/Game.py - handle_suggestion method update
    # Game/Game.py - handle_suggestion method update
    def handle_suggestion(self, player, room, required=False):
        """
        Handle player suggestion.

        Args:
            player: Player making the suggestion
            room: Room where the suggestion is being made
            required: Whether a suggestion is mandatory
        """
        print(f"\nYou are in the {room}.")

        if not required:
            make_suggestion = input("Would you like to make a suggestion? (y/n): ").lower()
            if make_suggestion != 'y':
                return
        else:
            print("You must make a suggestion after entering a new room.")

        # Get suggestion details
        print("\nAvailable suspects:")
        for i, suspect in enumerate(CHARACTERS):
            print(f"{i + 1}. {suspect}")

        while True:
            try:
                suspect_choice = int(input("Choose a suspect (number): ")) - 1
                if 0 <= suspect_choice < len(CHARACTERS):
                    suspect = CHARACTERS[suspect_choice]
                    break
                else:
                    print("Invalid choice. Please select a valid number.")
            except ValueError:
                print("Please enter a valid number.")

        print("\nAvailable weapons:")
        for i, weapon in enumerate(WEAPONS):
            print(f"{i + 1}. {weapon}")

        while True:
            try:
                weapon_choice = int(input("Choose a weapon (number): ")) - 1
                if 0 <= weapon_choice < len(WEAPONS):
                    weapon = WEAPONS[weapon_choice]
                    break
                else:
                    print("Invalid choice. Please select a valid number.")
            except ValueError:
                print("Please enter a valid number.")

        # Process the suggestion
        suggestion = player.make_suggestion(room, suspect, weapon)
        print(f"\n{player.character_name} suggests: {suspect} in the {room} with the {weapon}")

        # Move the suspected character to this room
        if suspect in self.characters:
            suspected_character = self.characters[suspect]
            old_position = suspected_character.position

            # Move the character to the suggesting room
            suspected_character.move_to(room)

            # Update character_board if needed
            if isinstance(old_position, tuple) and len(old_position) == 2:
                old_row, old_col = old_position
                self.character_board.grid[old_row][old_col] = None

            # Place character in the room on the character_board
            room_cells = self.mansion_board.get_room_cells(room)
            if room_cells:
                # Find an empty cell in the room
                for cell_row, cell_col in room_cells:
                    if self.character_board.get_cell_content(cell_row, cell_col) is None:
                        self.character_board.place(suspect, cell_row, cell_col)
                        break

            print(f"Moved {suspect} to the {room}")

        # Move the weapon to this room
        if weapon in self.weapons:
            self.weapons[weapon].move_to(room)
            print(f"Moved the {weapon} to the {room}")

        # Process through game logic
        responding_player, revealed_card = process_suggestion(self, player, room, suspect, weapon)

        if responding_player:
            print(f"{responding_player.character_name} showed a card to {player.character_name}")
        else:
            print("No one could disprove the suggestion!")

    def handle_accusation(self, player):
        """
        Handle player accusation.

        Args:
            player: Player making the accusation
        """
        # Check if the player is in the Clue room
        current_position = player.character.position
        in_clue_room = False

        if isinstance(current_position, str) and current_position == "Clue":
            in_clue_room = True
        elif isinstance(current_position, tuple) and len(current_position) == 3 and current_position[0] == "Clue":
            in_clue_room = True

        if not in_clue_room:
            print("\nYou must be in the Clue room to make an accusation.")
            return

        # Ask if player wants to make an accusation
        make_accusation = input("\nWould you like to make an accusation? (y/n): ").lower()
        if make_accusation != 'y':
            return

        # Get accusation details
        print("\nAvailable suspects:")
        for i, suspect in enumerate(CHARACTERS):
            print(f"{i + 1}. {suspect}")

        while True:
            try:
                suspect_choice = int(input("Choose a suspect (number): ")) - 1
                if 0 <= suspect_choice < len(CHARACTERS):
                    suspect = CHARACTERS[suspect_choice]
                    break
                else:
                    print("Invalid choice. Please select a valid number.")
            except ValueError:
                print("Please enter a valid number.")

        print("\nAvailable weapons:")
        for i, weapon in enumerate(WEAPONS):
            print(f"{i + 1}. {weapon}")

        while True:
            try:
                weapon_choice = int(input("Choose a weapon (number): ")) - 1
                if 0 <= weapon_choice < len(WEAPONS):
                    weapon = WEAPONS[weapon_choice]
                    break
                else:
                    print("Invalid choice. Please select a valid number.")
            except ValueError:
                print("Please enter a valid number.")

        print("\nAvailable rooms:")
        for i, room in enumerate(SUSPECT_ROOMS):
            print(f"{i + 1}. {room}")

        while True:
            try:
                room_choice = int(input("Choose a room (number): ")) - 1
                if 0 <= room_choice < len(SUSPECT_ROOMS):
                    room = SUSPECT_ROOMS[room_choice]
                    break
                else:
                    print("Invalid choice. Please select a valid number.")
            except ValueError:
                print("Please enter a valid number.")

        # Process the accusation
        accusation = player.make_accusation(room, suspect, weapon)
        print(f"\n{player.character_name} accuses: {suspect} in the {room} with the {weapon}")

        # Check if accusation is correct
        correct = self.check_accusation(accusation)

        if correct:
            # Player wins
            print(f"\nCORRECT! {player.character_name} has solved the mystery!")
            self.game_over = True
            self.winner = player
        else:
            # Player is eliminated from making moves
            print(f"\nINCORRECT! {player.character_name} is eliminated from making moves.")
            print("You can still participate by showing cards when needed, but your turns will be skipped.")
            player.eliminated = True

    def check_accusation(self, accusation):
        """
        Check if an accusation is correct.

        Args:
            accusation: Tuple of (room, suspect, weapon)

        Returns:
            bool: True if the accusation is correct
        """
        room, suspect, weapon = accusation
        solution_room, solution_suspect, solution_weapon = self.solution

        return (room == solution_room and
                suspect == solution_suspect and
                weapon == solution_weapon)

    def end_game(self, winner=None):
        """End the game with an optional winner."""
        self.game_over = True
        self.winner = winner

    # Game/Game.py - process_turn method update
    def process_turn(self, player):
        """Process a single player's turn."""
        print(f"\n===== {player.character_name}'s Turn =====")

        # Get current location before movement
        original_position = player.character.position
        original_room = None

        if isinstance(original_position, str):
            original_room = original_position
        elif isinstance(original_position, tuple) and len(original_position) == 3:
            original_room = original_position[0]

        # Roll the die
        die_roll = self.roll_die()
        print(f"{player.character_name} rolled a {die_roll}")

        # Get available moves
        available_moves = player.get_available_moves(self.mansion_board, self.character_board, die_roll)

        # Add option to stay in current room if already in a room
        if original_room:
            available_moves.append(original_room)
            print(f"You can choose to stay in the {original_room}.")

        # Handle player movement
        new_room = self.handle_movement(player, available_moves)

        # Check if player is in a room
        current_position = player.character.position
        current_room = None

        if isinstance(current_position, str):
            current_room = current_position
        elif isinstance(current_position, tuple) and len(current_position) == 3:
            current_room = current_position[0]

        # If player entered a new room, they MUST make a suggestion
        if current_room and current_room != original_room:
            print(f"\nYou have entered the {current_room}. You must make a suggestion.")
            self.handle_suggestion(player, current_room, required=True)
        # If player stayed in their original room, suggestion is optional
        elif current_room:
            self.handle_suggestion(player, current_room, required=False)

        # Player can make an accusation if they want
        self.handle_accusation(player)

    # Game/Game.py - process_ai_turn method
    def process_ai_turn(self, ai_player):
        """Process a turn for an AI player."""
        print(f"\n===== {ai_player.character_name}'s Turn (AI) =====")

        # Check if the AI is in the Clue room and wants to make an accusation
        current_position = ai_player.character.position
        in_clue_room = False

        if isinstance(current_position, str) and current_position == "Clue":
            in_clue_room = True
        elif isinstance(current_position, tuple) and len(current_position) == 3 and current_position[0] == "Clue":
            in_clue_room = True

        # Roll the die
        die_roll = self.roll_die()
        print(f"{ai_player.character_name} rolled a {die_roll}")

        # Get available moves
        available_moves = ai_player.get_available_moves(self.mansion_board, self.character_board, die_roll)

        # Check if the Clue room is reachable and AI wants to make an accusation
        clue_room_reachable = False
        for move in available_moves:
            # Check if this move can get to the Clue room
            if isinstance(move, str) and move == "Clue":
                clue_room_reachable = True
                break
            elif isinstance(move, tuple) and len(move) == 3 and move[0] == "Clue":
                clue_room_reachable = True
                break

        # If AI is confident and can reach the Clue room, prioritize going there for accusation
        solution_candidates = ai_player.get_solution_candidates()
        confident_in_solution = (
                len(solution_candidates["suspects"]) == 1 and
                len(solution_candidates["weapons"]) == 1 and
                len(solution_candidates["rooms"]) == 1
        )

        # AI decision making
        if in_clue_room and confident_in_solution:
            # Already in Clue room and confident, make accusation
            made_accusation = ai_player.handle_accusation(self)

            if made_accusation:
                # Check if accusation is correct
                suspect = list(solution_candidates["suspects"])[0]
                weapon = list(solution_candidates["weapons"])[0]
                room = list(solution_candidates["rooms"])[0]
                accusation = (room, suspect, weapon)

                correct = self.check_accusation(accusation)

                if correct:
                    # AI wins
                    print(f"\nCORRECT! {ai_player.character_name} has solved the mystery!")
                    self.game_over = True
                    self.winner = ai_player
                else:
                    # AI is eliminated from making moves
                    print(f"\nINCORRECT! {ai_player.character_name} is eliminated from making moves.")
                    ai_player.eliminated = True

                return

        elif clue_room_reachable and confident_in_solution:
            # Can reach Clue room and confident, move there
            for move in available_moves:
                if (isinstance(move, str) and move == "Clue") or (
                        isinstance(move, tuple) and len(move) == 3 and move[0] == "Clue"):
                    ai_player.move(move)
                    print(f"{ai_player.character_name} moves to the Clue room to make an accusation")

                    # Update board position
                    if isinstance(move, tuple) and len(move) == 3:
                        _, row, col = move
                        self.character_board.move(ai_player.character_name, row, col)

                    # Make accusation immediately
                    made_accusation = ai_player.handle_accusation(self)

                    if made_accusation:
                        # Check if accusation is correct
                        suspect = list(solution_candidates["suspects"])[0]
                        weapon = list(solution_candidates["weapons"])[0]
                        room = list(solution_candidates["rooms"])[0]
                        accusation = (room, suspect, weapon)

                        correct = self.check_accusation(accusation)

                        if correct:
                            # AI wins
                            print(f"\nCORRECT! {ai_player.character_name} has solved the mystery!")
                            self.game_over = True
                            self.winner = ai_player
                        else:
                            # AI is eliminated from making moves
                            print(f"\nINCORRECT! {ai_player.character_name} is eliminated from making moves.")
                            ai_player.eliminated = True

                    return

        # Regular AI turn if not making an accusation
        # AI chooses move and makes suggestion if in a room
        chosen_move = ai_player.make_move(self, available_moves, die_roll)

        if chosen_move:
            ai_player.move(chosen_move)

            # Update character_board if moving to a specific position
            if isinstance(chosen_move, tuple):
                if len(chosen_move) == 2:
                    row, col = chosen_move
                    self.character_board.move(ai_player.character_name, row, col)
                elif len(chosen_move) == 3:
                    _, row, col = chosen_move
                    self.character_board.move(ai_player.character_name, row, col)

            # If AI moved to a room, make a suggestion
            current_room = None
            current_position = ai_player.character.position

            if isinstance(current_position, str):
                current_room = current_position
            elif isinstance(current_position, tuple) and len(current_position) == 3:
                current_room = current_position[0]

            if current_room and current_room in SUSPECT_ROOMS:
                suggestion = ai_player.choose_suggestion(current_room)
                room, suspect, weapon = suggestion

                print(f"{ai_player.character_name} suggests: {suspect} in the {room} with the {weapon}")

                # Move the suspected character to this room
                if suspect in self.characters:
                    suspected_character = self.characters[suspect]
                    old_position = suspected_character.position

                    # Move the character to the suggesting room
                    suspected_character.move_to(room)

                    # Update character_board if needed
                    if isinstance(old_position, tuple) and len(old_position) == 2:
                        old_row, old_col = old_position
                        self.character_board.grid[old_row][old_col] = None

                    # Place character in the room on the character_board
                    room_cells = self.mansion_board.get_room_cells(room)
                    if room_cells:
                        # Find an empty cell in the room
                        for cell_row, cell_col in room_cells:
                            if self.character_board.get_cell_content(cell_row, cell_col) is None:
                                self.character_board.place(suspect, cell_row, cell_col)
                                break

                    print(f"Moved {suspect} to the {room}")

                # Move the weapon to this room
                if weapon in self.weapons:
                    self.weapons[weapon].move_to(room)
                    print(f"Moved the {weapon} to the {room}")

                # Process through game logic
                responding_player, revealed_card = process_suggestion(self, ai_player, room, suspect, weapon)

                if responding_player:
                    print(f"{responding_player.character_name} showed a card to {ai_player.character_name}")
                else:
                    print("No one could disprove the suggestion!")

    # Game/Game.py - play_game method update
    # Game/Game.py - play_game method update
    def play_game(self):
        """Main game loop."""
        print("\nStarting the game of Clue!")

        while not self.game_over:
            # Get current player
            current_player = self.players[self.current_player_idx]

            # Skip eliminated players
            if current_player.eliminated:
                print(f"\n{current_player.character_name}'s turn is skipped (eliminated).")
                self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
                continue

            # Process turn based on player type
            if hasattr(current_player, 'is_ai') and current_player.is_ai:
                self.process_ai_turn(current_player)
            else:
                self.process_turn(current_player)

            # Move to next player
            self.current_player_idx = (self.current_player_idx + 1) % len(self.players)

            input("\nPress Enter to continue to the next player's turn...")

        # Game is over, show the result
        if self.winner:
            print(f"\nGame over! {self.winner.character_name} wins!")
        else:
            print("\nGame over! No one was able to solve the mystery.")