import os
import typing
import logging
import traceback
import numpy as np
from collections import Counter
import time

import torch
from torch import multiprocessing as mp

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


def create_env(flags):
    return Env()


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
        x_dim =  436
        specs = dict(
            done=dict(size=(T,), dtype=torch.bool),
            episode_return=dict(size=(T,), dtype=torch.float32),
            target=dict(size=(T,), dtype=torch.float32),
            obs_x_no_action=dict(size=(T, x_dim), dtype=torch.int8),
            obs_action=dict(size=(T, 54), dtype=torch.int8),
            obs_z=dict(size=(T,5,162), dtype=torch.int8),
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
        log.info(f'演员进程 {actor_id} 已在设备 {device} 上启动。')

        env = create_env(flags)
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
                    # 使用 env_output 中的最终分数（在 reset 前抓取），后备读取属性
                    scores = env_output.get('final_scores', env.env._game_scores)
                    # 归一化到 [0,1] 区间，稳定训练
                    new_targets = [float(scores[pos]) / 3.0 for pos in player_position_buf]


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
