import multiprocessing as mp
import pickle

from environment.game import GameEnv


def load_card_play_models(model_path):
    players = {}

    for position in ['player_1', 'player_2', 'player_3']:
        from .random_agent import RandomAgent
        players[position] = RandomAgent
    from .agent import GuanZeroAgent
    players['player_4'] = GuanZeroAgent(model_path)
    return players


def mp_simulate(card_play_data_list, model_path, q):
    players = load_card_play_models(model_path)

    env = GameEnv(players)
    for idx, card_play_data in enumerate(card_play_data_list):
        env.card_play_init(card_play_data)
        while not env.game_over:
            env.step()
        env.reset()

    q.put((env.num_wins['player_1'],
           env.num_wins['player_2'],
           env.num_wins['player_3'],
           env.num_wins['player_4'],
           env.scores['player_1'],
           env.scores['player_2'],
           env.scores['player_3'],
           env.scores['player_4']
           ))


def data_allocation_per_worker(card_play_data_list, num_workers):
    """Distribute data evenly across workers"""
    if num_workers <= 0:
        return [card_play_data_list]

    card_play_data_list_each_worker = [[] for _ in range(num_workers)]
    for idx, data in enumerate(card_play_data_list):
        card_play_data_list_each_worker[idx % num_workers].append(data)

    # Print distribution info
    for i, worker_data in enumerate(card_play_data_list_each_worker):
        print(f"Worker {i}: {len(worker_data)} games")

    return card_play_data_list_each_worker


def evaluate(model_path, eval_data, num_workers):
    # Input validation
    if num_workers <= 0:
        raise ValueError("num_workers must be positive")

    try:
        with open(eval_data, 'rb') as f:
            card_play_data_list = pickle.load(f)
    except FileNotFoundError:
        print(f"Error: Evaluation data file '{eval_data}' not found")
        return
    except Exception as e:
        print(f"Error loading evaluation data: {e}")
        return

    if not card_play_data_list:
        print("Error: No evaluation data found")
        return

    print(f"Loaded {len(card_play_data_list)} games for evaluation")

    card_play_data_list_each_worker = data_allocation_per_worker(
        card_play_data_list, num_workers)
    del card_play_data_list

    num_player_1_wins = 0
    num_player_2_wins = 0
    num_player_3_wins = 0
    num_player_4_wins = 0

    player_1_scores = 0
    player_2_scores = 0
    player_3_scores = 0
    player_4_scores = 0

    ctx = mp.get_context('spawn')
    q = ctx.Queue()
    processes = []
    for card_play_data in card_play_data_list_each_worker:
        p = ctx.Process(
            target=mp_simulate,
            args=(card_play_data, model_path, q))
        p.start()
        processes.append(p)

    # Wait for all processes to complete
    for p in processes:
        p.join()

    # Collect results with timeout
    results_collected = 0
    for i in range(num_workers):
        try:
            result = q.get(timeout=30)  # 30 second timeout
            num_player_1_wins += result[0]
            num_player_2_wins += result[1]
            num_player_3_wins += result[2]
            num_player_4_wins += result[3]
            player_1_scores += result[4]
            player_2_scores += result[5]
            player_3_scores += result[6]
            player_4_scores += result[7]
            results_collected += 1
        except Exception as e:
            print(f"Warning: Failed to collect result from worker {i}: {e}")

    if results_collected < num_workers:
        print(f"Warning: Only collected results from {results_collected}/{num_workers} workers")

    num_total_wins = num_player_1_wins + num_player_2_wins + num_player_3_wins + num_player_4_wins
    if num_total_wins == 0:
        print('Error: No results collected. Please check model loading and worker errors above.')
        return
    print('WP results:')
    print('player 1 : player 2 : player 3 : player 4 - {:.3f} : {:.3f} : {:.3f} : {:.3f}'.format(
        num_player_1_wins / num_total_wins,
        num_player_2_wins / num_total_wins,
        num_player_3_wins / num_total_wins,
        num_player_4_wins / num_total_wins))
    print('ADP results:')
    print('player 1 : player 2 : player 3 : player 4 - {:.3f} : {:.3f} : {:.3f} : {:.3f}'.format(
        player_1_scores / num_total_wins,
        player_2_scores / num_total_wins,
        player_3_scores / num_total_wins,
        player_4_scores / num_total_wins))
