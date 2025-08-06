import collections
import itertools
from environment.utils import list_combinations, make_it_unique
from environment.utils import EnvCard2Rank, EnvCard2Suit


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
        self.straight_flush_moves = []
        self.gen_type_10_straight_flush()
        self._3_2_moves = []
        self.gen_type_4_3_2()
        self.serial_pair_moves = []
        self.gen_type_6_serial_pair()
        self.serial_triple_moves = []
        self.gen_type_7_serial_triple()

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
                self.pair_moves += list_combinations(v, 2)
            if self.wild_card_of_game in self.cards_list:
                for k1, v1 in self.cards_dict.items():
                    if k1 != EnvCard2Rank[self.wild_card_of_game] and k1 != 15 and k1 != 16:
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
                moves += list_combinations(v, number_of_cards)
            if self.wild_card_of_game in self.cards_list:  # with one wildcard
                for k1, v1 in self.cards_dict.items():
                    if k1 != EnvCard2Rank[self.wild_card_of_game] and k1 != 15 and k1 != 16:
                        list_of_combination = list_combinations(v1, number_of_cards - 1)
                        for i1 in range(len(list_of_combination)):
                            moves.append(list_of_combination[i1] + [self.wild_card_of_game])
            if self.cards_list.count(self.wild_card_of_game) == 2:  # with 2 wildcards
                for k1, v1 in self.cards_dict.items():
                    if k1 != EnvCard2Rank[self.wild_card_of_game] and k1 != 15 and k1 != 16:
                        list_of_combination = list_combinations(v1, number_of_cards - 2)
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

    def gen_type_10_straight_flush(self):
        self.straight_flush_moves = []
        for straight in self.straight_moves:
            non_wildcard_cards = []
            suit_list = []
            for card in straight:
                if card != self.wild_card_of_game:
                    non_wildcard_cards.append(card)
            for card in non_wildcard_cards:
                suit_list.append(EnvCard2Suit[card])
            is_straight_flush = len(set(suit_list)) == 1
            if is_straight_flush:
                self.straight_flush_moves.append(straight)
        return self.straight_flush_moves

    def gen_type_4_3_2(self):
        self._3_2_moves = []
        combinations = [list(combination) for combination in
                        list(itertools.product(self.triple_cards_moves, self.pair_moves))]
        # the card on the position 0 determines the rank of the triple
        legal_combinations = [combination for combination in combinations if
                              EnvCard2Rank[combination[0][0]] != EnvCard2Rank[combination[1][0]]]
        legal_combinations = [sorted(combination[0] + combination[1]) for combination in legal_combinations]
        legal_combinations = [combination for combination in legal_combinations if
                              combination.count(self.wild_card_of_game) <= self.number_of_wild_cards]
        self._3_2_moves = [list(combination) for combination in
                           list(set([tuple(combination) for combination in legal_combinations]))]
        return self._3_2_moves

    def gen_type_6_serial_pair(self):
        self.serial_pair_moves = self._gen_series(self.pair_moves, sequence_length=3)
        return self.serial_pair_moves

    def gen_type_7_serial_triple(self):
        self.serial_triple_moves = self._gen_series(self.triple_cards_moves, sequence_length=2)
        return self.serial_triple_moves

    def _gen_series(self, components: list, sequence_length: int = 2):
        """
        generate series based on existing moves such as triples or pairs
        sequence_length means the length of rank in the series, 2 for '333444' and 3 for '334455'
        """
        moves = []
        sorted_components = sorted(components, key=lambda x: (EnvCard2Rank[x[0]], x[0]))
        components_dict = collections.defaultdict(list)
        for i in sorted_components:
            if 14 >= EnvCard2Rank[i[0]] >= 2:
                components_dict[EnvCard2Rank[i[0]]].append(i)
        components_dict[1] = components_dict[14]
        existing_series_start = []
        for i in range(1, 16 - sequence_length):
            if all(k in components_dict.keys() for k in [i + k for k in range(0, sequence_length)]):
                existing_series_start.append(i)
        for i in existing_series_start:
            ranks = [i + offset for offset in range(0, sequence_length)]
            cards = [components_dict[k] for k in ranks]
            combinations = list(itertools.product(*cards))

            combinations = [sorted([item for group in combination for item in group]) for combination in combinations]
            legal_combinations = [combination for combination in combinations if
                                  combination.count(self.wild_card_of_game) <= self.number_of_wild_cards]
            moves += legal_combinations

        moves = make_it_unique(moves)
        return moves

    def gen_moves(self):
        moves = []
        moves.extend(self.gen_type_1_single())
        moves.extend(self.gen_type_2_pair())
        moves.extend(self.gen_type_3_triple())
        moves.extend(self.gen_type_4_3_2())
        moves.extend(self.gen_type_5_straight())
        moves.extend(self.gen_type_6_serial_pair())
        moves.extend(self.gen_type_7_serial_triple())
        moves.extend(self.gen_type_8_bomb_4())
        moves.extend(self.gen_type_9_bomb_5())
        moves.extend(self.gen_type_10_straight_flush())
        moves.extend(self.gen_type_11_bomb_6())
        moves.extend(self.gen_type_12_bomb_7())
        moves.extend(self.gen_type_13_bomb_8())
        moves.extend(self.gen_type_14_joker_bomb())
        return moves
