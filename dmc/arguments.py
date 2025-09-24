import argparse

parser = argparse.ArgumentParser(description='GuanZero: PyTorch Guandan AI')

#general settings
parser.add_argument('--xpid',default = 'guanzero',
                    help='Experiment id (default:guanzero)')
parser.add_argument('--save_interval', default=5, type=int,
                    help='Time interval (in minutes) at which to save the model')

#device settings
parser.add_argument('--actor_device_cpu', action='store_true',
                    help='Use CPU as actor device')
parser.add_argument('--gpu_devices', default='0', type=str,
                    help='Which GPUs to be used for training')
parser.add_argument('--num_actor_devices', default=1, type=int,
                    help='The number of devices used for simulation')
parser.add_argument('--num_actors', default=5, type=int,
                    help='The number of actors for each simulation device')
parser.add_argument('--training_device', default='0', type=str,
                    help='The index of the GPU used for training models. `cpu` means using cpu')
parser.add_argument('--load_model', action='store_true',
                    help='Load an existing model')
parser.add_argument('--disable_checkpoint', action='store_true',
                    help='Disable saving checkpoint')
parser.add_argument('--savedir',default='guanzero_checkpoints',
                    help='The root directory for saving all experimental data(default:)')

#hyperparameters
parser.add_argument('--total_frames', default=1000000000000, type=int,
                    help='Total environment frames to train for')
parser.add_argument('--exp_epsilon', default=0.1, type=float,
                    help='The probability for exploration (default: 0.1)')
parser.add_argument('--batch_size', default=32, type=int,
                    help='Learner batch size')
parser.add_argument('--unroll_length', default=100, type=int,
                    help='The unroll length (time dimension)')
parser.add_argument('--num_buffers', default=50, type=int,
                    help='Number of shared-memory buffers')
parser.add_argument('--max_grad_norm', default=40., type=float,
                    help='Max norm of gradients')
parser.add_argument('--num_threads', default=4, type=int,
                    help='Number of threads for data loading')

#optimizer settings
parser.add_argument('--learning_rate', default=0.0001, type=float,
                    help='Learning rate')
parser.add_argument('--epsilon', default=1e-8, type=float,
                    help='The epsilon parameter of the Adam optimizer')

#model settings
parser.add_argument('--use_transformer', action='store_true', default=True,
                    help='Use Transformer instead of LSTM (default: True)')
parser.add_argument('--use_lstm', action='store_true',
                    help='Use LSTM instead of Transformer')
parser.add_argument('--d_model', default=128, type=int,
                    help='Transformer model dimension (default: 128)')
parser.add_argument('--nhead', default=8, type=int,
                    help='Number of attention heads (default: 8)')
parser.add_argument('--num_layers', default=2, type=int,
                    help='Number of Transformer layers (default: 2)')
parser.add_argument('--max_seq_len', default=100, type=int,
                    help='Maximum sequence length for Transformer (default: 100)')

#reward shaping settings
parser.add_argument('--enable_reward_shaping', action='store_true', default=True,
                    help='Enable strategic reward shaping (default: True)')
parser.add_argument('--control_reward_weight', default=0.1, type=float,
                    help='Weight for taking control (beating opponent) reward (default: 0.1)')
parser.add_argument('--combo_reward_weight', default=0.03, type=float,
                    help='Weight for forming effective card combinations (default: 0.03)')
parser.add_argument('--single_card_reward', default=0.08, type=float,
                    help='Reward for playing single cards early (priority strategy) (default: 0.08)')
parser.add_argument('--excess_single_penalty', default=0.03, type=float,
                    help='Penalty for keeping too many single cards (default: 0.03)')

#progressive reward shaping settings
parser.add_argument('--enable_progressive_reward', action='store_true', default=True,
                    help='Enable progressive reward decay (default: True)')
parser.add_argument('--reward_decay_start', default=0.3, type=float,
                    help='Training progress to start reward decay (0.0-1.0, default: 0.3)')
parser.add_argument('--reward_decay_end', default=0.8, type=float,
                    help='Training progress to end reward decay (0.0-1.0, default: 0.8)')
parser.add_argument('--min_reward_scale', default=0.1, type=float,
                    help='Minimum reward scaling factor (default: 0.1)')