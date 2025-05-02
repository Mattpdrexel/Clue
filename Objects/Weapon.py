class Weapon:
    def __init__(self, name):
        self.name = name
        self.location = None  # Room name

    def move_to(self, room_name):
        self.location = room_name

    def __repr__(self):
        return f"{self.name} in {self.location}"
