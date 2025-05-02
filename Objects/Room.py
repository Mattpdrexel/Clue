
class RoomEntrance:
    def __init__(self, room_name, row, column):
        self.room_name = room_name
        self.row = row
        self.column = column

class Room:
    def __init__(self, name):
        self.name = name
        self.room_entrance_list = []
        self.secret_passage_to = None  # Name of room connected by secret passage

    def add_room_entrance(self, row, column):
        room_entrance = RoomEntrance(self.name, row, column)
        self.room_entrance_list.append(room_entrance)

    def add_secret_passage(self, destination_room):
        """Add a secret passage to another room"""
        self.secret_passage_to = destination_room

    def get_room_entrance_from_cell(self, row, column):
        for entrance in self.room_entrance_list:
            if entrance.row == row and entrance.column == column:
                return entrance
        return None  # Not an entrance to this room

    def __repr__(self):
        passage_info = f" (Secret passage to: {self.secret_passage_to})" if self.secret_passage_to else ""
        return f"Room: {self.name.title()}{passage_info}"
