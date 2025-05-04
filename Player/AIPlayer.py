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
        * Otherwise we favour rooms we have not yet visited, then rooms that
          still *could* be the solution according to *PlayerKnowledge*, then
          anything else.
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
            # 1. unseen rooms (except Clue)
            unseen = [m for m in room_moves
                      if self._room_name(m) not in self._visited_rooms and
                      self._room_name(m) != "Clue"]

            # 2. rooms still plausible for envelope
            plausible = []
            if self.knowledge is not None:
                for m in room_moves:
                    r = self._room_name(m)
                    if r in self.knowledge.possible_solution["rooms"]:
                        plausible.append(m)

            # 3. anything else (but avoid immediate back‑tracking)
            # Fix the slicing issue here by using list(self.last_positions)
            # and checking individual positions
            recent_positions = list(self.last_positions)[-2:] if len(self.last_positions) >= 2 else []
            fallback = [m for m in room_moves if m not in recent_positions]

            for choices in (unseen, plausible, fallback):
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
        """Return the (room, suspect, weapon) tuple that we believe is the
        solution. Compatible with Player.make_accusation method signature.
        """
        if self.knowledge is None or not self.knowledge.is_solution_known():
            # Fallback if knowledge is missing or incomplete
            return None

        sol = self.knowledge.possible_solution
        room = next(iter(sol["rooms"]))
        suspect = next(iter(sol["suspects"]))
        weapon = next(iter(sol["weapons"]))
        return (room, suspect, weapon)

    # ---------------------------------------------------- internal logic
    def _choose_suspect_weapon(self, room: str, game):
        """Pick a (suspect, weapon) pair that maximises information gain – at
        this basic level we simply prefer cards still possible for the envelope
        and that we have *not* asked about before.
        """
        if self.knowledge is None:
            # Fallback if knowledge is not initialized
            return (random.choice(game.character_names),
                    random.choice(game.weapon_names))

        poss_sus = self.knowledge.possible_solution["suspects"]
        poss_wea = self.knowledge.possible_solution["weapons"]

        # ensure non‑empty fall‑backs
        if not poss_sus:
            poss_sus = set(game.character_names)
        if not poss_wea:
            poss_wea = set(game.weapon_names)

        candidates = [(s, w) for s in poss_sus for w in poss_wea
                      if (s, w, room) not in self._previous_suggestions]
        if not candidates:
            candidates = [(s, w) for s in game.character_names for w in game.weapon_names]

        return random.choice(candidates)

    def _ready_to_accuse(self) -> bool:
        """Return *True* iff the knowledge base has narrowed each category down
        to exactly one possibility *and* we are currently in the Clue room (the
        game engine should check the latter but we guard anyway)."""
        if self.knowledge is None:
            return False

        sol = self.knowledge.possible_solution
        unique = all(len(sol[c]) == 1 for c in ("suspects", "weapons", "rooms"))

        # location check (character.position can be a str room or (room,r,c))
        in_clue = False
        if hasattr(self, 'character') and self.character is not None:
            if isinstance(self.character.position, str):
                in_clue = (self.character.position == "Clue")
            elif isinstance(self.character.position, tuple) and len(self.character.position) == 3:
                in_clue = (self.character.position[0] == "Clue")

        return unique and in_clue

    def handle_accusation(self, game):
        """Handle making an accusation if the AI decides to make one."""
        from Game.GameLogic import process_accusation

        # Check if the AI wants to make an accusation
        if self.should_make_accusation(game):
            print(f"{self.character_name} is making an accusation!")

            # Get the accusation from the AI
            accusation = self.make_accusation(game)

            if accusation:
                room, suspect, weapon = accusation

                # Process the accusation
                is_correct = process_accusation(game, self, suspect, weapon, room)

                if is_correct:
                    print(f"\n{self.character_name} made the correct accusation and wins the game!")
                else:
                    print(f"\n{self.character_name} made an incorrect accusation and is eliminated.")
