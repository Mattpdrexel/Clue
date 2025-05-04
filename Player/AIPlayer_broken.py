from Player.Player import Player
import random
import itertools
from collections import deque
from Data.Constants import ROOMS, SUSPECT_ROOMS, WEAPONS

class AIPlayer(Player):
    def __init__(self, player_id: int, character_name: str):
        super().__init__(player_id, character_name)
        self.is_ai = True
        self._must_exit_next_turn = False
        self.last_positions = deque(maxlen=5)
        self._visited_rooms = set()
        self._previous_suggestions = set()
        self.suggestion_results = {}
        self.current_target_suggestion = None
        self.eliminated_suspects = set()
        self.eliminated_weapons = set()
        self.eliminated_rooms = set()
        self._turn_counter = 0

    def _room_name(self, move):
        """Return room name from a move (room‑token or (room,r,c) tuple)."""
        if isinstance(move, str):
            return move
        if isinstance(move, tuple) and len(move) == 3:
            return move[0]
        return None

    def make_move(self, game, available_moves, dice_roll):
        """Choose where to move this turn."""
        self._turn_counter += 1

        # Simple random choice for movement
        return random.choice(available_moves) if available_moves else None

    def should_make_suggestion(self, game, room):
        """Determine if the AI should make a suggestion while staying in a room."""
        return True  # Always make suggestions when possible

    def handle_suggestion(self, game, room):
        """Make a suggestion when in a room."""
        self._must_exit_next_turn = True
        self._visited_rooms.add(room)

        # Get all available suspects and weapons
        suspects = set(SUSPECT_ROOMS)
        weapons = set(WEAPONS)

        # Remove eliminated options
        suspects = suspects - self.eliminated_suspects
        weapons = weapons - self.eliminated_weapons

        # Choose random suspect and weapon
        suspect = random.choice(list(suspects)) if suspects else random.choice(game.character_names)
        weapon = random.choice(list(weapons)) if weapons else random.choice(game.weapon_names)

        suggestion = (room, suspect, weapon)
        self._previous_suggestions.add(suggestion)
        self.current_target_suggestion = suggestion

        return suggestion

    def should_make_accusation(self, game):
        """Determine if AI should make an accusation."""
        if not self.knowledge:
            return False

        # Only accuse if we know the solution
        return self.knowledge.is_solution_known()

    def make_accusation(self, game):
        """Make an accusation with our best guess."""
        if not self.knowledge or not self.knowledge.is_solution_known():
            return None

        sol = self.knowledge.possible_solution
        room = next(iter(sol["rooms"]))
        suspect = next(iter(sol["suspects"]))
        weapon = next(iter(sol["weapons"]))

        return (room, suspect, weapon)

    def update_knowledge_from_suggestion(self, suggesting_player, suggestion, responding_player, revealed_card=None):
        """Update knowledge based on suggestion responses."""
        # Call parent method to update knowledge
        super().update_knowledge_from_suggestion(
            suggesting_player, suggestion, responding_player, revealed_card
        )

        room, suspect, weapon = suggestion

        # If no one responded, these cards might be in the solution
        if responding_player is None:
            if self.knowledge:
                if room not in self.eliminated_rooms:
                    self.knowledge.possible_solution["rooms"].add(room)
                if suspect not in self.eliminated_suspects:
                    self.knowledge.possible_solution["suspects"].add(suspect)
                if weapon not in self.eliminated_weapons:
                    self.knowledge.possible_solution["weapons"].add(weapon)

        # If a card was revealed, we know it's not in the solution
        elif revealed_card is not None:
            card_type, card_name = revealed_card
            if card_type == "room":
                self.eliminated_rooms.add(card_name)
                if self.knowledge and card_name in self.knowledge.possible_solution["rooms"]:
                    self.knowledge.possible_solution["rooms"].remove(card_name)
            elif card_type == "suspect":
                self.eliminated_suspects.add(card_name)
                if self.knowledge and card_name in self.knowledge.possible_solution["suspects"]:
                    self.knowledge.possible_solution["suspects"].remove(card_name)
            elif card_type == "weapon":
                self.eliminated_weapons.add(card_name)
                if self.knowledge and card_name in self.knowledge.possible_solution["weapons"]:
                    self.knowledge.possible_solution["weapons"].remove(card_name)

    def handle_accusation(self, game):
        """Handle making an accusation if the AI decides to make one."""
        from Game.GameLogic import process_accusation

        # Check if the AI wants to make an accusation
        if self.should_make_accusation(game):
            print(f"\n❗ {self.character_name} is making an accusation!")

            # Get the accusation from the AI
            accusation = self.make_accusation(game)

            if accusation:
                room, suspect, weapon = accusation

                # Display the accusation clearly
                print(
                    f"\n🔎 ACCUSATION: {self.character_name} accuses {suspect} of committing the murder in the {room} with the {weapon}")

                # Process the accusation
                is_correct = process_accusation(game, self, suspect, weapon, room)

                if is_correct:
                    print(f"\n✅ {self.character_name} made the correct accusation and wins the game!")
                    game.end_game(winner=self)
                else:
                    print(f"\n❌ {self.character_name} made an incorrect accusation and is eliminated.")
                    self.eliminated = True
                    self.made_wrong_accusation = True

                    # Check if all players are eliminated
                    if all(p.eliminated for p in game.players):
                        print("\nAll players have been eliminated. Game over!")
                        game.end_game()

    def print_knowledge(self):
        """Print the AI's current knowledge in a readable format."""
        if self.knowledge is None:
            print(f"\n{self.character_name}'s Knowledge: Not initialized")
            return

        print(f"\n=== {self.character_name}'s Knowledge (Turn {self._turn_counter}) ===")

        # Print current target suggestion
        if self.current_target_suggestion:
            room, suspect, weapon = self.current_target_suggestion
            print(f"\nCurrent Target Suggestion: {suspect} in the {room} with the {weapon}")

        # Print deduction confidence
        sol = self.knowledge.possible_solution
        suspect_count = len(sol["suspects"])
        weapon_count = len(sol["weapons"])
        room_count = len(sol["rooms"])
        total_count = suspect_count + weapon_count + room_count


