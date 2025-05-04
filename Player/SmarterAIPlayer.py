# Player/SmarterAIPlayer.py
from Player.KnowledgeAIPlayer import KnowledgeAIPlayer
import random


class SmarterAIPlayer(KnowledgeAIPlayer):
    """
    A smarter AI player that uses advanced strategies based on the knowledge base.
    """

    def __init__(self, player_id, character_name):
        """Initialize the SmarterAIPlayer."""
        super().__init__(player_id, character_name)

        # Movement strategy parameters
        self.target_room = None
        self.previous_rooms = []
        self.max_previous_rooms = 3

        # A patience threshold for making accusations
        # If no progress is made over this many turns, consider making accusation
        self.patience_threshold = 10
        self.last_knowledge_state = None
        self.no_progress_turns = 0

    def make_move(self, game, available_moves, die_roll):
        """
        Make a strategic move based on knowledge.

        Args:
            game: The Game instance
            available_moves: List of available moves
            die_roll: The value rolled on the die

        Returns:
            The chosen move
        """
        # Initialize knowledge base if needed
        if self.kb is None:
            self.initialize_knowledge_base(game)

        # Track if any new knowledge has been gained
        current_knowledge_state = (
            len(self.kb.envelope_suspects),
            len(self.kb.envelope_weapons),
            len(self.kb.envelope_rooms)
        )

        if self.last_knowledge_state == current_knowledge_state:
            self.no_progress_turns += 1
        else:
            self.no_progress_turns = 0
            self.last_knowledge_state = current_knowledge_state

        # If should make accusation and Clue room is available, prioritize it
        if (self.no_progress_turns >= self.patience_threshold or
                len(self.kb.envelope_suspects) * len(self.kb.envelope_weapons) * len(self.kb.envelope_rooms) <= 8):
            if "Clue" in available_moves:
                return "Clue"

        # If we need to exit room, prioritize hallway moves
        if self.must_exit_next_turn and available_moves:
            # Split moves into rooms and corridors
            room_moves = [m for m in available_moves if isinstance(m, str)]
            corridor_moves = [m for m in available_moves if not isinstance(m, str)]

            if corridor_moves:
                self.must_exit_next_turn = False
                return random.choice(corridor_moves)

        # Split available moves into rooms and corridors
        room_moves = [m for m in available_moves if isinstance(m, str)]
        corridor_moves = [m for m in available_moves if not isinstance(m, str)]

        # If we're in a corridor and rooms are available, prioritize rooms
        if room_moves:
            # Preference for rooms we haven't visited recently
            unvisited_rooms = [r for r in room_moves if r not in self.previous_rooms]

            if unvisited_rooms:
                chosen_room = self._choose_best_room(unvisited_rooms)
                self._update_previous_rooms(chosen_room)
                return chosen_room
            else:
                chosen_room = self._choose_best_room(room_moves)
                self._update_previous_rooms(chosen_room)
                return chosen_room

        # If only corridor moves are available, choose one
        if corridor_moves:
            return random.choice(corridor_moves)

        # Fallback to any available move
        if available_moves:
            return random.choice(available_moves)

        return None

    def _choose_best_room(self, rooms):
        """Choose the most informative room to investigate."""
        if not rooms:
            return None

        # If a single room candidate remains in envelope, prioritize rooms we don't know
        if len(self.kb.envelope_rooms) == 1:
            envelope_room = next(iter(self.kb.envelope_rooms))
            # If the envelope room is in our options, prioritize other rooms
            if envelope_room in rooms and len(rooms) > 1:
                other_rooms = [r for r in rooms if r != envelope_room]
                return random.choice(other_rooms)

        # Get the room with most information value
        # Information value = how many suspects/weapons in envelope could be in this room
        room_scores = {}
        for room in rooms:
            # Score is higher for rooms we've never suggested in
            score = 10
            if room in [r for (_, _, r) in self.previous_suggestions]:
                score -= 5

            # Adjust score based on how many times we've visited recently
            occurrences = self.previous_rooms.count(room)
            score -= occurrences * 2

            room_scores[room] = score

        # Choose room with highest score, breaking ties randomly
        max_score = max(room_scores.values())
        best_rooms = [r for r, s in room_scores.items() if s == max_score]
        return random.choice(best_rooms)

    def _update_previous_rooms(self, room):
        """Update the list of previously visited rooms."""
        self.previous_rooms.append(room)
        if len(self.previous_rooms) > self.max_previous_rooms:
            self.previous_rooms.pop(0)

    def choose_suggestion(self, game, room):
        """
        Choose a strategic suggestion based on knowledge.

        Args:
            game: The Game instance
            room: The current room

        Returns:
            tuple: (suspect, weapon) for the suggestion
        """
        # Initialize knowledge base if needed
        if self.kb is None:
            self.initialize_knowledge_base(game)

        # Get envelope candidates
        envelope = self.kb.envelope_candidates()

        # If we haven't narrowed down a category yet, try to gather information
        # about as many cards as possible
        if len(envelope["suspects"]) > 1 and len(envelope["weapons"]) > 1:
            # Look for novel combinations we haven't tried yet
            novel_suggestions = []
            for suspect in envelope["suspects"]:
                for weapon in envelope["weapons"]:
                    if (suspect, weapon, room) not in self.previous_suggestions:
                        novel_suggestions.append((suspect, weapon))

            # If we have novel suggestions, use one of those
            if novel_suggestions:
                return random.choice(novel_suggestions)

        # If we've narrowed down suspects but not weapons, fix the suspect and vary weapons
        elif len(envelope["suspects"]) == 1 and len(envelope["weapons"]) > 1:
            suspect = next(iter(envelope["suspects"]))
            for weapon in envelope["weapons"]:
                if (suspect, weapon, room) not in self.previous_suggestions:
                    return (suspect, weapon)

        # If we've narrowed down weapons but not suspects, fix the weapon and vary suspects
        elif len(envelope["weapons"]) == 1 and len(envelope["suspects"]) > 1:
            weapon = next(iter(envelope["weapons"]))
            for suspect in envelope["suspects"]:
                if (suspect, weapon, room) not in self.previous_suggestions:
                    return (suspect, weapon)

        # Fall back to parent implementation
        return super().choose_suggestion(game, room)

    def should_make_accusation(self, game):
        """
        Determine if we should make an accusation based on knowledge.

        Args:
            game: The Game instance

        Returns:
            bool: True if we should try to make an accusation
        """
        # First check if solution is logically known from KB
        kb_says_accuse = super().should_make_accusation(game)
        if kb_says_accuse:
            return True

        # Check if we're in the Clue room
        current_position = self.character.position
        in_clue_room = False

        if isinstance(current_position, str) and current_position == "Clue":
            in_clue_room = True
        elif isinstance(current_position, tuple) and len(current_position) == 3 and current_position[0] == "Clue":
            in_clue_room = True

        if not in_clue_room:
            return False

        # If we've narrowed down options significantly, consider making an accusation
        envelope = self.kb.envelope_candidates()
        total_possibilities = (
                len(envelope["suspects"]) *
                len(envelope["weapons"]) *
                len(envelope["rooms"])
        )

        # If very few possibilities remain or we've been stuck for a while
        if total_possibilities <= 4 or self.no_progress_turns >= self.patience_threshold:
            return True

        return False

    def handle_accusation(self, game):
        """
        Handle making an accusation based on current knowledge.

        Args:
            game: The Game instance

        Returns:
            bool: True if accusation was made, False otherwise
        """
        from Game.GameLogic import process_accusation

        # Check if we have a definite solution from KB
        if super().handle_accusation(game):
            return True

        # If we should make a guess based on available information
        if self.should_make_accusation(game):
            envelope = self.kb.envelope_candidates()

            # Pick the most likely solution
            suspect = random.choice(list(envelope["suspects"]))
            weapon = random.choice(list(envelope["weapons"]))
            room = random.choice(list(envelope["rooms"]))

            print(f"{self.character_name} makes an educated guess: {suspect} in the {room} with the {weapon}")

            # Submit the accusation
            result = process_accusation(game, self, suspect, weapon, room)

            if result:
                print(f"{self.character_name} was correct!")
            else:
                print(f"{self.character_name} was wrong and is eliminated.")

            return True

        return False