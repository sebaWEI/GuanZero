import collections
from move_detector import get_move_info

def common_handle(moves, rival_move):
    new_moves = list()
    rival_move_rank = get_move_info(rival_move).rank
    for move in moves:
        move_rank = get_move_info(move).rank
        if move_rank > rival_move_rank:
            new_moves.append(move)
    return new_moves

def filter_type_1_single(moves, rival_move):
    return common_handle(moves, rival_move)

def filter_type_2_pair(moves, rival_move):
    return common_handle(moves, rival_move)

def filter_type_three_triple(moves, rival_move):
    return common_handle(moves, rival_move)



