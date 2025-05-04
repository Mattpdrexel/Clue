# Player/AIPlayer.py
from Player.Player import Player
import random
from typing import List, Tuple, Set
from collections import deque


class AIPlayer(Player):
    """An AI‑controlled Clue player powered by *PlayerKnowledge*."""

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

    # --------------------------------------------------------- API hooks
    def make_move(self, game, available_moves: List, dice_roll: int):
        """Choose where to move this turn.

        * If we *must* exit (because we suggested last turn) we pick any
          corridor square – that satisfies the unit tests.
        * Otherwise we prioritize:
          1. The Clue room if we know the solution
          2. Rooms that are still in the possible solution and we haven't visited
          3. Rooms that are still in the possible solution
          4. Rooms we haven't visited
          5. Any other room (avoiding backtracking)
        """
        self._turn_counter += 1

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

            # 1. Rooms that are still in the possible solution and we haven't visited
            priority_rooms = [m for m in room_moves
                             if self._room_name(m) in solution_rooms and
                             self._room_name(m) not in self._visited_rooms and
                             self._room_name(m) != "Clue"]

            # 2. Rooms that are still in the possible solution (even if visited)
            solution_room_moves = [m for m in room_moves
                                  if self._room_name(m) in solution_rooms and
                                  self._room_name(m) != "Clue"]

            # 3. Rooms we haven't visited (except Clue)
            unseen = [m for m in room_moves
                      if self._room_name(m) not in self._visited_rooms and
                      self._room_name(m) != "Clue"]

            # 4. Anything else (but avoid immediate back‑tracking)
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
        # remember we need to step outside next turn
        self._must_exit_next_turn = True
        self._visited_rooms.add(room)

        suspect, weapon = self._choose_suspect_weapon(room, game)
        self._previous_suggestions.add((suspect, weapon, room))
        return (room, suspect, weapon)

    # -------------------------------------------------------------- accusation
    def should_make_accusation(self, game=None) -> bool:
        """Engine query: do you wish to accuse right now?"""
        return self._ready_to_accuse()

    def make_accusation(self, game=None):
        """
        Return the (room, suspect, weapon) tuple that we believe is the solution.

        If we know the exact solution, return it.
        Otherwise, make an educated guess based on our knowledge.
        """
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

        # Otherwise, make an educated guess based on our knowledge

        # For each category, calculate a score for each possibility
        # based on how many times it's been suggested and not shown

        # Initialize scores
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
        # If there's a tie, choose randomly among the tied cards

        # Suspects
        max_suspect_score = max(suspect_scores.values()) if suspect_scores else 0
        top_suspects = [s for s, score in suspect_scores.items() if score == max_suspect_score]
        suspect = random.choice(top_suspects) if top_suspects else next(iter(sol["suspects"]))

        # Weapons
        max_weapon_score = max(weapon_scores.values()) if weapon_scores else 0
        top_weapons = [w for w, score in weapon_scores.items() if score == max_weapon_score]
        weapon = random.choice(top_weapons) if top_weapons else next(iter(sol["weapons"]))

        # Rooms
        max_room_score = max(room_scores.values()) if room_scores else 0
        top_rooms = [r for r, score in room_scores.items() if score == max_room_score]
        room = random.choice(top_rooms) if top_rooms else next(iter(sol["rooms"]))

        return (room, suspect, weapon)

    # ---------------------------------------------------- internal logic
    def _choose_suspect_weapon(self, room: str, game):
        """Pick a (suspect, weapon) pair that maximises information gain.

        Strategy:
        1. Prioritize cards that are still in the possible solution
        2. Prioritize combinations we haven't asked about before
        3. Prioritize cards that we don't know who has them
        4. Prioritize cards that are held by players we haven't asked yet
        5. Avoid cards that we know are in our hand or other players' hands
        """
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
                              if (s, w, room) not in self._previous_suggestions]
        candidate_lists.append(priority_candidates)

        # 2. Cards that are still in the possible solution AND we haven't asked about this combination before
        solution_candidates = [(s, w) for s in poss_sus for w in poss_wea
                              if (s, w, room) not in self._previous_suggestions]
        candidate_lists.append(solution_candidates)

        # 3. Cards that we don't know who has them AND we haven't asked about this combination before
        unknown_candidates = [(s, w) for s in unknown_sus for w in unknown_wea
                             if (s, w, room) not in self._previous_suggestions]
        candidate_lists.append(unknown_candidates)

        # 4. Any combination we haven't asked about before
        new_candidates = [(s, w) for s in game.character_names for w in game.weapon_names
                         if (s, w, room) not in self._previous_suggestions]
        candidate_lists.append(new_candidates)

        # 5. Fallback: any combination
        all_candidates = [(s, w) for s in game.character_names for w in game.weapon_names]
        candidate_lists.append(all_candidates)

        # Choose from the highest priority non-empty list
        for candidates in candidate_lists:
            if candidates:
                return random.choice(candidates)

        # This should never happen, but just in case
        return (random.choice(game.character_names), random.choice(game.weapon_names))

    def _ready_to_accuse(self) -> bool:
        """
        Return *True* if the AI is ready to make an accusation.

        Conditions:
        1. The AI must be in the Clue room
        2. Either:
           a. The AI knows the exact solution (one possibility in each category)
           b. The AI is very confident in the solution (few possibilities left and high turn count)
        """
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