import os
import glob
from dmc.dmc import train
from dmc.arguments import parser

if __name__ == '__main__':
    args = [
        "--actor_device_cpu",
        "--training_device", "cpu",
        "--gpu_devices", "",
        "--load_model",
        "--xpid", "guanzero",
        "--savedir", "guanzero_checkpoints",
        # Model settings - uncomment to use LSTM instead of Transformer
        # "--use_lstm",
        # Transformer settings (optional, defaults are already good)
        # "--d_model", "128",
        # "--nhead", "8", 
        # "--num_layers", "2",
        # "--max_seq_len", "100",
        # Reward shaping settings - single card priority strategy
        "--enable_reward_shaping",
        "--control_reward_weight", "0.1",
        "--combo_reward_weight", "0.03", 
        "--single_card_reward", "0.08",
        "--excess_single_penalty", "0.03",
        # Progressive reward decay settings
        "--enable_progressive_reward",
        "--reward_decay_start", "0.3",
        "--reward_decay_end", "0.8",
        "--min_reward_scale", "0.1"
    ]
    flags = parser.parse_args(args)

    # Check checkpoint file
    checkpoint_path = os.path.join(flags.savedir, flags.xpid, 'model.tar')
    print(f"Checkpoint path: {checkpoint_path}")
    print(f"Checkpoint exists: {os.path.exists(checkpoint_path)}")
    
    # Find latest weight file
    weights_dir = os.path.join(flags.savedir, flags.xpid)
    weight_files = glob.glob(os.path.join(weights_dir, "guandan_weights_*.ckpt"))
    if weight_files:
        latest_weight_file = max(weight_files, key=os.path.getmtime)
        print(f"Latest weight file: {latest_weight_file}")
        
        # Check weight file content
        try:
            import torch
            weight_checkpoint = torch.load(latest_weight_file, map_location='cpu', weights_only=False)
            if isinstance(weight_checkpoint, dict) and 'frames' in weight_checkpoint:
                print(f"Frames in weight file: {weight_checkpoint['frames']}")
            else:
                print("Weight file contains only model state, no training progress")
        except Exception as e:
            print(f"Failed to read weight file: {e}")
    else:
        print("No weight files found")
    
    if hasattr(flags, "gpu_devices") and flags.gpu_devices != "":
        os.environ["CUDA_VISIBLE_DEVICES"] = flags.gpu_devices
    else:
        os.environ["CUDA_VISIBLE_DEVICES"] = ""

    train(flags)
