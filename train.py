import os
import glob
import torch
from dmc.dmc import train
from dmc.arguments import parser

if __name__ == '__main__':
    args = [
        # GPU training settings
        "--training_device", "0",  # Use first GPU
        "--gpu_devices", "0",
        "--load_model",
        "--xpid", "guanzero_gpu",
        "--savedir", "guanzero_checkpoints",
        # Model settings 
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

    # Check GPU availability
    gpu_count = torch.cuda.device_count()
    if gpu_count == 0:
        print("❌ No GPU detected! Please use train_cpu.py for CPU training.")
        exit(1)
    
    print(f"\n{'='*50}")
    print(f"Detected {gpu_count} available GPUs:")
    for i in range(gpu_count):
        gpu_name = torch.cuda.get_device_name(i)
        gpu_mem = torch.cuda.get_device_properties(i).total_memory / 1024**3
        print(f"GPU {i}: {gpu_name} ({gpu_mem:.1f} GB)")
    print(f"Using GPU device: {flags.training_device}")
    print(f"{'='*50}\n")

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
            weight_checkpoint = torch.load(latest_weight_file, map_location='cpu', weights_only=False)
            if isinstance(weight_checkpoint, dict) and 'frames' in weight_checkpoint:
                print(f"Frames in weight file: {weight_checkpoint['frames']}")
            else:
                print("Weight file contains only model state, no training progress")
        except Exception as e:
            print(f"Failed to read weight file: {e}")
    else:
        print("No weight files found")
    
    # Set GPU environment
    os.environ["CUDA_VISIBLE_DEVICES"] = flags.gpu_devices

    print("🚀 Starting GPU training with progressive reward shaping...")
    train(flags)
