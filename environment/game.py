from copy import deepcopy
from .move_generator import MovesGenerator
from . import move_detector as md, move_selector as ms


def get_team_mate(player):
    if player == 'player_1':
        return 'player_3'
    elif player == 'player_2':
        return 'player_4'
    elif player == 'player_3':
        return 'player_1'
    else:
        return 'player_2'


class GameEnv(object):
    def __init__(self, players, wild_card_of_game=1):
        self.wild_card_of_game = wild_card_of_game
        self.card_play_action_seq = []
        self.card_play_type_seq = []
        self.players_seq = []
        self.players_remain = ['player_1', 'player_2', 'player_3', 'player_4']

        self.game_over = False

        self.acting_player_position = None

        self.players = players

        self.info_sets = {'player_1': InfoSet('player_1'),
                          'player_2': InfoSet('player_2'),
                          'player_3': InfoSet('player_3'),
                          'player_4': InfoSet('player_4')}

        self.last_move = []
        self.last_two_moves = []

        self.num_wins = {'player_1': 0,
                         'player_2': 0,
                         'player_3': 0,
                         'player_4': 0}

        self.scores = {'player_1': 0,
                       'player_2': 0,
                       'player_3': 0,
                       'player_4': 0}

        self.played_cards = {'player_1': [],
                             'player_2': [],
                             'player_3': [],
                             'player_4': []}

        self.last_move_dict = {'player_1': [],
                               'player_2': [],
                               'player_3': [],
                               'player_4': []}

        self.game_info_set = None
        self.winner = None
        self.players_rank = {'player_1': None,
                             'player_2': None,
                             'player_3': None,
                             'player_4': None}
        self.bomb_num = 0
        self.last_pid = 'player_1'
        self.free_type_right = False
        self.no_free_type_right = False
        self.pending_free_type_check = False
        self.pending_round_start = 0
        self.out_players = []
        self.player_follows = None
        self.updated_position_outside = False

    def card_play_init(self, player_hand_dict):
        self.info_sets['player_1'].player_hand_cards = player_hand_dict['player_1']
        self.info_sets['player_2'].player_hand_cards = player_hand_dict['player_2']
        self.info_sets['player_3'].player_hand_cards = player_hand_dict['player_3']
        self.info_sets['player_4'].player_hand_cards = player_hand_dict['player_4']
        self.pass_acting_player_position()
        self.game_info_set = self.get_info_set()

    def game_done(self):
        if len(self.info_sets[self.acting_player_position].player_hand_cards) == 0:
            remain_before = len(self.players_remain)
            self.player_follows = self.players_remain[
                (self.players_remain.index(self.acting_player_position) + 1) % len(self.players_remain)]
            if remain_before == 4:
                self.winner = self.acting_player_position
                self.num_wins[self.acting_player_position] += 1
                self.scores[self.acting_player_position] += 3
            elif remain_before == 3:
                self.scores[self.acting_player_position] += 2
            elif remain_before == 2:
                self.scores[self.acting_player_position] += 1
            self.update_players_list(self.acting_player_position)

    def get_winner(self):
        return self.winner

    def get_winning_team(self):
        if self.game_over:
            if self.winner in ['player_1', 'player_3']:
                return 'team_1_3'
            elif self.winner in ['player_2', 'player_4']:
                return 'team_2_4'
            else:
                return None

    def get_last_valid_move(self):
        for move in reversed(self.card_play_action_seq):
            if len(move) != 0:
                return move
        return []

    def get_last_two_moves(self):
        last_two_moves = [[], []]
        for card in self.card_play_action_seq[-2:]:
            last_two_moves.insert(0, card)
            last_two_moves = last_two_moves[:2]
        return last_two_moves

    def pass_acting_player_position(self):
        if self.player_follows:
            self.acting_player_position = self.player_follows
            self.player_follows = None
        elif len(self.players_remain) == 4:
            if self.acting_player_position is None:
                self.acting_player_position = 'player_1'

            else:
                if self.acting_player_position == 'player_1':
                    self.acting_player_position = 'player_2'

                elif self.acting_player_position == 'player_2':
                    self.acting_player_position = 'player_3'

                elif self.acting_player_position == 'player_3':
                    self.acting_player_position = 'player_4'

                elif self.acting_player_position == 'player_4':
                    self.acting_player_position = 'player_1'

                else:
                    self.acting_player_position = 'player_1'

        elif len(self.players_remain) == 3:
            self.acting_player_position = self.players_remain[
                (self.players_remain.index(self.acting_player_position) + 1) % 3]

        elif len(self.players_remain) == 2:
            # Switch to the other remaining player
            other_player = [p for p in self.players_remain if p != self.acting_player_position]
            if other_player:
                self.acting_player_position = other_player[0]

        return self.acting_player_position

    def get_out_player_from_history(self):
        if self.out_players:
            return self.out_players[-1]
        return None

    def update_players_list(self, player_out=None):
        if player_out is None:
            player_out = self.players_remain[
                (self.players_remain.index(self.acting_player_position) - 1 + len(self.players_remain)) % len(
                    self.players_remain)]
        teammate = get_team_mate(player_out)

        if len(self.players_remain) == 4:
            self.players_rank[player_out] = 1
        elif len(self.players_remain) == 3:
            self.players_rank[player_out] = 2
        elif len(self.players_remain) == 2:
            self.players_rank[player_out] = 3

        self.out_players.append(player_out)

        # Remove player from remaining list
        self.players_remain.remove(player_out)

        for player in self.players_remain:
            self.info_sets[player].players_remain = self.players_remain

        if len(self.players_remain) == 3:
            self.pending_free_type_check = True
            self.pending_round_start = len(self.card_play_action_seq)
        elif len(self.players_remain) == 2:
            if teammate in self.players_remain:
                if teammate == self.players_remain[0]:
                    self.acting_player_position = teammate
                    self.updated_position_outside = True
                    self.free_type_right = True
            else:
                # Both teammates are out, game ends
                self.players_rank[self.players_remain[0]] = 3
                self.players_rank[self.players_remain[1]] = 4
                self.game_over = True
        elif len(self.players_remain) == 1:
            # Last player
            self.players_rank[player_out] = 3
            self.players_rank[self.players_remain[0]] = 4
            self.game_over = True

    def get_legal_card_play_actions(self):
        mg = MovesGenerator(
            self.info_sets[self.acting_player_position].player_hand_cards, wild_card_of_game=self.wild_card_of_game)

        action_sequence = self.card_play_action_seq
        type_sequence = self.card_play_type_seq

        rival_move = []
        rival_type = None

        if self.free_type_right:
            moves = mg.gen_moves()
            self.free_type_right = False
            return moves

        if len(self.players_remain) == 4 or self.no_free_type_right:
            self.no_free_type_right = False
            if len(action_sequence) != 0:
                if len(action_sequence[-1]) == 0:
                    if len(action_sequence[-2]) == 0:
                        rival_move = action_sequence[-3]
                        rival_type = type_sequence[-3]
                    else:
                        rival_move = action_sequence[-2]
                        rival_type = type_sequence[-2]
                else:
                    rival_move = action_sequence[-1]
                    rival_type = type_sequence[-1]
        elif len(self.players_remain) == 3 and self.no_free_type_right is False:
            if len(action_sequence) != 0:
                if len(action_sequence[-1]) == 0:
                    rival_move = action_sequence[-2]
                    rival_type = type_sequence[-2]
                else:
                    rival_move = action_sequence[-1]
                    rival_type = type_sequence[-1]
        elif len(self.players_remain) == 2:
            if len(action_sequence) != 0:
                rival_move = action_sequence[-1]
                rival_type = type_sequence[-1]

        rival_info = md.get_move_info(rival_move, wild_card_of_game=self.wild_card_of_game)
        rival_move_type = rival_info['type']
        moves = list()

        if rival_move_type == md.TYPE_0_PASS:
            moves = mg.gen_moves()

        elif rival_move_type == md.TYPE_1_SINGLE:
            all_moves = mg.gen_type_1_single()
            moves = ms.common_filter(all_moves, rival_move, wild_card_of_game=self.wild_card_of_game)

        elif rival_move_type == md.TYPE_2_PAIR:
            all_moves = mg.gen_type_2_pair()
            moves = ms.common_filter(all_moves, rival_move, wild_card_of_game=self.wild_card_of_game)

        elif rival_move_type == md.TYPE_3_TRIPLE:
            all_moves = mg.gen_type_3_triple()
            moves = ms.common_filter(all_moves, rival_move, wild_card_of_game=self.wild_card_of_game)

        elif rival_move_type == md.TYPE_4_3_2:
            all_moves = mg.gen_type_4_3_2()
            moves = ms.common_filter(all_moves, rival_move, wild_card_of_game=self.wild_card_of_game)

        elif rival_move_type == md.TYPE_5_STRAIGHT:
            all_moves = mg.gen_type_5_straight()
            moves = ms.common_filter(all_moves, rival_move, wild_card_of_game=self.wild_card_of_game)

        elif rival_move_type == md.TYPE_6_SERIAL_PAIR:
            all_moves = mg.gen_type_6_serial_pair()
            moves = ms.common_filter_with_conditional_statement(all_moves, rival_move,
                                                                wild_card_of_game=self.wild_card_of_game)

        elif rival_move_type == md.TYPE_7_SERIAL_TRIPLE:
            all_moves = mg.gen_type_7_serial_triple()
            moves = ms.common_filter_with_conditional_statement(all_moves, rival_move,
                                                                wild_card_of_game=self.wild_card_of_game)

        elif rival_move_type == [md.TYPE_6_SERIAL_PAIR, md.TYPE_7_SERIAL_TRIPLE]:
            if rival_type == md.TYPE_6_SERIAL_PAIR:
                all_moves = mg.gen_type_6_serial_pair()
                moves = ms.common_filter_with_conditional_statement(all_moves, rival_move,
                                                                    wild_card_of_game=self.wild_card_of_game)
            if rival_type == md.TYPE_7_SERIAL_TRIPLE:
                all_moves = mg.gen_type_7_serial_triple()
                moves = ms.common_filter_with_conditional_statement(all_moves, rival_move,
                                                                    wild_card_of_game=self.wild_card_of_game)

        elif rival_move_type == md.TYPE_8_BOMB_4:
            all_moves = mg.gen_type_8_bomb_4()
            moves = ms.common_filter(all_moves, rival_move,
                                     wild_card_of_game=self.wild_card_of_game) + mg.gen_type_9_bomb_5() + \
                    mg.gen_type_10_straight_flush() + mg.gen_type_11_bomb_6() + \
                    mg.gen_type_12_bomb_7() + mg.gen_type_13_bomb_8()

        elif rival_move_type == md.TYPE_9_BOMB_5:
            all_moves = mg.gen_type_9_bomb_5()
            moves = ms.common_filter(all_moves, rival_move,
                                     wild_card_of_game=self.wild_card_of_game) + mg.gen_type_10_straight_flush() + \
                    mg.gen_type_11_bomb_6() + mg.gen_type_12_bomb_7() + mg.gen_type_13_bomb_8()

        elif rival_move_type == md.TYPE_10_STRAIGHT_FLUSH:
            all_moves = mg.gen_type_10_straight_flush()
            moves = ms.common_filter(all_moves, rival_move,
                                     wild_card_of_game=self.wild_card_of_game) + mg.gen_type_11_bomb_6() + \
                    mg.gen_type_12_bomb_7() + mg.gen_type_13_bomb_8()

        elif rival_move_type == md.TYPE_11_BOMB_6:
            all_moves = mg.gen_type_11_bomb_6()
            moves = ms.common_filter(all_moves, rival_move,
                                     wild_card_of_game=self.wild_card_of_game) + mg.gen_type_12_bomb_7() + \
                    mg.gen_type_13_bomb_8()

        elif rival_move_type == md.TYPE_12_BOMB_7:
            all_moves = mg.gen_type_12_bomb_7()
            moves = ms.common_filter(all_moves, rival_move,
                                     wild_card_of_game=self.wild_card_of_game) + mg.gen_type_13_bomb_8()

        elif rival_move_type == md.TYPE_13_BOMB_8:
            all_moves = mg.gen_type_13_bomb_8()
            moves = ms.common_filter(all_moves, rival_move, wild_card_of_game=self.wild_card_of_game)

        elif rival_move_type == md.TYPE_14_JOKER_BOMB:
            moves = []

        if rival_move_type not in [md.TYPE_0_PASS, md.TYPE_8_BOMB_4, md.TYPE_9_BOMB_5,
                                   md.TYPE_10_STRAIGHT_FLUSH, md.TYPE_11_BOMB_6,
                                   md.TYPE_12_BOMB_7, md.TYPE_13_BOMB_8, md.TYPE_14_JOKER_BOMB]:
            moves = moves + mg.gen_type_8_bomb_4() + mg.gen_type_9_bomb_5() + mg.gen_type_10_straight_flush() + \
                    mg.gen_type_11_bomb_6() + mg.gen_type_12_bomb_7() + mg.gen_type_13_bomb_8()

        if len(rival_move) != 0:  # rival_move is not 'pass'
            moves = moves + [[]]

        for m in moves:
            m.sort()

        return moves

    def get_bomb_num(self):
        return self.bomb_num

    def step(self):
        if self.pending_free_type_check:
            current_round_actions = self.card_play_action_seq[self.pending_round_start:]
            if len(current_round_actions) >= len(self.players_remain):
                if all(action == [] for action in current_round_actions):
                    out_player = self.get_out_player_from_history()
                    if out_player:
                        teammate = get_team_mate(out_player)
                        if teammate in self.players_remain:
                            self.acting_player_position = teammate
                            self.free_type_right = True
                self.pending_free_type_check = False
                self.pending_round_start = 0

        action = self.players[self.acting_player_position].act(
            self.game_info_set)
        assert action in self.game_info_set.legal_actions

        action_info = md.get_move_info(action, wild_card_of_game=self.wild_card_of_game)
        action_type = action_info['type']

        if len(action) > 0:
            self.last_pid = self.acting_player_position

        if action_type in [md.TYPE_8_BOMB_4, md.TYPE_9_BOMB_5,
                           md.TYPE_10_STRAIGHT_FLUSH, md.TYPE_11_BOMB_6,
                           md.TYPE_12_BOMB_7, md.TYPE_13_BOMB_8, md.TYPE_14_JOKER_BOMB]:
            self.bomb_num += 1

        self.last_move_dict[
            self.acting_player_position] = action.copy()

        self.card_play_action_seq.append(action)
        self.card_play_type_seq.append(action_type)
        self.players_seq.append(self.acting_player_position)

        self.update_acting_player_hand_cards(action)

        self.played_cards[self.acting_player_position] += action

        self.game_done()
        if not self.game_over:
            if self.updated_position_outside:
                self.updated_position_outside = False
            else:
                self.pass_acting_player_position()
            self.game_info_set = self.get_info_set()

    def update_acting_player_hand_cards(self, action):
        if action != []:
            for card in action:
                self.info_sets[
                    self.acting_player_position].player_hand_cards.remove(card)
            self.info_sets[self.acting_player_position].player_hand_cards.sort()

    def get_info_set(self):
        self.info_sets[self.acting_player_position].wild_card_of_game = self.wild_card_of_game
        self.info_sets[self.acting_player_position].last_pid = self.last_pid

        self.info_sets[self.acting_player_position].players_remain = self.players_remain

        self.info_sets[
            self.acting_player_position].legal_actions = \
            self.get_legal_card_play_actions()

        self.info_sets[
            self.acting_player_position].last_move = self.get_last_valid_move()

        self.info_sets[
            self.acting_player_position].last_two_moves = self.get_last_two_moves()

        self.info_sets[
            self.acting_player_position].last_move_dict = self.last_move_dict

        self.info_sets[self.acting_player_position].num_cards_left_dict = \
            {pos: len(self.info_sets[pos].player_hand_cards)
             for pos in ['player_1', 'player_2', 'player_3', 'player_4']}

        self.info_sets[self.acting_player_position].other_hand_cards = []
        for pos in ['player_1', 'player_2', 'player_3', 'player_4']:
            if pos != self.acting_player_position:
                self.info_sets[
                    self.acting_player_position].other_hand_cards += \
                    self.info_sets[pos].player_hand_cards

        self.info_sets[self.acting_player_position].played_cards = \
            self.played_cards
        self.info_sets[self.acting_player_position].card_play_action_seq = \
            self.card_play_action_seq
        self.info_sets[self.acting_player_position].card_play_type_seq = \
            self.card_play_type_seq
        self.info_sets[self.acting_player_position].players_seq = self.players_seq

        self.info_sets[
            self.acting_player_position].all_hand_cards = \
            {pos: self.info_sets[pos].player_hand_cards
             for pos in ['player_1', 'player_2', 'player_3', 'player_4']}

        return deepcopy(self.info_sets[self.acting_player_position])

    def reset(self):
        self.card_play_action_seq = []
        self.card_play_type_seq = []
        self.players_seq = []
        self.players_remain = ['player_1', 'player_2', 'player_3', 'player_4']

        self.game_over = False

        self.acting_player_position = None

        self.info_sets = {'player_1': InfoSet('player_1'),
                          'player_2': InfoSet('player_2'),
                          'player_3': InfoSet('player_3'),
                          'player_4': InfoSet('player_4')}

        self.last_move = []
        self.last_two_moves = []

        self.played_cards = {'player_1': [],
                             'player_2': [],
                             'player_3': [],
                             'player_4': []}

        self.last_move_dict = {'player_1': [],
                               'player_2': [],
                               'player_3': [],
                               'player_4': []}

        self.winner = None
        self.players_rank = {'player_1': None,
                             'player_2': None,
                             'player_3': None,
                             'player_4': None}
        self.bomb_num = 0
        self.last_pid = 'player_1'
        self.free_type_right = False
        self.no_free_type_right = False
        self.pending_free_type_check = False
        self.pending_round_start = 0
        self.out_players = []


class InfoSet(object):
    def __init__(self, player_position):
        self.wild_card_of_game = None
        # The player position, i.e., player_1, player_2, player_3, player_4
        self.player_position = player_position
        self.players_remain = []
        # The hand cards of the current player. A list.
        self.player_hand_cards = None
        # The historical moves. It is a list of list
        self.card_play_action_seq = None
        self.card_play_type_seq = None
        self.players_seq = None
        # The union of the hand cards of the other 3 players for the current player
        self.other_hand_cards = None
        # The legal actions for the current move. It is a list of list
        self.legal_actions = None
        # The most recent valid move
        self.last_move = None
        # The most recent two moves
        self.last_two_moves = None
        # The last moves for all the positions
        self.last_move_dict = None
        # The played cards so far. It is a list.
        self.played_cards = None
        # Last player position that plays a valid move, i.e., not `pass`
        self.last_pid = None
        # number of cards remains on each player's hand
        self.num_cards_left_dict = None
        self.all_hand_cards = None
