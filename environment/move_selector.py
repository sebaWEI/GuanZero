# under the same card type, select all moves that are larger than rival move
from move_detector import get_move_info


def common_filter(moves, rival_move):
    new_moves = list()
    rival_move_rank = get_move_info(rival_move)['rank']
    rival_move_type = get_move_info(rival_move)['type']
    for move in moves:
        move_rank = get_move_info(move)['rank']
        if move_rank > rival_move_rank:
            new_moves.append(move)
    return new_moves
