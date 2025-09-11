import multiprocessing as mp
import pickle
import numpy as np

from environment.game import GameEnv

from random_agent import RandomAgent
from agent import GuanZeroAgent
from human_player import HumanPlayer

deck = []
for i in range(0, 54):
    deck.extend([i for _ in range(2)])


def load_card_play_models():
    players = {}

    for position in ['player_1', 'player_2', 'player_3']:
        from random_agent import RandomAgent
        players[position] = RandomAgent
    from human_player import HumanPlayer
    players['player_4'] = HumanPlayer
    return players


def create_game_with_players(model_path, player_config=None, wild_card_of_game=1):
    """
    Args:
        model_path: the path of pretrained model

        player_config: Dict[str, str]：
            {
                'player_1': 'human',
                'player_2': 'ai',
                'player_3': 'random',
                'player_4': 'ai'
            }

        wild_card_of_game: wild card of a single game
    """
    if player_config is None:
        player_config = {
            'player_1': 'human',
            'player_2': 'random',
            'player_3': 'random',
            'player_4': 'random'
        }

    players = {}
    for position in ['player_1', 'player_2', 'player_3', 'player_4']:
        player_type = player_config.get(position, 'random')
        if player_type == 'human':
            players[position] = HumanPlayer()
        elif player_type == 'ai':
            if not model_path:
                raise ValueError(f"AI player {position} requires model_path")
            players[position] = GuanZeroAgent(model_path)
        else:  # 'random' or default
            players[position] = RandomAgent()

    return GameEnv(players, wild_card_of_game=wild_card_of_game)


def play_single_game(model_path=None, player_config=None, wild_card_of_game=1):
    env = create_game_with_players(model_path, player_config, wild_card_of_game=wild_card_of_game)

    _deck = deck.copy()
    np.random.shuffle(_deck)
    player_hand_dict = {
        'player_1': _deck[:27],
        'player_2': _deck[27:54],
        'player_3': _deck[54:81],
        'player_4': _deck[81:108]
    }

    for player in player_hand_dict:
        player_hand_dict[player].sort()

    env.card_play_init(player_hand_dict)

    while not env.game_over:
        env.step()

    return {
        'wins': env.num_wins,
        'scores': env.scores
    }


def mp_simulate(card_play_data_list, model_path, q, player_config, wild_card_of_game=1):
    env = create_game_with_players(model_path, player_config, wild_card_of_game=wild_card_of_game)
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


def evaluate(model_path, eval_data, num_workers, player_config):
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
            args=(card_play_data, model_path, q, player_config))
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


if __name__ == "__main__":
    config = {
        'player_1': 'ai',
        'player_2': 'human',
        'player_3': 'random',
        'player_4': 'random'
    }

    try:
        result = play_single_game(model_path="/Users/weiziheng/Documents/GitHub/GuanZero/guanzero_checkpoints/guanzero/guandan_weights_636800.ckpt",
                                  player_config=config,
                                  wild_card_of_game=1)
        print("\ngame over!")
        print("wins:", result['wins'])
        print("scores:", result['scores'])
    except Exception as e:
        print(f"errors during game: {e}")
