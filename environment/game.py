from copy import deepcopy
from move_generator import MovesGenerator
import move_detector as md, move_selector as ms


class GameEnv(object):
    def __init__(self, players):
        self.card_play_action_seq = []
        self.card_play_type_seq = []

        self.game_over = False

        self.acting_player_position = None

        self.players = players

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

        self.game_info_set = None
        self.winner = None
        self.bomb_num = 0
        self.last_pid = 'player_1'

    def card_play_init(self, player_hand_dict):
        self.info_sets['player_1'].player_hand_cards = player_hand_dict['player_1']
        self.info_sets['player_2'].player_hand_cards = player_hand_dict['player_2']
        self.info_sets['player_3'].player_hand_cards = player_hand_dict['player_3']
        self.info_sets['player_4'].player_hand_cards = player_hand_dict['player_4']
        self.get_acting_player_position()
        self.game_info_set = self.get_info_set()

    def game_done(self):
        if len(self.info_sets['player_1'].player_hand_cards) == 0:
            self.winner = 'player_1'
            self.game_over = True
        if len(self.info_sets['player_2'].player_hand_cards) == 0:
            self.winner = 'player_2'
            self.game_over = True
        if len(self.info_sets['player_3'].player_hand_cards) == 0:
            self.winner = 'player_3'
            self.game_over = True
        if len(self.info_sets['player_4'].player_hand_cards) == 0:
            self.winner = 'player_4'
            self.game_over = True

    def get_winner(self):
        return self.winner
    
    def get_winning_team(self):
        if  self.game_over:
            if self.winner in ['player_1','player_3']:
                return 'team_1_3'
            elif self.winner in ['player_2','player_4']:
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

    def get_acting_player_position(self):
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

        return self.acting_player_position

    def get_legal_card_play_actions(self):
        mg = MovesGenerator(
            self.info_sets[self.acting_player_position].player_hand_cards)

        action_sequence = self.card_play_action_seq
        type_sequence = self.card_play_type_seq

        rival_move = []
        rival_type = None
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

        rival_info = md.get_move_info(rival_move)
        rival_move_type = rival_info['type']
        moves = list()

        if rival_move_type == md.TYPE_0_PASS:
            moves = mg.gen_moves()

        elif rival_move_type == md.TYPE_1_SINGLE:
            all_moves = mg.gen_type_1_single()
            moves = ms.common_filter(all_moves, rival_move)

        elif rival_move_type == md.TYPE_2_PAIR:
            all_moves = mg.gen_type_2_pair()
            moves = ms.common_filter(all_moves, rival_move)

        elif rival_move_type == md.TYPE_3_TRIPLE:
            all_moves = mg.gen_type_3_triple()
            moves = ms.common_filter(all_moves, rival_move)

        elif rival_move_type == md.TYPE_4_3_2:
            all_moves = mg.gen_type_4_3_2()
            moves = ms.common_filter(all_moves, rival_move)

        elif rival_move_type == md.TYPE_5_STRAIGHT:
            all_moves = mg.gen_type_5_straight()
            moves = ms.common_filter(all_moves, rival_move)

        elif rival_move_type == md.TYPE_6_SERIAL_PAIR:
            all_moves = mg.gen_type_6_serial_pair()
            moves = ms.common_filter_with_conditional_statement(all_moves, rival_move)

        elif rival_move_type == md.TYPE_7_SERIAL_TRIPLE:
            all_moves = mg.gen_type_7_serial_triple()
            moves = ms.common_filter_with_conditional_statement(all_moves, rival_move)

        elif rival_move_type == [md.TYPE_6_SERIAL_PAIR, md.TYPE_7_SERIAL_TRIPLE]:
            if rival_type == md.TYPE_6_SERIAL_PAIR:
                all_moves = mg.gen_type_6_serial_pair()
                moves = ms.common_filter_with_conditional_statement(all_moves, rival_move)
            if rival_type == md.TYPE_7_SERIAL_TRIPLE:
                all_moves = mg.gen_type_7_serial_triple()
                moves = ms.common_filter_with_conditional_statement(all_moves, rival_move)

        elif rival_move_type == md.TYPE_8_BOMB_4:
            all_moves = mg.gen_type_8_bomb_4()
            moves = ms.common_filter(all_moves, rival_move) + mg.gen_type_9_bomb_5() + \
                    mg.gen_type_10_straight_flush() + mg.gen_type_11_bomb_6() + \
                    mg.gen_type_12_bomb_7() + mg.gen_type_13_bomb_8()

        elif rival_move_type == md.TYPE_9_BOMB_5:
            all_moves = mg.gen_type_9_bomb_5()
            moves = ms.common_filter(all_moves, rival_move) + mg.gen_type_10_straight_flush() + \
                    mg.gen_type_11_bomb_6() + mg.gen_type_12_bomb_7() + mg.gen_type_13_bomb_8()

        elif rival_move_type == md.TYPE_10_STRAIGHT_FLUSH:
            all_moves = mg.gen_type_10_straight_flush()
            moves = ms.common_filter(all_moves, rival_move) + mg.gen_type_11_bomb_6() + \
                    mg.gen_type_12_bomb_7() + mg.gen_type_13_bomb_8()

        elif rival_move_type == md.TYPE_11_BOMB_6:
            all_moves = mg.gen_type_11_bomb_6()
            moves = ms.common_filter(all_moves, rival_move) + mg.gen_type_12_bomb_7() + \
                    mg.gen_type_13_bomb_8()

        elif rival_move_type == md.TYPE_12_BOMB_7:
            all_moves = mg.gen_type_12_bomb_7()
            moves = ms.common_filter(all_moves, rival_move) + mg.gen_type_13_bomb_8()

        elif rival_move_type == md.TYPE_13_BOMB_8:
            all_moves = mg.gen_type_13_bomb_8()
            moves = ms.common_filter(all_moves, rival_move)

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
        action = self.players[self.acting_player_position].act(
            self.game_info_set)
        assert action in self.game_info_set.legal_actions

        action_info = md.get_move_info(action)
        action_type = action_info['type']

        if len(action) > 0:
            self.last_pid = self.acting_player_position

        if action_type in [md.TYPE_0_PASS, md.TYPE_8_BOMB_4, md.TYPE_9_BOMB_5,
                           md.TYPE_10_STRAIGHT_FLUSH, md.TYPE_11_BOMB_6,
                           md.TYPE_12_BOMB_7, md.TYPE_13_BOMB_8, md.TYPE_14_JOKER_BOMB]:
            self.bomb_num += 1

        self.last_move_dict[
            self.acting_player_position] = action.copy()

        self.card_play_action_seq.append(action)
        self.card_play_type_seq.append(action_type)

        self.update_acting_player_hand_cards(action)

        self.played_cards[self.acting_player_position] += action

        self.game_done()
        if not self.game_over:
            self.get_acting_player_position()
            self.game_info_set = self.get_info_set()

    def update_acting_player_hand_cards(self, action):
        if action != []:
            for card in action:
                self.info_sets[
                    self.acting_player_position].player_hand_cards.remove(card)
            self.info_sets[self.acting_player_position].player_hand_cards.sort()

    def get_info_set(self):
        self.info_sets[self.acting_player_position].last_pid = self.last_pid

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

        self.info_sets[
            self.acting_player_position].all_hand_cards = \
            {pos: self.info_sets[pos].player_hand_cards
             for pos in ['player_1', 'player_2', 'player_3', 'player_4']}

        return deepcopy(self.info_sets[self.acting_player_position])

    def reset(self):
        self.card_play_action_seq = []
        self.card_play_type_seq = []

        self.game_over = False

        self.acting_player_position = None

        self.last_move_dict = {'player_1': [],
                               'player_2': [],
                               'player_3': [],
                               'player_4': []}

        self.played_cards = {'player_1': [],
                             'player_2': [],
                             'player_3': [],
                             'player_4': []}

        self.last_move = []
        self.last_two_moves = []

        self.info_sets = {'player_1': InfoSet('player_1'),
                          'player_2': InfoSet('player_2'),
                          'player_3': InfoSet('player_3'),
                          'player_4': InfoSet('player_4')}

        self.bomb_num = 0
        self.last_pid = 'player_1'


class InfoSet(object):
    def __init__(self, player_position):
        # The player position, i.e., player_1, player_2, player_3, player_4
        self.player_position = player_position
        # The hand cards of the current player. A list.
        self.player_hand_cards = None
        # The historical moves. It is a list of list
        self.card_play_action_seq = None
        self.card_play_type_seq = None
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
