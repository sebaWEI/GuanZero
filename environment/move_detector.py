import collections
from environment.utils import *

def get_move_type(move, wild_card_of_game=1):
    move_size = len(move)
    move_dict = collections.defaultdict(list)
    for i in move:
        move_dict[EnvCard2Rank[i]].append(i)

    move_without_wildcard = sorted([card for card in move if card != wild_card_of_game])
    number_of_wild_cards = len(move) - len(move_without_wildcard)
    move_dict_without_wildcard = collections.defaultdict(list)
    for i in move_without_wildcard:
        move_dict_without_wildcard[EnvCard2Rank[i]].append(i)
    rank2number = collections.defaultdict(int)
    for i in move_dict_without_wildcard.keys():
        rank2number[i] = len(move_dict_without_wildcard[i])
    number2rank = collections.defaultdict(list)
    for k, v in rank2number.items():
        number2rank[v] += [k]
                                #number2rank and rank2number both put the wild card out of the game 
    if move_size == 0:
        return {'type': TYPE_0_PASS,'rank': None}

    if move_size == 1:
        return {'type': TYPE_1_SINGLE, 'rank': EnvCard2Rank[move[0]]}

    if move_size == 2:
        if EnvCard2Rank[move[0]] == EnvCard2Rank[move[1]] :
            return {'type': TYPE_2_PAIR, 'rank': EnvCard2Rank[move[0]]}
        elif move[0] == wild_card_of_game and move[1] != 52 and move[1] != 53:
            return {'type': TYPE_2_PAIR, 'rank': EnvCard2Rank[move[1]]}
        elif move[1] == wild_card_of_game and move[0] != 52 and move[0] != 53:
            return {'type': TYPE_2_PAIR, 'rank': EnvCard2Rank[move[0]]}
        else:
            return {'type': TYPE_15_WRONG,'rank': None}

    if move_size == 3:
        if number_of_wild_cards <= 2 and len(move_dict_without_wildcard) == 1 and \
                list(move_dict_without_wildcard.keys())[0] != 15 and list(move_dict_without_wildcard.keys())[0] != 16:
            return {'type': TYPE_3_TRIPLE, 'rank': EnvCard2Rank[move_without_wildcard[0]]}
        else:
            return {'type': TYPE_15_WRONG, 'rank': None}

    if move_size == 4:
        if len(move_dict[15]) == 2 and len(move_dict[16]) == 2:
            return {'type': TYPE_14_JOKER_BOMB, 'rank': 15}
        if number_of_wild_cards <= 2 and len(move_dict_without_wildcard) == 1 and \
                list(move_dict_without_wildcard.keys())[0] != 15 and list(move_dict_without_wildcard.keys())[0] != 16:
            return {'type': TYPE_8_BOMB_4, 'rank': EnvCard2Rank[move_without_wildcard[0]]}
        else:
            return {'type': TYPE_15_WRONG, 'rank': None}

    if move_size == 5:
        if number_of_wild_cards <= 2 and len(move_dict_without_wildcard) == 1:
            return {'type': TYPE_9_BOMB_5, 'rank': EnvCard2Rank[move_without_wildcard[0]]}
        if any(x in move for x in Rank2EnvCard[14]) and (len(move_dict_without_wildcard) == 5 - number_of_wild_cards):#check if there is a A
            if len([card for card in move_without_wildcard if card in Rank2EnvCard[2] + Rank2EnvCard[3] \
                    + Rank2EnvCard[4] + Rank2EnvCard[5]]) + number_of_wild_cards == 4:
                suit_dict = collections.defaultdict(list)
                for i in move_without_wildcard:
                    suit_dict[EnvCard2Suit[i]].append(i)
                if len(suit_dict) == 1:
                    return {'type': TYPE_10_STRAIGHT_FLUSH, 'rank': 1}#12345
                else:
                    return {'type': TYPE_5_STRAIGHT, 'rank': 1}
            if len([card for card in move_without_wildcard if card in Rank2EnvCard[10] + Rank2EnvCard[11] \
                    + Rank2EnvCard[12] + Rank2EnvCard[13]]) + number_of_wild_cards == 4:
                suit_dict = collections.defaultdict(list)
                for i in move_without_wildcard:
                    suit_dict[EnvCard2Suit[i]].append(i)
                if len(suit_dict) == 1:
                    return {'type': TYPE_10_STRAIGHT_FLUSH, 'rank': 10}
                else:
                    return {'type': TYPE_5_STRAIGHT, 'rank': 10}#10,11,12,13,14
                
        if (len(move_dict_without_wildcard) == 5 - number_of_wild_cards) and (
                2 <= EnvCard2Rank[move_without_wildcard[0]] < EnvCard2Rank[move_without_wildcard[-1]] <= 14) and (
                EnvCard2Rank[move_without_wildcard[-1]] - EnvCard2Rank[move_without_wildcard[0]] <= 4):
            suit_dict = collections.defaultdict(list)
            for i in move_without_wildcard:
                suit_dict[EnvCard2Suit[i]].append(i)
            if [EnvCard2Rank[card] for card in move_without_wildcard]==[11,12,13]:#check if the move is a special case of xxJQK
                if len(suit_dict) == 1:
                    return {'type': TYPE_10_STRAIGHT_FLUSH, 'rank': 10}
                return {'type': TYPE_5_STRAIGHT, 'rank': 10}#xxJQK
            if len(suit_dict) == 1:
                return {'type': TYPE_10_STRAIGHT_FLUSH, 'rank': EnvCard2Rank[move_without_wildcard[0]]}
            return {'type': TYPE_5_STRAIGHT, 'rank': EnvCard2Rank[move_without_wildcard[0]]}
            

        if len(move_dict_without_wildcard) == 2 and sorted(rank2number.values()) == [2, 3]:
            rank = [k for k, v in rank2number.items() if v == 3][0]
            return {'type': TYPE_4_3_2, 'rank': rank}
        if number_of_wild_cards == 1 and len(
                move_dict_without_wildcard) == 2 and list(rank2number.values()) == [2, 2]:
            if (15 in number2rank[2]) or (16 in number2rank[2]):
                rank = [rank for rank in number2rank[2] if rank != 15 and rank != 16][0]
                if rank is None:
                    return {'type': TYPE_15_WRONG, 'rank': None}
                else:
                    return {'type': TYPE_4_3_2, 'rank': rank}
            else:
                rank = max(list(rank2number.keys()))
                return {'type': TYPE_4_3_2, 'rank': rank}
        if number_of_wild_cards == 1 and len(move_dict_without_wildcard) == 2 and sorted(
                list(rank2number.values())) == [1, 3]:
            rank = [k for k, v in move_dict_without_wildcard.items() if len(v) == 3][0]
            return {'type': TYPE_4_3_2, 'rank': rank}
        if number_of_wild_cards == 2 and len(move_dict_without_wildcard) == 1:
            rank = EnvCard2Rank[move_without_wildcard[0]]
            return {'type': TYPE_4_3_2, 'rank': rank}#this case should not be detected as 4-3-2,cause it is a bomb
        if number_of_wild_cards == 2 and len(move_dict_without_wildcard) == 2:
            if 15 in list(rank2number.keys()) or 16 in list(rank2number.keys()):
                rank = [rank for rank in list(rank2number.keys()) if rank != 15 and rank != 16][0]
                return {'type': TYPE_4_3_2, 'rank': rank}#this case should not be detected as 4-3-2,cause
            else:
                rank = max(list(rank2number.keys()))
                return {'type': TYPE_4_3_2, 'rank': rank}#need to check 53 pair
        else:
            return {'type': TYPE_15_WRONG}

    if move_size == 6:
        if number_of_wild_cards <= 2 and len(move_dict_without_wildcard) == 1:
            return {'type': TYPE_11_BOMB_6, 'rank': EnvCard2Rank[move_without_wildcard[0]]}
        sorted_move_without_wild_card = sorted(move_without_wildcard)
        sorted_rank_without_wild_card = [EnvCard2Rank[card] for card in sorted_move_without_wild_card]
        
        if sorted_rank_without_wild_card[-1] == 14:#check the special case of 6 cards,rank is special
            if  len(number2rank[2]) == 3 and sorted(rank2number.keys()) == [2, 3, 14]:
                return {'type': TYPE_6_SERIAL_PAIR, 'rank': 1}
            if len(number2rank[2] ) == 3 and sorted(rank2number.keys()) == [12, 13, 14]:
                return {'type': TYPE_6_SERIAL_PAIR, 'rank': 12}
            if len(number2rank[3]) == 2 and sorted(rank2number.keys()) == [2, 14]:
                return {'type': TYPE_7_SERIAL_TRIPLE, 'rank': 1}
            if len(number2rank[3]) == 2 and sorted(rank2number.keys()) == [13, 14]:
                return {'type': TYPE_7_SERIAL_TRIPLE, 'rank': 13}
            
            if number_of_wild_cards == 1 :
                if len(number2rank[2]) == 2 and sorted(rank2number.keys()) == [2, 3, 14]:
                    return {'type': TYPE_6_SERIAL_PAIR, 'rank': 1}
                if len(number2rank[2]) == 2 and sorted(rank2number.keys()) == [12, 13, 14]:
                    return {'type': TYPE_6_SERIAL_PAIR, 'rank': 12}
                if len(number2rank[3]) == 1 and sorted(rank2number.keys()) == [2, 14]:
                    return {'type': TYPE_7_SERIAL_TRIPLE, 'rank': 1}
                if len(number2rank[3]) == 1 and sorted(rank2number.keys()) == [13, 14]:
                    return {'type': TYPE_7_SERIAL_TRIPLE, 'rank': 13}
                
            if number_of_wild_cards == 2:
                if sorted(rank2number.keys()) == [2, 3, 14]:
                    return {'type': TYPE_6_SERIAL_PAIR, 'rank': 1}
                if sorted(rank2number.keys()) == [12, 13, 14]:
                    return {'type': TYPE_6_SERIAL_PAIR, 'rank': 12}
                if sorted(rank2number.keys()) == [2, 14] and len(number2rank[2]) != 2:
                    return {'type': TYPE_7_SERIAL_TRIPLE, 'rank': 1}
                if sorted(rank2number.keys()) == [13, 14] and len(number2rank[2]) != 2:
                    return {'type': TYPE_7_SERIAL_TRIPLE, 'rank': 13}
                if len(rank2number.keys()) == 2 and len(number2rank[2]) == 2:
                    if sorted(rank2number.keys()) == [2, 14]:
                        return {'type': [TYPE_7_SERIAL_TRIPLE,TYPE_6_SERIAL_PAIR], 'rank': 1}
                    if sorted(rank2number.keys()) == [13, 14]:
                        return {'type': [TYPE_7_SERIAL_TRIPLE,TYPE_6_SERIAL_PAIR], 'rank': [13,12]}
                    if sorted(rank2number.keys()) == [3, 14]:
                        return {'type': TYPE_6_SERIAL_PAIR, 'rank': 1}
                    if sorted(rank2number.keys()) == [12, 14]:
                        return {'type': TYPE_6_SERIAL_PAIR, 'rank': 12}
        
        if number_of_wild_cards == 0 :#check the normal case of 6 cards while wild card number is 0
            if 2 in number2rank and len(number2rank[2]) == 3 and sorted(number2rank.values())[0][0]+2 == sorted(number2rank.values())[0][1]+1 == sorted(number2rank.values())[0][2]\
                      and sorted(number2rank.values())[0][2]<=14 :
                    return {'type': TYPE_6_SERIAL_PAIR, 'rank': sorted_rank_without_wild_card[0]}#223344
            if len(number2rank[3]) == 2 and sorted(number2rank.values())[0][0]+1 == sorted(number2rank.values())[0][1]\
                      and sorted(number2rank.values())[0][1]<=14 :
                return {'type': TYPE_7_SERIAL_TRIPLE, 'rank': sorted_rank_without_wild_card[0]}#222333

        if number_of_wild_cards == 1:
            if sorted(rank2number.values()) == [1,2,2] and sorted(number2rank.values())[0][0]+2 == sorted(number2rank.values())[1][0]+1 == sorted(number2rank.values())[1][1]\
                      and sorted(number2rank.values())[1][1]<=14 :
                return {'type': TYPE_6_SERIAL_PAIR, 'rank': sorted_rank_without_wild_card[0]}#22334x
            if sorted(rank2number.values()) == [2,3] and sorted(number2rank.values())[0][0]+1 == sorted(number2rank.values())[1][0]\
                        and sorted(number2rank.values())[1][0]<=14:
                return {'type': TYPE_7_SERIAL_TRIPLE, 'rank': sorted_rank_without_wild_card[0]}#22233x
            
        if number_of_wild_cards == 2:
            if sorted(rank2number.values())==[1,1,2] and sorted(number2rank.values())[0][0]+2 == sorted(number2rank.values())[0][1]+1 == sorted(number2rank.values())[1][0]\
                      and sorted(number2rank.values())[1][0]<=14:
                return {'type': TYPE_6_SERIAL_PAIR, 'rank': sorted_rank_without_wild_card[0]}#2x3x44
            if sorted(rank2number.values()) == [1,3] and sorted(number2rank.values())[0][0]+1 == sorted(number2rank.values())[1][0] \
                      and sorted(number2rank.values())[1][0]<=14:
                return {'type': TYPE_7_SERIAL_TRIPLE, 'rank': sorted_rank_without_wild_card[0]}#2223xx
            if sorted(rank2number.values()) == [2,2] and sorted(number2rank.values())[0][0]+1 == sorted(number2rank.values())[0][1] \
                      and sorted(number2rank.values())[0][1]<=14:
                return {'type': [TYPE_6_SERIAL_PAIR,TYPE_7_SERIAL_TRIPLE], 'rank': sorted_rank_without_wild_card[0]}#2233xx and 22x33x
            if sorted(rank2number.values()) == [2,2] and sorted(number2rank.values())[0][0]+2 == sorted(number2rank.values())[0][1] \
                      and sorted(number2rank.values())[0][1]<=14:
                return {'type': TYPE_6_SERIAL_PAIR, 'rank': sorted_rank_without_wild_card[0]}#22xx44

        else:
            return {'type': TYPE_15_WRONG,'rank':None}

    if move_size == 7:
        if number_of_wild_cards <= 2 and len(move_dict_without_wildcard) == 1:
            return {'type': TYPE_12_BOMB_7, 'rank': EnvCard2Rank[move_without_wildcard[0]]}
    if move_size == 8:
        if number_of_wild_cards <= 2 and len(move_dict_without_wildcard) == 1:
            return {'type': TYPE_13_BOMB_8, 'rank': EnvCard2Rank[move_without_wildcard[0]]}
