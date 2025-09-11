import numpy as np

import torch
from torch import nn


class Model(nn.Module):
    def __init__(self, device=0):
        super().__init__()
        self.lstm = nn.LSTM(162, 128, batch_first=True)
        self.dense1 = nn.Linear(676, 1024)
        self.dense2 = nn.Linear(1024, 1024)
        self.dense3 = nn.Linear(1024, 1024)
        self.dense4 = nn.Linear(1024, 1024)
        self.dense5 = nn.Linear(1024, 1024)
        self.dense6 = nn.Linear(1024, 1024)
        self.dense7 = nn.Linear(1024, 1024)
        self.dense8 = nn.Linear(1024, 1)

        if device != 'cpu':
            device = f'cuda:{device}'
        self.to(torch.device(device))

    def forward(self, z, x, return_value=False, flags=None):
        lstm_out, (h_n, _) = self.lstm(z)
        lstm_out = lstm_out[:, -1, :]
        x = torch.cat([lstm_out, x], dim=-1)
        x = self.dense1(x)
        x = torch.relu(x)
        x = self.dense2(x)
        x = torch.relu(x)
        x = self.dense3(x)
        x = torch.relu(x)
        x = self.dense4(x)
        x = torch.relu(x)
        x = self.dense5(x)
        x = torch.relu(x)
        x = self.dense6(x)
        x = torch.relu(x)
        x = self.dense7(x)
        x = torch.relu(x)
        x = self.dense8(x)
        if return_value:
            return dict(values=x)
        else:
            if flags is not None and flags.exp_epsilon > 0 and np.random.rand() < flags.exp_epsilon:
                action = torch.randint(x.shape[0], (1,))[0]
            else:
                action = torch.argmax(x, dim=0)[0]
            return dict(action=action)
