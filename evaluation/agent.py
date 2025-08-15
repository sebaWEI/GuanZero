import torch
import numpy as np

from environment.env import get_obs


def _load_model(model_path):
    from dmc.model import Model
    device = 0 if torch.cuda.is_available() else 'cpu'
    model = Model(device=device)
    state = torch.load(model_path, map_location='cuda:0' if torch.cuda.is_available() else 'cpu')
    model.load_state_dict(state, strict=False)
    model.eval()
    return model


class GuanZeroAgent:

    def __init__(self, model_path):
        self.model = _load_model(model_path)

    def act(self, info_set):
        if len(info_set.legal_actions) == 1:
            return info_set.legal_actions[0]

        obs = get_obs(info_set)

        z_batch = torch.from_numpy(obs['z_batch']).float()
        x_batch = torch.from_numpy(obs['x_batch']).float()
        if torch.cuda.is_available():
            z_batch, x_batch = z_batch.cuda(), x_batch.cuda()
        y_pred = self.model.forward(z_batch, x_batch, return_value=True)['values']
        y_pred = y_pred.detach().cpu().numpy()

        best_action_index = np.argmax(y_pred, axis=0)[0]
        best_action = info_set.legal_actions[best_action_index]

        return best_action
