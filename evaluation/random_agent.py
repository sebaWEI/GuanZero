import random


class RandomAgent():

    def __init__(self):
        self.name = 'Random'

    def act(self, info_set):
        return random.choice(info_set.legal_actions)
