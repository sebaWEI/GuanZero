from environment.game import GameEnv
import numpy as np
from collections import Counter

deck = []
for i in range(0, 54):
    deck.extend([i for _ in range(2)])


class Env:
    def __init__(self):
        self.players = {}
        for position in ['player_1', 'player_2', 'player_3', 'player_4']:
            self.players[position] = DummyAgent(position)

        self._env = GameEnv(self.players)

        self.info_set = None

    def reset(self):
        self._env.reset()

        _deck = deck.copy()
        np.random.shuffle(_deck)
        player_hand_dict = {'player_1': _deck[:27],
                            'player_2': _deck[27:54],
                            'player_3': _deck[54:81],
                            'player_4': _deck[81:108]}
        for player in player_hand_dict:
            player_hand_dict[player].sort()

        self._env.card_play_init(player_hand_dict)
        self.info_set = self._game_info_set

        return get_obs(self.info_set)

    def step(self, action):
        assert action in self.info_set.legal_actions
        self.players[self._acting_player_position].set_action(action)
        self._env.step()
        self.info_set = self._game_info_set
        done = False
        reward = 0.0
        if self._game_over:
            done = True
            reward = self._get_reward()
            obs = None
        else:
            obs = get_obs(self.info_set)
        return obs, reward, done, {}

    def _get_reward(self):
        winner = self._game_winner
        if winner == 'player_1' or winner == 'player_3':
            return 1.0
        else:
            return -1.0

    @property
    def _game_info_set(self):
        return self._env.game_info_set

    @property
    def _game_bomb_num(self):
        return self._env.get_bomb_num()

    @property
    def _game_winner(self):
        return self._env.get_winner()

    @property
    def _winning_team(self):
        return self._env.get_winning_team()

    @property
    def _game_scores(self):
        ranks = self._env.players_rank

        def score_from_rank(rank):
            if rank == 1:
                return 3
            elif rank == 2:
                return 1
            elif rank == 3:
                return -1
            elif rank == 4:
                return -3
            else:
                return 0

        return {
            'player_1': score_from_rank(ranks['player_1']),
            'player_2': score_from_rank(ranks['player_2']),
            'player_3': score_from_rank(ranks['player_3']),
            'player_4': score_from_rank(ranks['player_4']),
        }

    @property
    def _acting_player_position(self):
        return self._env.acting_player_position

    @property
    def _game_over(self):
        return self._env.game_over


class DummyAgent(object):
    def __init__(self, position):
        self.position = position
        self.action = None

    def act(self, info_set):
        assert self.action in info_set.legal_actions
        return self.action

    def set_action(self, action):
        self.action = action


def get_obs(info_set):
    """
    `x_batch` is a batch of features (excluding the historical moves).
    It also encodes the action feature

    `z_batch` is a batch of features with historical moves only.

    `legal_actions` is the legal moves

    `x_no_action`: the features (excluding the historical moves and
    the action features). It does not have the batch dim.

    `z`: same as z_batch but not a batch.
    """
    return get_obs_from_player(info_set)


def cards2array(list_cards):
    if len(list_cards) == 0:
        return np.zeros(54, dtype=np.int8)

    matrix = np.zeros(54, dtype=np.int8)
    counter = Counter(list_cards)
    for card, num_times in counter.items():
        matrix[card] = num_times
    return matrix


def get_one_hot_array(num_left_cards):
    one_hot = np.zeros(27)
    one_hot[num_left_cards - 1] = 1
    return one_hot


def process_action_seq(sequence, length=15):
    sequence = sequence[-length:].copy()
    if len(sequence) < length:
        empty_sequence = [[] for _ in range(length - len(sequence))]
        empty_sequence.extend(sequence)
        sequence = empty_sequence
    return sequence


def action_seq_list2array(action_seq_list):
    action_seq_array = np.zeros((len(action_seq_list), 54))
    for row, list_cards in enumerate(action_seq_list):
        action_seq_array[row, :] = cards2array(list_cards)
    action_seq_array = action_seq_array.reshape(5, 162)
    return action_seq_array


def players_remain_to_array(players_remain):
    players_remain_array = [0, 0, 0, 0]
    if 'player_1' in players_remain:
        players_remain_array[0] = 1
    if 'player_2' in players_remain:
        players_remain_array[1] = 1
    if 'player_3' in players_remain:
        players_remain_array[2] = 1
    if 'player_4' in players_remain:
        players_remain_array[3] = 1
    return players_remain_array


def get_obs_from_player(info_set):
    num_legal_actions = len(info_set.legal_actions)
    player = info_set.player_position
    if player == 'player_1':
        position_matrix = [1, 0, 0, 0]
        teammate = 'player_3'
    elif player == 'player_2':
        position_matrix = [0, 1, 0, 0]
        teammate = 'player_4'
    elif player == 'player_3':
        position_matrix = [0, 0, 1, 0]
        teammate = 'player_1'
    else:
        position_matrix = [0, 0, 0, 1]
        teammate = 'player_2'

    position_matrix_batch = np.repeat(np.array(position_matrix)[np.newaxis, :], num_legal_actions, axis=0)

    players_remain = players_remain_to_array(info_set.players_remain)
    players_remain_batch = np.repeat(np.array(players_remain)[np.newaxis, :], num_legal_actions, axis=0)

    my_hand_cards = cards2array(info_set.player_hand_cards)
    my_hand_cards_batch = np.repeat(my_hand_cards[np.newaxis, :], num_legal_actions, axis=0)

    other_hand_cards = cards2array(info_set.other_hand_cards)
    other_hand_cards_batch = np.repeat(other_hand_cards[np.newaxis, :], num_legal_actions, axis=0)

    last_action = cards2array(info_set.last_move)
    last_action_batch = np.repeat(last_action[np.newaxis, :], num_legal_actions, axis=0)

    my_action_batch = np.zeros(my_hand_cards_batch.shape)
    for j, action in enumerate(info_set.legal_actions):
        my_action_batch[j, :] = cards2array(action)

    my_last_action = cards2array(
        info_set.last_move_dict[player])
    my_last_action_batch = np.repeat(
        my_last_action[np.newaxis, :],
        num_legal_actions, axis=0)
    my_num_cards_left = get_one_hot_array(info_set.num_cards_left_dict[player])
    my_num_cards_left_batch = np.repeat(my_num_cards_left[np.newaxis, :], num_legal_actions, axis=0)

    my_played_cards = cards2array(
        info_set.played_cards[player])
    my_played_cards_batch = np.repeat(my_played_cards[np.newaxis, :], num_legal_actions, axis=0)

    last_teammate_action = cards2array(info_set.last_move_dict[teammate])
    last_teammate_action_batch = np.repeat(last_teammate_action[np.newaxis, :], num_legal_actions, axis=0)
    teammate_num_cards_left = get_one_hot_array(info_set.num_cards_left_dict[teammate])
    teammate_num_cards_left_batch = np.repeat(teammate_num_cards_left[np.newaxis, :], num_legal_actions, axis=0)

    teammate_played_cards = cards2array(info_set.played_cards[teammate])
    teammate_played_cards_batch = np.repeat(teammate_played_cards[np.newaxis, :], num_legal_actions, axis=0)

    x_batch = np.hstack((position_matrix_batch,
                         players_remain_batch,
                         my_hand_cards_batch,
                         other_hand_cards_batch,
                         my_played_cards_batch,
                         teammate_played_cards_batch,
                         last_action_batch,
                         my_last_action_batch,
                         last_teammate_action_batch,
                         my_num_cards_left_batch,
                         teammate_num_cards_left_batch,
                         my_action_batch))
    x_no_action = np.hstack((position_matrix,
                             players_remain,
                             my_hand_cards,
                             other_hand_cards,
                             my_played_cards,
                             teammate_played_cards,
                             last_action,
                             my_last_action,
                             last_teammate_action,
                             my_num_cards_left,
                             teammate_num_cards_left))
    z = action_seq_list2array(process_action_seq(
        info_set.card_play_action_seq))
    z_batch = np.repeat(
        z[np.newaxis, :, :],
        num_legal_actions, axis=0)
    obs = {
        'position': player,
        'x_batch': x_batch.astype(np.float32),
        'z_batch': z_batch.astype(np.float32),
        'legal_actions': info_set.legal_actions,
        'x_no_action': x_no_action.astype(np.int8),
        'z': z.astype(np.int8),
    }
    return obs
