import random
from Game.GameSetup import initialize_game
from Game.TurnManagement import process_turn, process_ai_turn
from Game.GameLogic import process_suggestion, process_accusation


class Game:
    """
    Main class representing the Clue game.
    """

    def __init__(self, num_human_players=1, num_ai_players=2):
        """Initialize the game."""
        # Initialize the boards, characters, and weapons
        self.mansion_board, self.character_board, self.characters, self.weapons = initialize_game()

        # Game state variables
        self.game_over = False
        self.winner = None
        self.current_player_idx = 0

        # Set up players
        self.setup_players(num_human_players, num_ai_players)

        # Create the secret envelope (the solution)
        self.setup_solution()

        # Deal cards to players
        self.deal_cards()

        # Lists of all game elements
        self.character_names = list(self.characters.keys())
        self.weapon_names = list(self.weapons.keys())
        self.room_names = list(self.mansion_board.room_dict.keys())

    def setup_players(self, num_human_players, num_ai_players):
        """Set up the players for the game."""
        from Player.Player import Player
        from Player.SimpleAIPlayer import SimpleAIPlayer
        from Player.SmarterAIPlayer import SmarterAIPlayer

        self.players = []
        player_id = 0

        # Create human players
        for _ in range(num_human_players):
            # Let the human player choose their character
            available_characters = [name for name in self.characters.keys()
                                    if name not in [p.character_name for p in self.players]]

            print("Available characters:")
            for i, name in enumerate(available_characters, 1):
                print(f"{i}. {name}")

            while True:
                try:
                    choice = int(input("Choose your character: "))
                    if 1 <= choice <= len(available_characters):
                        character_name = available_characters[choice - 1]
                        break
                    else:
                        print("Invalid choice. Please try again.")
                except ValueError:
                    print("Please enter a number.")

            player = Player(player_id, character_name)
            player.character = self.characters[character_name]
            self.players.append(player)
            player_id += 1

        # Ask for AI type if we have AI players
        ai_type = "simple"
        if num_ai_players > 0:
            print("\nChoose AI difficulty:")
            print("1. Simple AI (makes random but legal moves)")
            print("2. Smarter AI (uses advanced strategy and deduction)")

            while True:
                try:
                    ai_choice = int(input("Choose AI difficulty (1-2): "))
                    if ai_choice == 1:
                        ai_type = "simple"
                        break
                    elif ai_choice == 2:
                        ai_type = "smarter"
                        break
                    else:
                        print("Invalid choice. Please try again.")
                except ValueError:
                    print("Please enter a number.")

        # Create AI players
        for _ in range(num_ai_players):
            available_characters = [name for name in self.characters.keys()
                                    if name not in [p.character_name for p in self.players]]
            character_name = random.choice(available_characters)

            if ai_type == "simple":
                ai_player = SimpleAIPlayer(player_id, character_name)
            else:  # smarter
                ai_player = SmarterAIPlayer(player_id, character_name)

            ai_player.character = self.characters[character_name]
            self.players.append(ai_player)
            player_id += 1

        print("\nPlayers in the game:")
        for player in self.players:
            player_type = "Simple AI" if hasattr(player, 'is_ai') and player.is_ai and isinstance(player,
                                                                                                  SimpleAIPlayer) else \
                "Smarter AI" if hasattr(player, 'is_ai') and player.is_ai and isinstance(player,
                                                                                         SmarterAIPlayer) else "Human"
            print(f"{player.character_name} ({player_type})")

    def setup_solution(self):
        """Set up the solution (secret envelope)."""
        # Choose a random character, weapon, and room for the solution
        suspect = random.choice(list(self.characters.keys()))
        weapon = random.choice(list(self.weapons.keys()))
        room = random.choice(list(self.mansion_board.room_dict.keys()))

        self.solution = (suspect, weapon, room)

    def deal_cards(self):
        """Deal the remaining cards to the players."""
        # Create a deck of all cards except the solution
        suspects = [("suspect", c) for c in self.characters.keys() if c != self.solution[0]]
        weapons = [("weapon", w) for w in self.weapons.keys() if w != self.solution[1]]
        rooms = [("room", r) for r in self.mansion_board.room_dict.keys() if r != self.solution[2]]

        deck = suspects + weapons + rooms
        random.shuffle(deck)

        # Deal cards evenly to players
        for i, card in enumerate(deck):
            player_idx = i % len(self.players)
            self.players[player_idx].add_card(card)

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
                process_ai_turn(self, current_player)
            else:
                process_turn(self, current_player)

            # Move to next player
            self.current_player_idx = (self.current_player_idx + 1) % len(self.players)

            input("\nPress Enter to continue to the next player's turn...")

        # Game is over, show the result
        if self.winner:
            print(f"\nGame over! {self.winner.character_name} wins!")
        else:
            print("\nGame over! No one was able to solve the mystery.")

    def end_game(self, winner=None):
        """End the game."""
        self.game_over = True
        self.winner = winner