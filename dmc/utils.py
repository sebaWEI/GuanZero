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
#from douzero.env.env import _cards2array

def create_env(flags):
    return Env()

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
                    agent_output = model.forward(env_output['z_batch'], env_output['x_batch'])
                
                _action_idx = int(agent_output['action'].cpu().item())
                action = obs['legal_actions'][_action_idx]
                
                #    需要一个辅助函数将原始动作格式化为Tensor
                obs_action_buf.append(_cards2tensor(action))
                size += 1
                position, next_obs, env_output = env.step(action)
                obs = next_obs

                if env_output['done']:
                    winning_team = env.env._winning_team
                    new_targets = []
                    for player_position in player_position_buf:
                        player_team = 'team_1_3' if player_position in [0, 2] else 'team_2_4'
                        if player_team == winning_team:
                            new_targets.append(1.0)
                        else:
                            new_targets.append(-1.0)
    
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
        log.error('Exception in worker process %i', i)
        traceback.print_exc()
        print()
        raise e
