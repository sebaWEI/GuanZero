import collections
import itertools
from environment.utils import select
from environment.utils import RealCard2EnvCard, EnvCard2RealCard, EnvCard2Rank, EnvCard2Suit


class MoveGenerator(object):
    """
    Generate possible combinations.
    """

    def __init__(self, cards_list, wild_card_of_game=1):

        self.wild_card_of_game = wild_card_of_game
        self.wild_cards_in_hand = []

        self.cards_list = cards_list
        self.cards_dict = collections.defaultdict(list)

        for i in self.cards_list:
            self.cards_dict[EnvCard2Rank[i]].append(i)

        self.single_card_moves = []
        self.gen_type_1_single()
        self.pair_moves = []
        self.gen_type_2_pair()
        self.triple_cards_moves = []
        self.gen_type_3_triple()
        self.bomb_4_moves = []
        self.gen_type_8_bomb_4()
        self.bomb_5_moves = []
        self.gen_type_9_bomb_5()
        self.bomb_6_moves = []
        self.gen_type_11_bomb_6()
        self.bomb_7_moves = []
        self.gen_type_12_bomb_7()
        self.bomb_8_moves = []
        self.gen_type_13_bomb_8()
        self.joker_bomb_moves = []
        self.gen_type_14_joker_bomb()

    def find_wild_card_in_hand(self):
        for i in self.cards_list:
            if self.wild_card_of_game == i:
                self.wild_cards_in_hand.append([i])
        return self.wild_cards_in_hand

    def gen_type_1_single(self):
        self.single_card_moves = []
        for i in set(self.cards_list):
            self.single_card_moves.append([i])
        return self.single_card_moves

    def gen_type_2_pair(self):
        self.pair_moves = []
        for k, v in self.cards_dict.items():
            if len(v) >= 2:
                self.pair_moves += list(map(list, itertools.combinations(v, 2)))
            if self.wild_card_of_game in self.cards_list:
                for k1, v1 in self.cards_dict.items():
                    if k1 != EnvCard2Rank[self.wild_card_of_game]:
                        for i1 in range(len(list(set(v1)))):
                            self.pair_moves.append([list(set(v1))[i1], self.wild_card_of_game])
        self.pair_moves = [list(t) for t in set(tuple(p) for p in self.pair_moves)]
        return self.pair_moves

    def gen_type_3_triple(self):
        self.triple_cards_moves = []
        for k, v in self.cards_dict.items():
            if len(v) >= 3:
                self.triple_cards_moves.append([k, k, k])
        return self.triple_cards_moves

    def gen_type_8_bomb_4(self):
        self.bomb_4_moves = []
        for k, v in self.cards_dict.items():
            if len(v) >= 4:
                self.bomb_4_moves.append([k, k, k, k])
        return self.bomb_4_moves

    def gen_type_9_bomb_5(self):
        self.bomb_5_moves = []
        for k, v in self.cards_dict.items():
            if len(v) >= 5:
                self.bomb_5_moves.append([k, k, k, k, k])
        return self.bomb_5_moves

    def gen_type_11_bomb_6(self):
        self.bomb_6_moves = []
        for k, v in self.cards_dict.items():
            if len(v) >= 6:
                self.bomb_6_moves.append([k, k, k, k, k, k])
        return self.bomb_6_moves

    def gen_type_12_bomb_7(self):
        self.bomb_7_moves = []
        for k, v in self.cards_dict.items():
            if len(v) >= 7:
                self.bomb_7_moves.append([k, k, k, k, k, k, k])
        return self.bomb_7_moves

    def gen_type_13_bomb_8(self):
        self.bomb_8_moves = []
        for k, v in self.cards_dict.items():
            if len(v) >= 8:
                self.bomb_8_moves.append([k, k, k, k, k, k, k, k])
        return self.bomb_8_moves

    def gen_type_14_joker_bomb(self):
        self.joker_bomb_moves = []
        if (52 in self.cards_list and 53 in self.cards_list and
                self.cards_list.count(52) == 2 and self.cards_list.count(53) == 2):
            self.joker_bomb_moves.append([52, 52, 53, 53])
        return self.joker_bomb_moves
    # def test(self):
    #     print(self.card_dict)


test_hand = MoveGenerator([2, 2, 3, 3, 4, 5, 6, 6], wild_card_of_game=3)
# test_hand.test()
print(len(test_hand.find_wild_card_in_hand()))
print(test_hand.joker_bomb_moves)
print(test_hand.cards_dict)
print(test_hand.pair_moves)