# Player/AIPlayer.py
from Player.Player import Player
import random
from typing import List, Tuple, Set, Dict
from collections import deque, defaultdict
import itertools
import gc
from Game.Game import Game

class AIPlayer(Player):
    """An AI‑controlled Clue player powered by PlayerKnowledge."""

    # ------------------------------------------------------------------ init
    def __init__(self, player_id: int, character_name: str):
        super().__init__(player_id, character_name)
        self.is_ai: bool = True

        # --- movement bookkeeping -------------------------------------
        self._must_exit_next_turn: bool = False  # we suggested last turn
        self.last_positions = deque(maxlen=5)  # for loop avoidance
        self._visited_rooms: Set[str] = set()

        # --- suggestion bookkeeping -----------------------------------
        self._previous_suggestions: Set[Tuple[str, str, str]] = set()
        self.suggestion_results: Dict[Tuple[str, str, str], Dict] = {}
        self.current_target_suggestion = None

        # --- systematic suggestion tracking ---------------------------
        # Keep track of all possible combinations we can try for each room
        self.room_suggestion_space: Dict[str, List[Tuple[str, str]]] = {}
        # Track which cards we've eliminated
        self.eliminated_suspects: Set[str] = set()
        self.eliminated_weapons: Set[str] = set()
        self.eliminated_rooms: Set[str] = set()

        # --- pacing ----------------------------------------------------
        self._turn_counter: int = 0

    # -------------------------------------------------- helper utilities
    @staticmethod
    def _room_name(move):
        """Return room name from a move (room‑token or (room,r,c) tuple)."""
        if isinstance(move, str):
            return move
        if isinstance(move, tuple) and len(move) == 3:
            return move[0]
        return None

    def initialize_suggestion_space(self, game):
        """Initialize the space of all possible suggestions for each room."""
        # For each room, create a list of all possible (suspect, weapon) combinations
        all_suspects = set(game.character_names)
        all_weapons = set(game.weapon_names)
        all_rooms = set(game.room_names)

        # Remove Clue room from potential suggestions
        if "Clue" in all_rooms:
            all_rooms.remove("Clue")

        # Create product of all suspects and weapons for each room
        for room in all_rooms:
            self.room_suggestion_space[room] = list(itertools.product(all_suspects, all_weapons))
            # Shuffle to avoid deterministic behavior
            random.shuffle(self.room_suggestion_space[room])

    # ----------------------------------------------- knowledge display
    # Player/AIPlayer.py (modify the print_knowledge method)

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

        # Display suggestion stats
        if self._previous_suggestions:
            print(f"Suggestions Made: {len(self._previous_suggestions)}")

            # Check for remaining suggestion combinations in current room
            if self.character and isinstance(self.character.position, str):
                current_room = self.character.position
                if current_room in self.room_suggestion_space:
                    remaining = len(self.room_suggestion_space[current_room])
                    print(f"Remaining combinations in {current_room}: {remaining}")

        # Print deduction confidence
        sol = self.knowledge.possible_solution
        suspect_count = len(sol["suspects"])
        weapon_count = len(sol["weapons"])
        room_count = len(sol["rooms"])
        total_count = suspect_count + weapon_count + room_count

        confidence_level = "Unknown"
        if total_count <= 3:
            confidence_level = "Very High"
        elif total_count <= 6:
            confidence_level = "High"
        elif total_count <= 9:
            confidence_level = "Medium"
        elif total_count <= 12:
            confidence_level = "Low"
        else:
            confidence_level = "Very Low"

        print(f"Solution Confidence: {confidence_level} ({total_count} possibilities)")

        # Print accusation readiness
        ready_to_accuse = self._ready_to_accuse()
        print(f"Ready to Accuse: {'Yes' if ready_to_accuse else 'No'}")

        # Get the game instance and update the scoresheet if available
        game = self._get_game_instance()
        if game:
            game.update_and_display_scoresheets()

    def _get_game_instance(self):
        """Helper method to get the game instance."""
        # This is a bit of a hack since we don't have direct access to the game instance
        # In a real implementation, the game would be passed to the player or tracked
        import sys
        for obj in gc.get_objects():
            if isinstance(obj, Game):
                return obj
        return None
    # --------------------------------------------------------- API hooks
    def make_move(self, game, available_moves: List, dice_roll: int):
        """Choose where to move this turn."""
        self._turn_counter += 1

        # Initialize suggestion space if not yet done
        if not self.room_suggestion_space and game:
            self.initialize_suggestion_space(game)

        # Update our target suggestion
        self.update_target_suggestion(game)

        # ---------------------------------------------------------------- exit
        if self._must_exit_next_turn:
            self._must_exit_next_turn = False
            corridor_moves = [m for m in available_moves
                              if not isinstance(m, str) and not
                              (isinstance(m, tuple) and len(m) == 3)]
            if corridor_moves:
                return random.choice(corridor_moves)
            # fall‑through if no corridor reachable with this die roll

        # ------------------------------------------------------- classify moves
        room_moves = [m for m in available_moves
                      if isinstance(m, str) or (isinstance(m, tuple) and len(m) == 3)]
        corridor_moves = [m for m in available_moves if m not in room_moves]

        # ------------------------------------------------------- accusation?
        # Check if we know the solution and Clue room is available
        solution_known = (self.knowledge is not None and
                          len(self.knowledge.possible_solution["suspects"]) == 1 and
                          len(self.knowledge.possible_solution["weapons"]) == 1 and
                          len(self.knowledge.possible_solution["rooms"]) == 1)

        if solution_known and room_moves:
            clue_moves = [m for m in room_moves if self._room_name(m) == "Clue"]
            if clue_moves:
                return clue_moves[0]

        # ------------------------------------------------------- pick a room
        if room_moves:
            # Get rooms that are still in the possible solution
            solution_rooms = set()
            if self.knowledge is not None:
                solution_rooms = self.knowledge.possible_solution["rooms"]

            # 1. Check for rooms with untested suggestions
            rooms_with_untested = []
            for m in room_moves:
                room_name = self._room_name(m)
                if (room_name in self.room_suggestion_space and
                        self.room_suggestion_space[room_name]):
                    rooms_with_untested.append(m)

            # 2. The room from our current target suggestion
            if self.current_target_suggestion:
                target_room = self.current_target_suggestion[2]  # room is 3rd element
                target_moves = [m for m in room_moves if self._room_name(m) == target_room]
                if target_moves:
                    move = random.choice(target_moves)
                    if isinstance(move, tuple) and len(move) == 2:  # corridor pathing
                        self.last_positions.append(move)
                    return move

            # 3. Prioritize rooms with untested suggestions that are in possible solution
            untested_in_solution = [m for m in rooms_with_untested
                                    if self._room_name(m) in solution_rooms]
            if untested_in_solution:
                move = random.choice(untested_in_solution)
                if isinstance(move, tuple) and len(move) == 2:  # corridor pathing
                    self.last_positions.append(move)
                return move

            # 4. Any room with untested suggestions
            if rooms_with_untested:
                move = random.choice(rooms_with_untested)
                if isinstance(move, tuple) and len(move) == 2:  # corridor pathing
                    self.last_positions.append(move)
                return move

            # 5. Rooms that are still in the possible solution and we haven't visited
            priority_rooms = [m for m in room_moves
                              if self._room_name(m) in solution_rooms and
                              self._room_name(m) not in self._visited_rooms and
                              self._room_name(m) != "Clue"]

            # 6. Rooms that are still in the possible solution (even if visited)
            solution_room_moves = [m for m in room_moves
                                   if self._room_name(m) in solution_rooms and
                                   self._room_name(m) != "Clue"]

            # 7. Rooms we haven't visited (except Clue)
            unseen = [m for m in room_moves
                      if self._room_name(m) not in self._visited_rooms and
                      self._room_name(m) != "Clue"]

            # 8. Anything else (but avoid immediate back‑tracking)
            recent_positions = list(self.last_positions)[-2:] if len(self.last_positions) >= 2 else []
            fallback = [m for m in room_moves if m not in recent_positions]

            # Try each category in order of priority
            for choices in (priority_rooms, solution_room_moves, unseen, fallback):
                if choices:
                    move = random.choice(choices)
                    if isinstance(move, tuple) and len(move) == 2:  # corridor pathing
                        self.last_positions.append(move)
                    return move

        # --------------------------------------------------- no room chosen
        if corridor_moves:
            move = random.choice(corridor_moves)
            if isinstance(move, tuple):
                self.last_positions.append(move)
            return move

        return random.choice(available_moves) if available_moves else None  # fallback

    # ------------------------------------------------------ suggestions/AI
    def handle_suggestion(self, game, room: str):
        """Called by the engine when this token is inside *room* and may/has to
        make a suggestion.  Returns (room, suspect, weapon).
        """
        # Remember we need to step outside next turn
        self._must_exit_next_turn = True
        self._visited_rooms.add(room)

        # Initialize suggestion space if not yet done
        if not self.room_suggestion_space and game:
            self.initialize_suggestion_space(game)

        # Check if we have untested suggestions for this room
        if room in self.room_suggestion_space and self.room_suggestion_space[room]:
            # Use next untested combination for this room
            suspect, weapon = self.room_suggestion_space[room].pop(0)
            suggestion = (room, suspect, weapon)
            self._previous_suggestions.add(suggestion)
            self.current_target_suggestion = suggestion
            return suggestion

        # If we've tried all combinations or this room isn't in our mapping,
        # fall back to our current target suggestion or to the strategy-based approach
        if self.current_target_suggestion and self.current_target_suggestion[2] == room:
            suspect, weapon, _ = self.current_target_suggestion
            suggestion = (room, suspect, weapon)
            self._previous_suggestions.add(suggestion)
            return suggestion

        # Fallback: use the strategic approach
        suspect, weapon = self._choose_suspect_weapon(room, game)
        suggestion = (room, suspect, weapon)
        self._previous_suggestions.add(suggestion)
        self.current_target_suggestion = suggestion
        return suggestion

    def should_make_suggestion(self, game, room):
        """Determine if the AI should make a suggestion while staying in a room."""
        # Always make a suggestion if there are untested combinations for this room
        if room in self.room_suggestion_space and self.room_suggestion_space[room]:
            return True

        # Make a suggestion if we have a current target for this room
        if self.current_target_suggestion and self.current_target_suggestion[2] == room:
            return True

        # Otherwise, only suggest if we haven't already suggested in this room this turn
        last_suggestion = None
        if self._previous_suggestions:
            # Get the most recent suggestion
            last_suggestion = next(iter(self._previous_suggestions))

        return last_suggestion is None or last_suggestion[0] != room

    # -------------------------------------------------------------- accusation
    def should_make_accusation(self, game=None) -> bool:
        """Engine query: do you wish to accuse right now?"""
        return self._ready_to_accuse()

    def make_accusation(self, game=None):
        """Return the (room, suspect, weapon) tuple that we believe is the solution."""
        if self.knowledge is None:
            # Fallback if knowledge is missing
            return None

        sol = self.knowledge.possible_solution

        # If we know the exact solution, return it
        if self.knowledge.is_solution_known():
            room = next(iter(sol["rooms"]))
            suspect = next(iter(sol["suspects"]))
            weapon = next(iter(sol["weapons"]))
            return (room, suspect, weapon)

        # Otherwise, use our current target suggestion
        if self.current_target_suggestion:
            return self.current_target_suggestion

        # Fallback to educated guess
        suspect_scores = {s: 0 for s in sol["suspects"]}
        weapon_scores = {w: 0 for w in sol["weapons"]}
        room_scores = {r: 0 for r in sol["rooms"]}

        # Analyze past suggestions to score each card
        for event in self.knowledge.events:
            if event["type"] == self.knowledge.EVENT_SUGGESTION:
                room, suspect, weapon = event["suggestion"]
                responding_player = event["responding_player"]

                # If no one could respond, all cards get a high score
                if responding_player is None:
                    if suspect in suspect_scores:
                        suspect_scores[suspect] += 3
                    if weapon in weapon_scores:
                        weapon_scores[weapon] += 3
                    if room in room_scores:
                        room_scores[room] += 3

                # If someone responded but we don't know which card they showed,
                # give a small boost to all cards in the suggestion
                elif "revealed_card" not in event:
                    if suspect in suspect_scores:
                        suspect_scores[suspect] += 1
                    if weapon in weapon_scores:
                        weapon_scores[weapon] += 1
                    if room in room_scores:
                        room_scores[room] += 1

        # Choose the highest scoring card in each category
        suspect = self._select_highest_score(suspect_scores)
        weapon = self._select_highest_score(weapon_scores)
        room = self._select_highest_score(room_scores)

        return (room, suspect, weapon)

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

    # ---------------------------------------------------- internal logic
    def update_knowledge_from_suggestion(self, suggesting_player, suggestion, responding_player, revealed_card=None):
        """
        Update knowledge based on a suggestion and its response.
        Also update our suggestion tracking.
        """
        # Call parent method to update knowledge
        super().update_knowledge_from_suggestion(
            suggesting_player, suggestion, responding_player, revealed_card
        )

        # If this was our suggestion, record the result
        if suggesting_player == self.player_id:
            room, suspect, weapon = suggestion

            # Store the result for this suggestion
            self.suggestion_results[(room, suspect, weapon)] = {
                'responding_player': responding_player,
                'revealed_card': revealed_card
            }

            # If no one responded, we know these cards aren't in anyone's hand
            # In AIPlayer when processing suggestions with no response, change:
            if responding_player is None:
                if room not in self.eliminated_rooms:
                    self.knowledge.possible_solution["rooms"].add(room)  # use add() instead of append()
                if suspect not in self.eliminated_suspects:
                    self.knowledge.possible_solution["suspects"].add(suspect)  # use add()
                if weapon not in self.eliminated_weapons:
                    self.knowledge.possible_solution["weapons"].add(weapon)  # use add()

            # If we know which card was shown, we can eliminate it from solution
        elif revealed_card is not None:
            card_type, card_name = revealed_card
            if card_type == "room":
                self.eliminated_rooms.add(card_name)
                if card_name in self.knowledge.possible_solution["rooms"]:
                    self.knowledge.possible_solution["rooms"].remove(card_name)
            elif card_type == "suspect":
                self.eliminated_suspects.add(card_name)
                if card_name in self.knowledge.possible_solution["suspects"]:
                    self.knowledge.possible_solution["suspects"].remove(card_name)
            elif card_type == "weapon":
                self.eliminated_weapons.add(card_name)
                if card_name in self.knowledge.possible_solution["weapons"]:
                    self.knowledge.possible_solution["weapons"].remove(card_name)
        # Update our suggestion space by removing eliminated cards
        self._prune_suggestion_space()

    def determine_target_suggestion(self, game):
        """Determine the best suggestion target based on our current knowledge."""
        if self.knowledge is None:
            # Fallback if knowledge is missing
            return (random.choice(game.character_names),
                    random.choice(game.weapon_names),
                    random.choice(game.room_names))

        # Get our current best guesses
        sol = self.knowledge.possible_solution

        # For each category, score each possible item based on confidence
        suspect_scores = self._score_candidates(sol["suspects"], "suspect")
        weapon_scores = self._score_candidates(sol["weapons"], "weapon")
        room_scores = self._score_candidates(sol["rooms"], "room")

        # Select the highest scoring item in each category
        suspect = self._select_highest_score(suspect_scores)
        weapon = self._select_highest_score(weapon_scores)
        room = self._select_highest_score(room_scores)

        return (suspect, weapon, room)

    def _score_candidates(self, candidates, category_type):
        """Score a set of candidates based on how likely they are to be the solution."""
        # Initialize scores
        scores = {item: 0 for item in candidates}

        if not scores:  # If no candidates, return empty dict
            return scores

        # If there's only one possibility, it gets max score
        if len(scores) == 1:
            item = next(iter(scores))
            scores[item] = 100
            return scores

        # Analyze past suggestions to score each candidate
        for event in self.knowledge.events:
            if event["type"] == self.knowledge.EVENT_SUGGESTION:
                room, suspect, weapon = event["suggestion"]
                responding_player = event["responding_player"]

                # Get the relevant item from this suggestion based on category_type
                item = None
                if category_type == "suspect":
                    item = suspect
                elif category_type == "weapon":
                    item = weapon
                elif category_type == "room":
                    item = room

                if item not in scores:
                    continue  # Skip if this item is not in our candidates

                # If no one could respond, that's strong evidence
                if responding_player is None:
                    scores[item] += 3

                # If someone responded but we don't know which card they showed,
                # give a small boost
                elif "revealed_card" not in event:
                    scores[item] += 1

                # If we know what card was shown and it wasn't this one,
                # that's also evidence in favor
                elif "revealed_card" in event:
                    revealed_type, revealed_name = event["revealed_card"]
                    if revealed_type != category_type or revealed_name != item:
                        scores[item] += 2

        return scores

    def _select_highest_score(self, scores):
        """Select the item with the highest score, breaking ties randomly."""
        if not scores:
            return None

        # Find the highest score
        max_score = max(scores.values())

        # Get all items with the highest score
        top_items = [item for item, score in scores.items() if score == max_score]

        # Return a random item from the top scorers
        return random.choice(top_items)

    def _prune_suggestion_space(self):
        """Remove combinations from suggestion space that contain eliminated cards."""
        # If knowledge isn't initialized, there's nothing to do
        if not self.knowledge:
            return

        # Update each room's suggestion space
        for room in list(self.room_suggestion_space.keys()):
            if room in self.eliminated_rooms:
                # If the room is eliminated, remove all combinations for this room
                self.room_suggestion_space[room] = []
                continue

            # Filter out combinations that include eliminated cards
            filtered_combinations = []
            for suspect, weapon in self.room_suggestion_space[room]:
                # Keep only combinations where neither suspect nor weapon is eliminated
                if (suspect not in self.eliminated_suspects and
                        weapon not in self.eliminated_weapons):
                    filtered_combinations.append((suspect, weapon))

            # Update the suggestion space for this room
            self.room_suggestion_space[room] = filtered_combinations

    def update_target_suggestion(self, game):
        """Update our target suggestion based on new information."""
        # If we have no knowledge system, we can't make a good target
        if not self.knowledge:
            return False

        # If we don't have a current target or it's now impossible, get a new one
        if not self.current_target_suggestion:
            self.current_target_suggestion = self.determine_target_suggestion(game)
            return True

        suspect, weapon, room = self.current_target_suggestion

        # Check if any component of our current target is now impossible
        impossible = False

        if suspect not in self.knowledge.possible_solution["suspects"]:
            impossible = True
        if weapon not in self.knowledge.possible_solution["weapons"]:
            impossible = True
        if room not in self.knowledge.possible_solution["rooms"]:
            impossible = True

        # If impossible, get a new target
        if impossible:
            self.current_target_suggestion = self.determine_target_suggestion(game)
            return True

        return False

    def _choose_suspect_weapon(self, room: str, game):
        """Pick a (suspect, weapon) pair that maximises information gain."""
        if self.knowledge is None:
            # Fallback if knowledge is not initialized
            return (random.choice(game.character_names),
                    random.choice(game.weapon_names))

        # Get cards that are still in the possible solution
        poss_sus = self.knowledge.possible_solution["suspects"]
        poss_wea = self.knowledge.possible_solution["weapons"]

        # Ensure non-empty fallbacks
        if not poss_sus:
            poss_sus = set(game.character_names)
        if not poss_wea:
            poss_wea = set(game.weapon_names)

        # Get cards that we know are in players' hands
        known_cards = set()
        for player_id, cards in self.knowledge.player_cards.items():
            known_cards.update(cards)

        # Get suspects and weapons that we don't know who has them
        unknown_sus = [s for s in game.character_names if s not in known_cards]
        unknown_wea = [w for w in game.weapon_names if w not in known_cards]

        # Prioritize cards that are still in the possible solution AND we don't know who has them
        priority_sus = [s for s in poss_sus if s in unknown_sus]
        priority_wea = [w for w in poss_wea if w in unknown_wea]

        # Create different candidate lists in order of priority
        candidate_lists = []

        # 1. Cards that are still in the possible solution AND we don't know who has them
        #    AND we haven't asked about this combination before
        priority_candidates = [(s, w) for s in priority_sus for w in priority_wea
                               if (room, s, w) not in self._previous_suggestions]
        candidate_lists.append(priority_candidates)

        # 2. Cards that are still in the possible solution AND we haven't asked about this combination before
        solution_candidates = [(s, w) for s in poss_sus for w in poss_wea
                               if (room, s, w) not in self._previous_suggestions]
        candidate_lists.append(solution_candidates)

        # 3. Cards that we don't know who has them AND we haven't asked about this combination before
        unknown_candidates = [(s, w) for s in unknown_sus for w in unknown_wea
                              if (room, s, w) not in self._previous_suggestions]
        candidate_lists.append(unknown_candidates)

        # 4. Any combination we haven't asked about before
        new_candidates = [(s, w) for s in game.character_names for w in game.weapon_names
                          if (room, s, w) not in self._previous_suggestions]
        candidate_lists.append(new_candidates)

        # 5. Fallback: any combination, preferring those we've asked about least
        suggestion_counts = defaultdict(int)
        for suggestion in self._previous_suggestions:
            r, s, w = suggestion
            if r == room:
                suggestion_counts[(s, w)] += 1

        all_candidates = [(s, w) for s in game.character_names for w in game.weapon_names]
        all_candidates.sort(key=lambda pair: suggestion_counts[pair])
        candidate_lists.append(all_candidates)

        # Choose from the highest priority non-empty list
        for candidates in candidate_lists:
            if candidates:
                return random.choice(candidates)

        # This should never happen, but just in case
        return (random.choice(game.character_names), random.choice(game.weapon_names))

    def _ready_to_accuse(self) -> bool:
        """Return *True* if the AI is ready to make an accusation."""
        if self.knowledge is None:
            return False

        # Check if we're in the Clue room
        in_clue = False
        if hasattr(self, 'character') and self.character is not None:
            if isinstance(self.character.position, str):
                in_clue = (self.character.position == "Clue")
            elif isinstance(self.character.position, tuple) and len(self.character.position) == 3:
                in_clue = (self.character.position[0] == "Clue")

        if not in_clue:
            return False

        sol = self.knowledge.possible_solution

        # Case 1: We know the exact solution
        exact_solution = all(len(sol[c]) == 1 for c in ("suspects", "weapons", "rooms"))
        if exact_solution:
            return True

        # Case 2: We're very confident in the solution
        # As the game progresses, we become more willing to make an accusation with less certainty
        suspect_count = len(sol["suspects"])
        weapon_count = len(sol["weapons"])
        room_count = len(sol["rooms"])

        # Calculate a confidence score based on how many possibilities are left
        # Lower is better (fewer possibilities)
        confidence_score = suspect_count + weapon_count + room_count

        # As turns increase, we're more willing to take risks
        turn_threshold = 30  # After this many turns, we'll be more aggressive

        # Early game: Only accuse if we're very confident
        if self._turn_counter < turn_threshold:
            return confidence_score <= 4  # e.g., 2 suspects, 1 weapon, 1 room

        # Mid game: Accuse if we're reasonably confident
        elif self._turn_counter < 2 * turn_threshold:
            return confidence_score <= 6  # e.g., 2 suspects, 2 weapons, 2 rooms

        # Late game: Take more risks
        else:
            return confidence_score <= 9  # e.g., 3 suspects, 3 weapons, 3 rooms


