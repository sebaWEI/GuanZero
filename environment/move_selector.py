# under the same card type, select all moves that are larger than rival move
from .move_detector import get_move_info


def common_filter(moves, rival_move):
    new_moves = list()
    rival_move_rank = get_move_info(rival_move)['rank']
    for move in moves:
        move_rank = get_move_info(move)['rank']
        if move_rank > rival_move_rank:
            new_moves.append(move)
    return new_moves


def common_filter_with_conditional_statement(moves, rival_move):
    new_moves = list()
    rival_move_rank = get_move_info(rival_move)['rank']
    for move in moves:
        move_rank = get_move_info(move)['rank']
        move_type = get_move_info(move)['type']
        if isinstance(rival_move_rank, int) and isinstance(move_rank, int):
            if move_rank > rival_move_rank:
                new_moves.append(move)
        elif isinstance(rival_move_rank, int) and move_type == [7, 6]:  # KKAAww
            new_moves.append(move)
    return new_moves
