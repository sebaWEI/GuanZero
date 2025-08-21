from .simulation import evaluate

if __name__ == '__main__':
	# Windows 多进程必须放在 main 保护下
	# 可自行修改为你需要的权重/数据/进程数
	model_path = 'guanzero_checkpoints/second_train/guandan_weights_649600.ckpt'
	eval_data = 'evaluation/eval.pkl'
	player_config = {
        'player_1': 'ai',
        'player_2': 'random',
        'player_3': 'random',
        'player_4': 'random'
    }
	num_workers = 4
	evaluate(model_path, eval_data, num_workers,player_config)