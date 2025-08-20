import itertools

# global parameters

# action types
TYPE_0_PASS = 0
TYPE_1_SINGLE = 1
TYPE_2_PAIR = 2
TYPE_3_TRIPLE = 3
TYPE_4_3_2 = 4
TYPE_5_STRAIGHT = 5
TYPE_6_SERIAL_PAIR = 6  # 556677
TYPE_7_SERIAL_TRIPLE = 7  # 555666
TYPE_8_BOMB_4 = 8
TYPE_9_BOMB_5 = 9
TYPE_10_STRAIGHT_FLUSH = 10
TYPE_11_BOMB_6 = 11
TYPE_12_BOMB_7 = 12
TYPE_13_BOMB_8 = 13
TYPE_14_JOKER_BOMB = 14
TYPE_15_WRONG = 15

Typenum2RealType = {
    0: 'pass',
    1: 'single',
    2: 'pair',
    3: 'triple',
    4: '3 + 2',
    5: 'straight',
    6: 'serial pair',
    7: 'serial triple',
    8: '4 * bomb',
    9: '5 * bomb',
    10: 'straight flush',
    11: '6 * bomb',
    12: '7 * bomb',
    13: '8 * bomb',
    14: 'joker bomb',
    15: 'type error'
}


# return all possible results of selecting num cards from cards list
def list_combinations(cards, num):
    combinations = [list(i) for i in list(set(itertools.combinations(cards, num)))]
    return combinations


def make_it_unique(repetitive_list):
    unique_list = list(set([tuple(sorted(i)) for i in repetitive_list]))
    unique_and_ordered_list = [list(i) for i in unique_list]
    return unique_and_ordered_list


RealCard2EnvCard = {'2S': 0, '2H': 1, '2C': 2, '2D': 3,
                    '3S': 4, '3H': 5, '3C': 6, '3D': 7,
                    '4S': 8, '4H': 9, '4C': 10, '4D': 11,
                    '5S': 12, '5H': 13, '5C': 14, '5D': 15,
                    '6S': 16, '6H': 17, '6C': 18, '6D': 19,
                    '7S': 20, '7H': 21, '7C': 22, '7D': 23,
                    '8S': 24, '8H': 25, '8C': 26, '8D': 27,
                    '9S': 28, '9H': 29, '9C': 30, '9D': 31,
                    '10S': 32, '10H': 33, '10C': 34, '10D': 35,
                    'JS': 36, 'JH': 37, 'JC': 38, 'JD': 39,
                    'QS': 40, 'QH': 41, 'QC': 42, 'QD': 43,
                    'KS': 44, 'KH': 45, 'KC': 46, 'KD': 47,
                    'AS': 48, 'AH': 49, 'AC': 50, 'AD': 51,
                    'X': 52, 'D': 53}

EnvCard2RealCard = {0: '2S', 1: '2H', 2: '2C', 3: '2D',
                    4: '3S', 5: '3H', 6: '3C', 7: '3D',
                    8: '4S', 9: '4H', 10: '4C', 11: '4D',
                    12: '5S', 13: '5H', 14: '5C', 15: '5D',
                    16: '6S', 17: '6H', 18: '6C', 19: '6D',
                    20: '7S', 21: '7H', 22: '7C', 23: '7D',
                    24: '8S', 25: '8H', 26: '8C', 27: '8D',
                    28: '9S', 29: '9H', 30: '9C', 31: '9D',
                    32: '10S', 33: '10H', 34: '10C', 35: '10D',
                    36: 'JS', 37: 'JH', 38: 'JC', 39: 'JD',
                    40: 'QS', 41: 'QH', 42: 'QC', 43: 'QD',
                    44: 'KS', 45: 'KH', 46: 'KC', 47: 'KD',
                    48: 'AS', 49: 'AH', 50: 'AC', 51: 'AD',
                    52: 'X', 53: 'D'}

EnvCard2Rank = {0: 2, 1: 2, 2: 2, 3: 2,
                4: 3, 5: 3, 6: 3, 7: 3,
                8: 4, 9: 4, 10: 4, 11: 4,
                12: 5, 13: 5, 14: 5, 15: 5,
                16: 6, 17: 6, 18: 6, 19: 6,
                20: 7, 21: 7, 22: 7, 23: 7,
                24: 8, 25: 8, 26: 8, 27: 8,
                28: 9, 29: 9, 30: 9, 31: 9,
                32: 10, 33: 10, 34: 10, 35: 10,
                36: 11, 37: 11, 38: 11, 39: 11,
                40: 12, 41: 12, 42: 12, 43: 12,
                44: 13, 45: 13, 46: 13, 47: 13,
                48: 14, 49: 14, 50: 14, 51: 14,
                52: 15, 53: 16}

Rank2EnvCard = {2: [0, 1, 2, 3],
                3: [4, 5, 6, 7],
                4: [8, 9, 10, 11],
                5: [12, 13, 14, 15],
                6: [16, 17, 18, 19],
                7: [20, 21, 22, 23],
                8: [24, 25, 26, 27],
                9: [28, 29, 30, 31],
                10: [32, 33, 34, 35],
                11: [36, 37, 38, 39],
                12: [40, 41, 42, 43],
                13: [44, 45, 46, 47],
                14: [48, 49, 50, 51],
                15: [52],
                16: [53]}

EnvCard2Suit = {0: 'S', 1: 'H', 2: 'C', 3: 'D',
                4: 'S', 5: 'H', 6: 'C', 7: 'D',
                8: 'S', 9: 'H', 10: 'C', 11: 'D',
                12: 'S', 13: 'H', 14: 'C', 15: 'D',
                16: 'S', 17: 'H', 18: 'C', 19: 'D',
                20: 'S', 21: 'H', 22: 'C', 23: 'D',
                24: 'S', 25: 'H', 26: 'C', 27: 'D',
                28: 'S', 29: 'H', 30: 'C', 31: 'D',
                32: 'S', 33: 'H', 34: 'C', 35: 'D',
                36: 'S', 37: 'H', 38: 'C', 39: 'D',
                40: 'S', 41: 'H', 42: 'C', 43: 'D',
                44: 'S', 45: 'H', 46: 'C', 47: 'D',
                48: 'S', 49: 'H', 50: 'C', 51: 'D',
                52: 'X', 53: 'D'}
