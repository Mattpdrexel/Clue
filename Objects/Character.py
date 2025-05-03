from Data.Constants import CHARACTERS

class Character:
    def __init__(self, name):
        self.name = name
        self.position = "Clue" # Characters start in the Clue room

    def move_to(self, new_position):
        self.position = new_position

    def __repr__(self):
        return f"{self.name} at {self.position}"

character_dict = {name : Character(name) for name in CHARACTERS}