import numpy as np
import torch 

def _format_observation(obs, device):
    """
    A utility function to process observations and
    move them to CUDA.
    """
    position = obs['position']
    if not device == "cpu":
        device = 'cuda:' + str(device)
    device = torch.device(device)
    x_batch = torch.from_numpy(obs['x_batch']).to(device)
    z_batch = torch.from_numpy(obs['z_batch']).to(device)
    x_no_action = torch.from_numpy(obs['x_no_action'])
    z = torch.from_numpy(obs['z'])
    obs = {'x_batch': x_batch,
           'z_batch': z_batch,
           'legal_actions': obs['legal_actions'],
           }
    return position, obs, x_no_action, z

class Environment:
    def __init__(self, env, device):
        """ Initialzie this environment wrapper
        """
        self.env = env
        self.device = device
        self.episode_return = None

    def initial(self):
        initial_position, initial_obs, x_no_action, z = _format_observation(self.env.reset(), self.device)
        initial_reward = torch.zeros(1, 1)
        self.episode_return = torch.zeros(1, 1)
        initial_done = torch.ones(1, 1, dtype=torch.bool)

        return initial_position, initial_obs, dict(
            done=initial_done,
            episode_return=self.episode_return,
            obs_x_no_action=x_no_action,
            obs_z=z,
            )
        
    def step(self, action):
        obs, reward, done, _ = self.env.step(action)

        self.episode_return += reward
        episode_return = self.episode_return 

        final_scores = None
        if done:
            # Capture game scores before reset
            if hasattr(self.env, '_game_scores'):
                final_scores = self.env._game_scores
            obs = self.env.reset()
            self.episode_return = torch.zeros(1, 1)

        position, obs, x_no_action, z = _format_observation(obs, self.device)
        reward = torch.tensor(reward).view(1, 1)
        done = torch.tensor(done).view(1, 1)
        out = dict(
            done=done,
            episode_return=episode_return,
            obs_x_no_action=x_no_action,
            obs_z=z,
        )
        if final_scores is not None:
            out['final_scores'] = final_scores
        return position, obs, out

    def close(self):
        self.env.close()
