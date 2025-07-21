import collections
from utils import *


def get_move_type(move, wild_card_of_game=1):
    move_size = len(move)
    move_dict = collections.defaultdict(list)
    for i in move:
        move_dict[EnvCard2Rank[i]].append(i)

    move_without_wildcard = [card for card in move if card != wild_card_of_game]
    number_of_wild_cards = len(move) - len(move_without_wildcard)
    move_dict_without_wildcard = collections.defaultdict(list)
    for i in move_without_wildcard:
        move_dict_without_wildcard[EnvCard2Rank[i]].append(i)

    if move_size == 0:
        return {'type': TYPE_0_PASS}

    if move_size == 1:
        return {'type': TYPE_1_SINGLE, 'rank': EnvCard2Rank[move[0]]}

    if move_size == 2:
        if move[0] == wild_card_of_game:
            return {'type': TYPE_2_PAIR, 'rank': EnvCard2Rank[move[1]]}
        elif move[1] == wild_card_of_game:
            return {'type': TYPE_2_PAIR, 'rank': EnvCard2Rank[move[0]]}
        elif EnvCard2Rank[move[0]] == EnvCard2Rank[move[1]]:
            return {'type': TYPE_2_PAIR, 'rank': EnvCard2Rank[move[0]]}
        else:
            return {'type': TYPE_15_WRONG}

    if move_size == 3:

        if number_of_wild_cards <= 2 and len(move_dict_without_wildcard) == 1:
            return {'type': TYPE_3_TRIPLE, 'rank': EnvCard2Rank[move_without_wildcard[0]]}
        else:
            return {'type': TYPE_15_WRONG}

    if move_size == 4:
        if move_dict[52] == 2 and move_dict[53] == 2:
            return {'type': TYPE_14_JOKER_BOMB}
        if number_of_wild_cards <= 2 and len(move_dict_without_wildcard) == 1:
            return {'type': TYPE_8_BOMB_4, 'rank': EnvCard2Rank[move_without_wildcard[0]]}
        else:
            return {'type': TYPE_15_WRONG}

    if move_size == 5:
        # bomb5, 3_2, straight, straight flush
        pass
    if move_size == 6:
        # bomb6, serial pair, serial triple
        pass
    if move_size == 7:
        # bomb7
        pass
    if move_size == 8:
        # bomb8
        pass
    return move_dict


print(get_move_type([21, 22, 23]))
