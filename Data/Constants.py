CHARACTERS = [
    "Miss Scarlet", "Colonel Mustard", "Mrs White",
    "Reverend Green", "Mrs Peacock", "Professor Plum"
]

WEAPONS = [
    "Candlestick", "Lead Pipe", "Wrench",
    "Knife", "Revolver", "Rope"
]

ROOMS = [
    "Study", "Hall", "Lounge", "Dining Room", "Kitchen",
    "Ball Room", "Conservatory", "Billiard Room", "Library",
    "Clue"          # central room
]

# Secret passages between rooms (diagonally opposite rooms)
SECRET_PASSAGES = {
    "Study": "Kitchen",
    "Kitchen": "Study",
    "Lounge": "Conservatory",
    "Conservatory": "Lounge"
}

# Bonus card types
BONUS_CARD_TYPES = [
    "Extra Turn",
    "See A Card",
    "Move Any Character",
    "Teleport",
    "Peek At Envelope"
]


ALL_CARDS = CHARACTERS + WEAPONS + ROOMS
