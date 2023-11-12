
class PinballMachine:
    def __init__(self, long_name, abbreviation, room):
        self.long_name = long_name
        self.abbreviation = abbreviation
        self.room = room

class Player:
    def __init__(self, name, abbreviation=None):
        self.name = name
        self.abbreviation = abbreviation

class Score:
    def __init__(self, player_abbreviation, pinball_abbreviation, points, date):
        self.player_abbreviation = player_abbreviation
        self.pinball_abbreviation = pinball_abbreviation
        self.points = points
        self.date = date
