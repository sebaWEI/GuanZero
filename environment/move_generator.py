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
                        list_of_same_rank = list(set(v1))
                        for i1 in range(len(list_of_same_rank)):
                            self.pair_moves.append([list_of_same_rank[i1], self.wild_card_of_game])
        self.pair_moves = [list(t) for t in set(tuple(p) for p in self.pair_moves)]
        return self.pair_moves

    def _cards_with_same_rank_with_wild_card(self, number_of_cards: int):
        """
        dealing with card type with same rank. more than 3 cards. consider wild card
        :param number_of_cards
        :return: all combinations of cards
        """
        moves = []
        for k, v in self.cards_dict.items():
            if len(v) >= number_of_cards:  # combinations without wildcard
                moves += list(map(list, itertools.combinations(v, number_of_cards)))
            if self.wild_card_of_game in self.cards_list:  # with one wildcard
                for k1, v1 in self.cards_dict.items():
                    if k1 != EnvCard2Rank[self.wild_card_of_game]:
                        list_of_combination = list(map(list, itertools.combinations(v1, number_of_cards - 1)))
                        for i1 in range(len(list_of_combination)):
                            moves.append(list_of_combination[i1] + [self.wild_card_of_game])
            if self.cards_list.count(self.wild_card_of_game) == 2:  # with 2 wildcards
                for k1, v1 in self.cards_dict.items():
                    if k1 != EnvCard2Rank[self.wild_card_of_game]:
                        list_of_combination = list(map(list, itertools.combinations(v1, number_of_cards - 2)))
                        for i1 in range(len(list_of_combination)):
                            moves.append(
                                list_of_combination[i1] + [self.wild_card_of_game] + [self.wild_card_of_game])
            moves = [list(t) for t in set(tuple(p) for p in moves)]  # make all moves unique
        return moves

    def gen_type_3_triple(self):
        self.triple_cards_moves = self._cards_with_same_rank_with_wild_card(number_of_cards=3)
        return self.triple_cards_moves

    def gen_type_8_bomb_4(self):
        self.bomb_4_moves = self._cards_with_same_rank_with_wild_card(number_of_cards=4)
        return self.bomb_4_moves

    def gen_type_9_bomb_5(self):
        self.bomb_5_moves = self._cards_with_same_rank_with_wild_card(number_of_cards=5)
        return self.bomb_5_moves

    def gen_type_11_bomb_6(self):
        self.bomb_6_moves = self._cards_with_same_rank_with_wild_card(number_of_cards=6)
        return self.bomb_6_moves

    def gen_type_12_bomb_7(self):
        self.bomb_7_moves = self._cards_with_same_rank_with_wild_card(number_of_cards=7)
        return self.bomb_7_moves

    def gen_type_13_bomb_8(self):
        self.bomb_8_moves = self._cards_with_same_rank_with_wild_card(number_of_cards=8)
        return self.bomb_8_moves

    def gen_type_14_joker_bomb(self):
        self.joker_bomb_moves = []
        if (52 in self.cards_list and 53 in self.cards_list and
                self.cards_list.count(52) == 2 and self.cards_list.count(53) == 2):
            self.joker_bomb_moves.append([52, 52, 53, 53])
        return self.joker_bomb_moves
    # def test(self):
    #     print(self.card_dict)


test_hand = MoveGenerator([2, 3, 3, 4, 6, 6], wild_card_of_game=3)
# test_hand.test()
print(len(test_hand.find_wild_card_in_hand()))
print(test_hand.joker_bomb_moves)
print(test_hand.cards_dict)
print(test_hand.pair_moves)
print(test_hand.triple_cards_moves)
print(test_hand.wild_card_of_game)
