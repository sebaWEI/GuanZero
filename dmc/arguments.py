import argparse

parser = argparse.ArgumentParser(description='GuanZero: PyTorch Guandan AI')

#general settings
parser.add_argument('--xpid',default = 'guanzero',
                    help='Experiment id (default:guanzero)')
parser.add_argument('--save_interval', default=10, type=int,
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
parser.add_argument('--exp_epsilon', default=0.01, type=float,
                    help='The probability for exploration')
parser.add_argument('--batch_size', default=32, type=int,
                    help='Learner batch size')
parser.add_argument('--unroll_length', default=100, type=int,
                    help='The unroll length (time dimension)')
parser.add_argument('--num_buffers', default=50, type=int,
                    help='Number of shared-memory buffers')
parser.add_argument('--max_grad_norm', default=40., type=float,
                    help='Max norm of gradients')

#optimizer settings
parser.add_argument('--learning_rate', default=0.0001, type=float,
                    help='Learning rate')
parser.add_argument('--epsilon', default=1e-8, type=float,
                    help='The epsilon parameter of the Adam optimizer')