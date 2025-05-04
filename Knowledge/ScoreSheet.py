# Knowledge/ScoreSheet.py
from typing import Dict, Set, List, Optional
import os
from Data.Constants import CHARACTERS, WEAPONS, ROOMS, SUSPECT_ROOMS


class ScoreSheet:
    """
    A visual representation of a player's knowledge about the game.
    This is similar to the physical scoresheets players use in the board game.
    """

    def __init__(self, player_names: List[str]):
        self.player_names = player_names
        self.num_players = len(player_names)

        # Knowledge state for each player
        # Format: {player_id: {card_name: status}}
        # Status can be: 'has', 'not_has', or None (unknown)
        self.player_knowledge: Dict[int, Dict[str, Optional[str]]] = {}

        # Initialize knowledge for each player
        for i in range(self.num_players):
            self.player_knowledge[i] = {}
            for card in CHARACTERS + WEAPONS + SUSPECT_ROOMS:
                self.player_knowledge[i][card] = None

        # Track which cards have been marked as solution
        self.solution_suspects: Set[str] = set()
        self.solution_weapons: Set[str] = set()
        self.solution_rooms: Set[str] = set()

    def mark_player_has_card(self, player_id: int, card_name: str):
        """Mark that a player has a specific card."""
        if player_id < 0 or player_id >= self.num_players:
            return

        if card_name not in self.player_knowledge[player_id]:
            return

        self.player_knowledge[player_id][card_name] = 'has'

        # Mark all other players as not having this card
        for pid in range(self.num_players):
            if pid != player_id:
                self.player_knowledge[pid][card_name] = 'not_has'

        # Remove from solution if it was marked there
        if card_name in CHARACTERS:
            self.solution_suspects.discard(card_name)
        elif card_name in WEAPONS:
            self.solution_weapons.discard(card_name)
        elif card_name in SUSPECT_ROOMS:
            self.solution_rooms.discard(card_name)

    def mark_player_not_has_card(self, player_id: int, card_name: str):
        """Mark that a player doesn't have a specific card."""
        if player_id < 0 or player_id >= self.num_players:
            return

        if card_name not in self.player_knowledge[player_id]:
            return

        self.player_knowledge[player_id][card_name] = 'not_has'

        # Check if all players don't have this card - it must be in the solution
        all_players_not_have = True
        for pid in range(self.num_players):
            if self.player_knowledge[pid].get(card_name) != 'not_has':
                all_players_not_have = False
                break

        if all_players_not_have:
            self.mark_solution_card(card_name)

    def mark_solution_card(self, card_name: str):
        """Mark a card as part of the solution."""
        if card_name in CHARACTERS:
            self.solution_suspects.add(card_name)
            # Mark all players as not having this card
            for pid in range(self.num_players):
                self.player_knowledge[pid][card_name] = 'not_has'
        elif card_name in WEAPONS:
            self.solution_weapons.add(card_name)
            # Mark all players as not having this card
            for pid in range(self.num_players):
                self.player_knowledge[pid][card_name] = 'not_has'
        elif card_name in SUSPECT_ROOMS:
            self.solution_rooms.add(card_name)
            # Mark all players as not having this card
            for pid in range(self.num_players):
                self.player_knowledge[pid][card_name] = 'not_has'

    def update_from_player_knowledge(self, player_id: int, knowledge):
        """Update the scoresheet from a PlayerKnowledge object."""
        if not knowledge:
            return

        # Update cards in players' hands
        for pid, cards in knowledge.player_cards.items():
            for card in cards:
                self.mark_player_has_card(pid, card)

        # Update cards that we know players don't have
        for pid, cards in knowledge.player_not_cards.items():
            for card in cards:
                self.mark_player_not_has_card(pid, card)

        # Process knowledge from events
        for event in knowledge.events:
            if event["type"] == knowledge.EVENT_SUGGESTION:
                suggestion = event["suggestion"]
                room, suspect, weapon = suggestion
                responding_player = event["responding_player"]

                # If no one responded, these cards might be in the solution
                if responding_player is None:
                    self.mark_solution_card(room)
                    self.mark_solution_card(suspect)
                    self.mark_solution_card(weapon)

                # If a card was revealed, mark it as held by that player
                if "revealed_card" in event:
                    card_type, card_name = event["revealed_card"]
                    if responding_player is not None:
                        self.mark_player_has_card(responding_player, card_name)

        # Update possible solution
        solution = knowledge.possible_solution
        for suspect in solution.get("suspects", []):
            if len(solution["suspects"]) == 1:
                self.mark_solution_card(suspect)

        for weapon in solution.get("weapons", []):
            if len(solution["weapons"]) == 1:
                self.mark_solution_card(weapon)

        for room in solution.get("rooms", []):
            if len(solution["rooms"]) == 1 and room != "Clue":
                self.mark_solution_card(room)

    def render_text(self, highlight_player_id: Optional[int] = None) -> str:
        """Render the scoresheet as formatted text."""
        output = []

        # Add header
        header = "CLUE SCORESHEET"
        output.append(f"\n{header.center(80, '=')}")

        # Add solution section
        output.append("\n🔍 SOLUTION")

        # Person
        suspect_status = ", ".join(sorted(self.solution_suspects)) if self.solution_suspects else "?"
        output.append(f"  PERSON:  {suspect_status}")

        # Weapon
        weapon_status = ", ".join(sorted(self.solution_weapons)) if self.solution_weapons else "?"
        output.append(f"  WEAPON:  {weapon_status}")

        # Room
        room_status = ", ".join(sorted(self.solution_rooms)) if self.solution_rooms else "?"
        output.append(f"  ROOM:    {room_status}")

        # Add player columns header
        output.append("\n\nPLAYERS:")

        # Create column header with player names
        player_header = "CARD".ljust(20)
        for i, name in enumerate(self.player_names):
            # Highlight current player if specified
            if highlight_player_id is not None and i == highlight_player_id:
                name = f"*{name}*"  # Add emphasis
            player_header += name.ljust(12)
        output.append(player_header)
        output.append("-" * 20 + "-" * 12 * self.num_players)

        # Characters section
        output.append("\nSUSPECTS:")
        for card in sorted(CHARACTERS):
            line = card.ljust(20)
            for pid in range(self.num_players):
                status = self.player_knowledge[pid].get(card)
                if status == 'has':
                    symbol = "✓".ljust(12)  # Has the card
                elif status == 'not_has':
                    symbol = "✗".ljust(12)  # Doesn't have the card
                else:
                    symbol = "?".ljust(12)  # Unknown
                line += symbol
            output.append(line)

        # Weapons section
        output.append("\nWEAPONS:")
        for card in sorted(WEAPONS):
            line = card.ljust(20)
            for pid in range(self.num_players):
                status = self.player_knowledge[pid].get(card)
                if status == 'has':
                    symbol = "✓".ljust(12)  # Has the card
                elif status == 'not_has':
                    symbol = "✗".ljust(12)  # Doesn't have the card
                else:
                    symbol = "?".ljust(12)  # Unknown
                line += symbol
            output.append(line)

        # Rooms section
        output.append("\nROOMS:")
        for card in sorted(SUSPECT_ROOMS):
            line = card.ljust(20)
            for pid in range(self.num_players):
                status = self.player_knowledge[pid].get(card)
                if status == 'has':
                    symbol = "✓".ljust(12)  # Has the card
                elif status == 'not_has':
                    symbol = "✗".ljust(12)  # Doesn't have the card
                else:
                    symbol = "?".ljust(12)  # Unknown
                line += symbol
            output.append(line)

        # Add legend at the bottom
        output.append("\nLEGEND:")
        output.append("  ✓ = Has card")
        output.append("  ✗ = Doesn't have card")
        output.append("  ? = Unknown")

        return "\n".join(output)

    def render_for_player(self, player_id: int) -> str:
        """Render the scoresheet from a specific player's perspective."""
        return self.render_text(highlight_player_id=player_id)

    def save_to_file(self, filename: str):
        """Save the scoresheet to a text file."""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(self.render_text())
