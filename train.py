import os
import torch
from dmc.dmc import train
from dmc.arguments import parser

if __name__ == '__main__':
    flags = parser.parse_args()
    
    gpu_count = torch.cuda.device_count()
    print(f"\n{'='*50}")
    print(f"检测到 {gpu_count} 个可用的 GPU:")
    for i in range(gpu_count):
        gpu_name = torch.cuda.get_device_name(i)
        gpu_mem = torch.cuda.get_device_properties(i).total_memory / 1024**3
        print(f"GPU {i}: {gpu_name} ({gpu_mem:.1f} GB)")
    print(f"当前选择的 GPU 设备: {flags.gpu_devices}")
    print(f"{'='*50}\n")
    flags.gpu_devices = ','.join([str(i) for i in range(gpu_count)])
    flags.num_actor_devices = gpu_count 
    os.environ["CUDA_VISIBLE_DEVICES"] = flags.gpu_devices

    train(flags)
