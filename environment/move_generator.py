import collections
import itertools
from environment.utils import select
from environment.utils import RealCard2EnvCard, EnvCard2RealCard, EnvCard2Rank, EnvCard2Suit


class MoveGenerator(object):
    """
    Generate possible combinations.
    """

    def __init__(self, cards_list, wild_card_of_game=1):

        self.cards_list = cards_list
        self.cards_dict = collections.defaultdict(list)
        for i in self.cards_list:
            self.cards_dict[EnvCard2Rank[i]].append(i)

        self.wild_card_of_game = wild_card_of_game
        self.wild_cards_in_hand = []
        self.number_of_wild_cards: int = 0
        self.find_wild_card_in_hand()
        self.cards_list_without_wild_cards = [x for x in self.cards_list if x != self.wild_card_of_game]
        self.cards_dict_without_wild_cards = collections.defaultdict(list)
        for i in self.cards_list_without_wild_cards:
            self.cards_dict_without_wild_cards[EnvCard2Rank[i]].append(i)

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
        self.straight_moves = []
        self.gen_type_5_straight()

    def find_wild_card_in_hand(self):
        self.wild_cards_in_hand = []
        self.number_of_wild_cards: int = 0
        for i in self.cards_list:
            if self.wild_card_of_game == i:
                self.wild_cards_in_hand.append([i])
        self.number_of_wild_cards = len(self.wild_cards_in_hand)
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
                self.pair_moves += select(v, 2)
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
        Build all **same-rank** hands of a requested length, **allowing wild cards**
        to substitute for missing cards of that rank.

        Parameters
        ----------
        number_of_cards : int
        Desired hand size (must be ≥ 3).
        E.g. 4 for a bomb, 3 for triple etc.

        Returns
        -------
        List[List[Card]]
        Every possible combination that meets the criteria; each inner list
        contains `number_of_cards` cards of identical rank, with wild cards
        """
        moves = []
        for k, v in self.cards_dict.items():
            if len(v) >= number_of_cards:  # combinations without wildcard
                moves += select(v, number_of_cards)
            if self.wild_card_of_game in self.cards_list:  # with one wildcard
                for k1, v1 in self.cards_dict.items():
                    if k1 != EnvCard2Rank[self.wild_card_of_game]:
                        list_of_combination = select(v1, number_of_cards - 1)
                        for i1 in range(len(list_of_combination)):
                            moves.append(list_of_combination[i1] + [self.wild_card_of_game])
            if self.cards_list.count(self.wild_card_of_game) == 2:  # with 2 wildcards
                for k1, v1 in self.cards_dict.items():
                    if k1 != EnvCard2Rank[self.wild_card_of_game]:
                        list_of_combination = select(v1, number_of_cards - 2)
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

    def straight_continuity_check(self):

        cards_rank = []
        for i in self.cards_list_without_wild_cards:
            cards_rank.append(EnvCard2Rank[i])
            cards_rank = [x for x in cards_rank if isinstance(x, int)]
        cards_rank = sorted(set(cards_rank))

        if 14 in cards_rank:
            cards_rank.append(1)
            cards_rank = sorted(cards_rank)

        legal_straight_set = []
        for start in range(1, 11):
            legal_straight_set.append([start, start + 1, start + 2, start + 3, start + 4])

        existing_straight = []

        for legal_straight in legal_straight_set:
            is_subset = set(legal_straight).issubset(cards_rank)
            if is_subset:
                if legal_straight[0] == 1:
                    legal_straight[0] = 14
                existing_straight.append(legal_straight)
            else:
                missing = list(set(legal_straight) - set(cards_rank))
                if self.number_of_wild_cards >= len(missing) >= 1:
                    filled_straight = self.fill_with_wild_cards(legal_straight)
                    if filled_straight[0] == 1:
                        filled_straight[0] = 14
                    existing_straight.append(filled_straight)
        return existing_straight

    def fill_with_wild_cards(self, target_seq):
        rank_exists = {}
        for rank in range(2, 15):
            if rank in self.cards_dict_without_wild_cards.keys():
                rank_exists[rank] = 1
            else:
                rank_exists[rank] = 0
        rank_exists[1] = rank_exists[14]

        result = []
        wild_cards_remain = self.number_of_wild_cards
        for card in target_seq:
            if rank_exists[card] == 1:
                result.append(card)
            elif wild_cards_remain > 0:
                result.append('w')
                wild_cards_remain -= 1
            elif wild_cards_remain == 0:
                return None
        return result

    def gen_type_5_straight(self):
        self.straight_moves = []
        existing_straight_list = self.straight_continuity_check()
        for existing_straight in existing_straight_list:
            cards_list = []
            for rank in existing_straight:
                if isinstance(rank, int):
                    cards = self.cards_dict_without_wild_cards[rank]
                    cards_list.append(cards)
                elif rank == 'w':
                    cards = [self.wild_card_of_game]
                    cards_list.append(cards)
            combinations_of_one_straight = [tuple(sorted(list(straight))) for straight in
                                            list(itertools.product(*cards_list))]
            self.straight_moves += combinations_of_one_straight
        self.straight_moves = list(set(self.straight_moves))
        self.straight_moves = [list(straight_move) for straight_move in self.straight_moves]
        return self.straight_moves


test_hand = MoveGenerator([3, 3, 24, 28, 32, 48, 4, 8, 12], wild_card_of_game=3)
# test_hand.test()

print(test_hand.joker_bomb_moves)
print(test_hand.cards_dict)
print(test_hand.pair_moves)
print(test_hand.triple_cards_moves)
print(test_hand.wild_card_of_game)
print(test_hand.straight_continuity_check())
print(test_hand.straight_moves)
