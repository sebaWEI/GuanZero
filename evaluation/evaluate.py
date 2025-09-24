from .simulation import evaluate

if __name__ == '__main__':
	# Windows multiprocessing must be under main protection
	# You can modify the weights/data/process count as needed
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