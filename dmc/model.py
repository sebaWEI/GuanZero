import numpy as np

import torch
from torch import nn

class PlayerLstmModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.lstm = nn.LSTM(162, 128, batch_first=True)
        self.dense1 = nn.Linear(373 + 128, 512)#373 need to change
        self.dense2 = nn.Linear(512, 512)
        self.dense3 = nn.Linear(512, 512)
        self.dense4 = nn.Linear(512, 512)
        self.dense5 = nn.Linear(512, 512)
        self.dense6 = nn.Linear(512, 1)

        def forward(self, z, x, return_value=False, flags=None):
            lstm_out, (h_n, _) = self.lstm(z)
            lstm_out = lstm_out[:,-1,:]
            x = torch.cat([lstm_out,x], dim=-1)
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
            if return_value:
                return dict(values=x)
            else:
                if flags is not None and flags.exp_epsilon > 0 and np.random.rand() < flags.exp_epsilon:
                    action = torch.randint(x.shape[0], (1,))[0]
                else:
                    action = torch.argmax(x,dim=0)[0]
                return dict(action=action)
            
class Model:
    '''
    Guan Dan is a symmetric 2v2 game. Fundamentally, there is no special role for any player over another.
    The objectives of player_1 and player_3 are completely aligned, as are those of player_2 and player_4. 
    The distinctions between players (such as who is my teammate and who is the previous player) can be 
    input as state features to the model without requiring a new model to represent them.
    '''
    def __init__(self, device=0):
        if not device == "cpu":
            device = 'cuda:' + str(device)
        self.model=PlayerLstmModel().to(torch.device(device))

    def forward(self,z,x,training=False,flags=None):
        return self.model.forward(z, x, training, flags)
    
    def share_memory(self):
        self.model.share_memory()

    def eval(self):
        self.model.eval()

    def parameters(self):
        return self.models.parameters()
    
    def get_model(self):
        return self.model