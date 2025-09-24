import os
import typing
import logging
import traceback
import numpy as np
from collections import Counter
import time

import torch

from .env_utils import Environment
from environment.env import Env
from environment.env import cards2array

shandle = logging.StreamHandler()
shandle.setFormatter(
    logging.Formatter(
        '[%(levelname)s:%(process)d %(module)s:%(lineno)d %(asctime)s] '
        '%(message)s'))
log = logging.getLogger('guandzero')
log.propagate = False
log.addHandler(shandle)
log.setLevel(logging.INFO)


def create_env(flags, training_progress=0.0):
    reward_shaping_config = {
        'enable_reward_shaping': flags.enable_reward_shaping,
        'control_reward_weight': flags.control_reward_weight,
        'combo_reward_weight': flags.combo_reward_weight,
        'single_card_reward': flags.single_card_reward,
        'excess_single_penalty': flags.excess_single_penalty,
        'enable_progressive_reward': flags.enable_progressive_reward,
        'reward_decay_start': flags.reward_decay_start,
        'reward_decay_end': flags.reward_decay_end,
        'min_reward_scale': flags.min_reward_scale,
    }
    return Env(reward_shaping_config=reward_shaping_config, training_progress=training_progress)


Buffers = typing.Dict[str, typing.List[torch.Tensor]]


def create_buffers(flags, device_iterator):
    '''
    we create buffers for different devices,
    but each buffer storages all data from 4 players
    '''
    T = flags.unroll_length
    buffers = {}
    for device in device_iterator:
        buffers[device] = {}
        x_dim = 494
        specs = dict(
            done=dict(size=(T,), dtype=torch.bool),
            episode_return=dict(size=(T,), dtype=torch.float32),
            target=dict(size=(T,), dtype=torch.float32),
            obs_x_no_action=dict(size=(T, x_dim), dtype=torch.int8),
            obs_action=dict(size=(T, 54), dtype=torch.int8),
            obs_z=dict(size=(T, 5, 162), dtype=torch.int8),
        )
        _buffers: Buffers = {key: [] for key in specs}
        for _ in range(flags.num_buffers):
            for key in _buffers:
                if not device == "cpu":
                    _buffer = torch.empty(**specs[key]).to(torch.device('cuda:' + str(device))).share_memory_()
                else:
                    _buffer = torch.empty(**specs[key]).to(torch.device('cpu')).share_memory_()
                _buffers[key].append(_buffer)
        buffers[device] = _buffers
    return buffers


def create_optimizer(flags, learner_model):
    optimizer = torch.optim.Adam(
        learner_model.parameters(),
        lr=flags.learning_rate,
        eps=flags.epsilon
    )
    return optimizer


def get_batch(free_queue,
              full_queue,
              buffers,
              flags,
              lock):
    with lock:
        indices = [full_queue.get() for _ in range(flags.batch_size)]
    batch = {
        key: torch.stack([buffers[key][m] for m in indices], dim=1)
        for key in buffers
    }
    for m in indices:
        free_queue.put(m)
    return batch


def act(actor_id, device, free_queue, full_queue, model, buffers, flags):
    try:

        T = flags.unroll_length
        log.info(f'Actor process {actor_id} started on device {device}.')

        # Calculate training progress based on frames (if available)
        training_progress = 0.0  # Default for actor processes
        if hasattr(flags, 'total_frames') and flags.total_frames > 0:
            # This is a rough estimate - in practice, frames should be passed from main process
            training_progress = min(1.0, 0.0)  # Will be updated by main process
        
        env = create_env(flags, training_progress)
        env = Environment(env, device)

        done_buf = []
        episode_return_buf = []
        target_buf = []
        obs_x_no_action_buf = []
        obs_action_buf = []
        obs_z_buf = []
        player_position_buf = []
        size = 0

        position, obs, env_output = env.initial()

        while True:
            while True:
                current_player_position = env.env._acting_player_position
                player_position_buf.append(current_player_position)
                obs_x_no_action_buf.append(env_output['obs_x_no_action'])
                obs_z_buf.append(env_output['obs_z'])

                with torch.no_grad():
                    agent_output = model.forward(obs['z_batch'], obs['x_batch'])

                _action_idx = int(agent_output['action'].cpu().item())
                action = obs['legal_actions'][_action_idx]

                obs_action_buf.append(_cards2tensor(action))
                size += 1
                position, next_obs, env_output = env.step(action)
                obs = next_obs

                if env_output['done']:
                    # Use final scores from env_output (captured before reset), fallback to reading attributes
                    scores = env_output.get('final_scores', env.env._game_scores)
                    # Normalize to [0,1] range for stable training
                    new_targets = [float(scores[pos]) for pos in player_position_buf]

                    target_buf.extend(new_targets)
                    diff = len(new_targets)
                    if diff > 0:
                        done_buf.extend([False for _ in range(diff - 1)])
                        done_buf.append(True)

                        episode_return = env_output['episode_return']
                        episode_return_buf.extend([0.0 for _ in range(diff - 1)])
                        episode_return_buf.append(episode_return)
                        player_position_buf = []
                    break

            while size > T:
                index = free_queue.get()
                if index is None:
                    break

                for t in range(T):
                    buffers['done'][index][t, ...] = done_buf[t]
                    buffers['episode_return'][index][t, ...] = episode_return_buf[t]
                    buffers['target'][index][t, ...] = target_buf[t]
                    buffers['obs_x_no_action'][index][t, ...] = obs_x_no_action_buf[t]
                    buffers['obs_action'][index][t, ...] = obs_action_buf[t]
                    buffers['obs_z'][index][t, ...] = obs_z_buf[t]

                full_queue.put(index)

                done_buf = done_buf[T:]
                episode_return_buf = episode_return_buf[T:]
                target_buf = target_buf[T:]
                obs_x_no_action_buf = obs_x_no_action_buf[T:]
                obs_action_buf = obs_action_buf[T:]
                obs_z_buf = obs_z_buf[T:]
                size -= T

    except KeyboardInterrupt:
        pass
    except Exception as e:
        log.error('Exception in worker process %i', actor_id)
        traceback.print_exc()
        print()
        raise e


def _cards2tensor(list_cards):
    matrix = cards2array(list_cards)
    matrix = torch.from_numpy(matrix)
    return matrix
