from environment.game import GameEnv
import numpy as np
from collections import Counter

deck = []
for i in range(0, 54):
    deck.extend([i for _ in range(2)])


class Env:
    def __init__(self, wild_card_of_game=1, reward_shaping_config=None, training_progress=0.0):
        self.players = {}
        for position in ['player_1', 'player_2', 'player_3', 'player_4']:
            self.players[position] = DummyAgent(position)

        self._env = GameEnv(self.players, wild_card_of_game=wild_card_of_game)
        self.reward_shaping_config = reward_shaping_config or {}
        self.training_progress = training_progress  # 0.0 to 1.0
        self.info_set = None
    
    def update_training_progress(self, progress):
        """Update training progress for progressive reward scaling"""
        self.training_progress = max(0.0, min(1.0, progress))

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
        
        # Store previous state for reward calculation
        prev_state = {
            'last_move': self.info_set.last_move,
            'player_hand_cards': self.info_set.player_hand_cards.copy(),
            'cards_left': len(self.info_set.player_hand_cards),
            'game_phase': self._get_game_phase()
        }
        
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
            # Add strategic reward
            reward = self._get_strategic_reward(action, prev_state)
        
        return obs, reward, done, {}
    
    def _get_game_phase(self):
        """Determine game phase based on total cards left"""
        total_cards_left = sum(len(player_cards) for player_cards in 
                              [self.info_set.player_hand_cards] + 
                              [self.info_set.other_hand_cards])
        if total_cards_left > 80:
            return 0  # Early
        elif total_cards_left > 40:
            return 1  # Middle
        else:
            return 2  # Late
    
    def _get_reward_scale_factor(self):
        """Calculate reward scaling factor based on training progress"""
        if not self.reward_shaping_config.get('enable_progressive_reward', True):
            return 1.0
        
        decay_start = self.reward_shaping_config.get('reward_decay_start', 0.3)
        decay_end = self.reward_shaping_config.get('reward_decay_end', 0.8)
        min_scale = self.reward_shaping_config.get('min_reward_scale', 0.1)
        
        if self.training_progress < decay_start:
            return 1.0  # Full reward in early training
        elif self.training_progress > decay_end:
            return min_scale  # Minimal reward in late training
        else:
            # Linear decay between decay_start and decay_end
            progress_in_decay = (self.training_progress - decay_start) / (decay_end - decay_start)
            return 1.0 - progress_in_decay * (1.0 - min_scale)

    def _get_strategic_reward(self, action, prev_state):
        """Calculate strategic reward for the action"""
        if not self.reward_shaping_config.get('enable_reward_shaping', True):
            return 0.0
        
        # Calculate base strategic reward
        base_reward = 0.0
        
        # 1. Encourage taking control (self or teammate having control counts)
        if prev_state['last_move'] and len(prev_state['last_move']) > 0:
            if self._can_beat_action(action, prev_state['last_move']):
                base_reward += self.reward_shaping_config.get('control_reward_weight', 0.1)
        
        # 2. Strongly encourage playing single cards first (highest priority)
        if len(action) == 1:
            single_reward = self.reward_shaping_config.get('single_card_reward', 0.08)
            # Encourage playing single cards early in game
            if prev_state['game_phase'] == 0:  # Early
                base_reward += single_reward * 1.5  # Higher reward for early single cards
            elif prev_state['game_phase'] == 1:  # Middle
                base_reward += single_reward
            else:  # Late
                base_reward += single_reward * 0.5  # Lower reward for late single cards
        
        # 3. Encourage forming effective card combinations (after single cards)
        elif len(action) > 1:
            combo_weight = self.reward_shaping_config.get('combo_reward_weight', 0.03)
            if self._is_pair(action):
                base_reward += combo_weight
            elif self._is_triple(action):
                base_reward += combo_weight * 1.5
            elif self._is_straight(action):
                base_reward += combo_weight * 2.0
            elif self._is_bomb(action):
                base_reward += combo_weight * 3.0
        
        # 4. Penalize excessive single card retention (stricter penalty)
        single_cards = self._count_single_cards(prev_state['player_hand_cards'])
        if single_cards > 2:  # Start penalty when single cards exceed 2
            penalty = self.reward_shaping_config.get('excess_single_penalty', 0.03)
            # More single cards = heavier penalty
            penalty_multiplier = min(single_cards - 2, 5)  # Max 5x penalty
            base_reward -= penalty * penalty_multiplier
        
        # 5. Encourage maintaining control (self or teammate)
        if self._will_maintain_control(action, prev_state):
            base_reward += 0.05
        
        # 6. Penalize losing control
        if self._will_lose_control(action, prev_state):
            base_reward -= 0.02
        
        # Apply progressive reward scaling
        scale_factor = self._get_reward_scale_factor()
        return base_reward * scale_factor
    
    def _can_beat_action(self, action, last_action):
        """Check if current action can beat last action"""
        if len(action) != len(last_action):
            return len(action) > len(last_action)
        return max(action) > max(last_action)
    
    def _is_pair(self, cards):
        return len(cards) == 2 and cards[0] == cards[1]
    
    def _is_triple(self, cards):
        return len(cards) == 3 and len(set(cards)) == 1
    
    def _is_straight(self, cards):
        if len(cards) < 3:
            return False
        sorted_cards = sorted(cards)
        for i in range(1, len(sorted_cards)):
            if sorted_cards[i] - sorted_cards[i-1] != 1:
                return False
        return True
    
    def _has_high_cards(self, cards):
        return any(card >= 50 for card in cards)
    
    def _is_bomb(self, cards):
        """Check if cards form a bomb (4+ of same card)"""
        if len(cards) < 4:
            return False
        return len(set(cards)) == 1
    
    def _count_single_cards(self, hand_cards):
        """Count how many single cards (not in pairs/triples) are in hand"""
        card_count = {}
        for card in hand_cards:
            card_count[card] = card_count.get(card, 0) + 1
        
        single_count = 0
        for count in card_count.values():
            if count == 1:
                single_count += 1
        return single_count
    
    def _is_middle_card_action(self, action, game_phase):
        """Check if action uses middle-value cards at appropriate phase"""
        if not action:
            return False
        
        # Define middle card range (adjust based on actual game rules)
        middle_cards = [card for card in action if 20 <= card <= 40]
        
        # Encourage playing middle cards in mid-game
        if game_phase == 1 and middle_cards:
            return True
        
        return False
    
    def _will_maintain_control(self, action, prev_state):
        """Check if this action will help maintain control (self or teammate)"""
        # Simplified logic: beating opponent or playing single cards = maintaining control
        if len(action) == 1:
            return True
        
        # If can beat opponent's cards
        if prev_state['last_move'] and len(prev_state['last_move']) > 0:
            if self._can_beat_action(action, prev_state['last_move']):
                return True
        
        return False
    
    def _will_lose_control(self, action, prev_state):
        """Check if this action will likely lose control"""
        # If playing high cards but cannot beat opponent, may lose control
        if len(action) == 1 and self._has_high_cards(action):
            if prev_state['last_move'] and len(prev_state['last_move']) > 0:
                if not self._can_beat_action(action, prev_state['last_move']):
                    return True
        
        return False

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

        def score_from_rank(rank, team_mate_rank):
            if rank == 1 and team_mate_rank == 2:
                return 3
            elif rank == 2 and team_mate_rank == 1:
                return 2
            elif (rank == 2 and team_mate_rank == 3) or (rank == 3 and team_mate_rank == 2):
                return -2
            elif (rank == 3 and team_mate_rank == 4) or (rank == 4 and team_mate_rank == 3):
                return -3
            else:
                return 0

        return {
            'player_1': score_from_rank(ranks['player_1'], ranks['player_3']),
            'player_2': score_from_rank(ranks['player_2'], ranks['player_4']),
            'player_3': score_from_rank(ranks['player_3'], ranks['player_1']),
            'player_4': score_from_rank(ranks['player_4'], ranks['player_2']),
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
    if isinstance(list_cards, int):
        matrix = np.zeros(54, dtype=np.int8)
        matrix[list_cards] = 1
        return matrix

    elif len(list_cards) == 0:
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

    wild_card_of_game = cards2array(info_set.wild_card_of_game)
    wild_card_of_game_batch = np.repeat(wild_card_of_game[np.newaxis, :], num_legal_actions, axis=0)

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
                         wild_card_of_game_batch,
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
                             wild_card_of_game,
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
