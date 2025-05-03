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

    def process_turn(self, player):
        """Process a single player's turn."""
        print(f"\n===== {player.character_name}'s Turn =====")

        # Roll the die
        die_roll = self.roll_die()
        print(f"{player.character_name} rolled a {die_roll}")

        # Get available moves
        available_moves = player.get_available_moves(self.mansion_board, self.character_board, die_roll)

        # Handle player movement
        self.handle_movement(player, available_moves)

        # Check if player is in a room
        current_position = player.character.position
        if isinstance(current_position, str):
            # Player is in a room and can make a suggestion
            self.handle_suggestion(player, current_position)

            # Player can make an accusation if they want
            self.handle_accusation(player)

    def handle_movement(self, player, available_moves):
        """Handle player movement."""
        if not available_moves:
            print("No moves available. Turn ends.")
            return

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
                return
            if 1 <= choice <= len(available_moves):
                new_position = available_moves[choice - 1]
                player.move(new_position)

                # Update character_board if moving to a specific position
                if isinstance(new_position, tuple) and len(new_position) == 2:
                    row, col = new_position
                    self.character_board.move(player.character_name, row, col)

                print(f"Moved to {new_position}")
            else:
                print("Invalid choice. Skipping movement.")
        except ValueError:
            print("Invalid input. Skipping movement.")

    # Game/Game.py - handle_suggestion method update
    def handle_suggestion(self, player, room):
        """Handle player suggestion."""
        print(f"\nYou are in the {room}. You can make a suggestion.")
        make_suggestion = input("Would you like to make a suggestion? (y/n): ").lower()

        if make_suggestion != 'y':
            return

        # Get suggestion details
        print("\nAvailable suspects:")
        for i, suspect in enumerate(CHARACTERS):
            print(f"{i + 1}. {suspect}")
        suspect_choice = int(input("Choose a suspect (number): ")) - 1
        suspect = CHARACTERS[suspect_choice]

        print("\nAvailable weapons:")
        for i, weapon in enumerate(WEAPONS):
            print(f"{i + 1}. {weapon}")
        weapon_choice = int(input("Choose a weapon (number): ")) - 1
        weapon = WEAPONS[weapon_choice]

        # Process the suggestion
        suggestion = (room, suspect, weapon)
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
        """Handle player accusation."""
        make_accusation = input("\nWould you like to make an accusation? (y/n): ").lower()

        if make_accusation != 'y':
            return

        # Get accusation details
        print("\nAvailable rooms:")
        for i, room in enumerate(SUSPECT_ROOMS):
            print(f"{i + 1}. {room}")
        room_choice = int(input("Choose a room (number): ")) - 1
        room = SUSPECT_ROOMS[room_choice]

        print("\nAvailable suspects:")
        for i, suspect in enumerate(CHARACTERS):
            print(f"{i + 1}. {suspect}")
        suspect_choice = int(input("Choose a suspect (number): ")) - 1
        suspect = CHARACTERS[suspect_choice]

        print("\nAvailable weapons:")
        for i, weapon in enumerate(WEAPONS):
            print(f"{i + 1}. {weapon}")
        weapon_choice = int(input("Choose a weapon (number): ")) - 1
        weapon = WEAPONS[weapon_choice]

        # Process the accusation
        print(f"\n{player.character_name} accuses: {suspect} in the {room} with the {weapon}")

        is_correct = process_accusation(self, player, room, suspect, weapon)

        if is_correct:
            print(f"CORRECT! {player.character_name} wins the game!")
            self.game_over = True
            self.winner = player
        else:
            print(f"INCORRECT! {player.character_name} is out of the game but continues to refute suggestions.")

    def end_game(self, winner=None):
        """End the game with an optional winner."""
        self.game_over = True
        self.winner = winner

    def play_game(self):
        """Main game loop."""
        print("Starting Clue game!")
        print_game_state(self.mansion_board, self.character_board, self.characters)

        # Print solution (for debugging - remove in production)
        print(f"Solution: {self.solution}")

        # Main game loop
        while not self.game_over:
            current_player = self.players[self.current_player_idx]
            self.process_turn(current_player)

            if self.game_over:
                break

            self.next_player()

            # Prompt to continue
            input("\nPress Enter to continue to next player's turn...")

        # Game over
        if self.winner:
            print(f"\nGame over! {self.winner.character_name} wins!")
        else:
            print("\nGame over! No winner.")