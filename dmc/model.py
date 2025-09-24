import numpy as np

import torch
from torch import nn


class Model(nn.Module):
    def __init__(self, device=0, use_transformer=True, d_model=128, nhead=8, num_layers=2, max_seq_len=100):
        super().__init__()
        self.use_transformer = use_transformer
        
        if use_transformer:
            # Transformer-based sequence processing
            self.d_model = d_model
            self.input_projection = nn.Linear(162, d_model)
            self.pos_encoding = nn.Parameter(torch.zeros(max_seq_len, d_model))
            
            # Transformer encoder
            encoder_layer = nn.TransformerEncoderLayer(
                d_model=d_model,
                nhead=nhead,
                dim_feedforward=d_model * 4,
                dropout=0.1,
                batch_first=True
            )
            self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
            
            # Output projection
            self.output_projection = nn.Linear(d_model, 128)
        else:
            # Original LSTM
            self.lstm = nn.LSTM(162, 128, batch_first=True)
        
        # Dense layers (same as original)
        self.dense1 = nn.Linear(676, 800)  # 128 + 548 = 676
        self.dense2 = nn.Linear(800, 800)
        self.dense3 = nn.Linear(800, 800)
        self.dense4 = nn.Linear(800, 800)
        self.dense5 = nn.Linear(800, 800)
        self.dense6 = nn.Linear(800, 1)
       

        if device != 'cpu':
            device = f'cuda:{device}'
        self.to(torch.device(device))

    def forward(self, z, x, return_value=False, flags=None):
        if self.use_transformer:
            # Transformer processing
            batch_size, seq_len, _ = z.shape
            
            # Project input to d_model
            z_proj = self.input_projection(z)  # [batch, seq_len, d_model]
            
            # Add positional encoding
            if seq_len <= self.pos_encoding.size(0):
                z_proj = z_proj + self.pos_encoding[:seq_len].unsqueeze(0)
            else:
                # Handle sequences longer than max_seq_len
                z_proj = z_proj + self.pos_encoding[-1:].unsqueeze(0).expand(batch_size, seq_len, -1)
            
            # Apply transformer
            transformer_out = self.transformer(z_proj)  # [batch, seq_len, d_model]
            
            # Use the last timestep output (similar to LSTM)
            seq_out = self.output_projection(transformer_out[:, -1, :])  # [batch, 128]
        else:
            # Original LSTM processing
            lstm_out, (h_n, _) = self.lstm(z)
            seq_out = lstm_out[:, -1, :]  # [batch, 128]
        
        # Concatenate with x and pass through dense layers
        x = torch.cat([seq_out, x], dim=-1)  # [batch, 128 + 548 = 676]
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
                action = torch.argmax(x, dim=0)[0]
            return dict(action=action)
