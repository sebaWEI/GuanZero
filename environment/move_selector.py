# under the same card type, select all moves that are larger than rival move
from .move_detector import get_move_info


def common_filter(moves, rival_move):
    new_moves = list()
    rival_move_rank = get_move_info(rival_move)['rank']
    for move in moves:
        move_rank = get_move_info(move)['rank']
        if move_rank is None:
            new_moves.append(move)
        elif move_rank > rival_move_rank:
            new_moves.append(move)
    return new_moves


def common_filter_with_conditional_statement(moves, rival_move):
    new_moves = []
    rival_move_rank = get_move_info(rival_move)['rank']
    for move in moves:
        move_info = get_move_info(move)
        move_rank = move_info['rank']
        move_type = move_info['type']

        if move_rank is None:
            new_moves.append(move)
        elif isinstance(rival_move_rank, int) and isinstance(move_rank, int):
            if move_rank > rival_move_rank:
                new_moves.append(move)
        elif isinstance(rival_move_rank, int) and move_type == [7, 6]:
            new_moves.append(move)

    return new_moves
