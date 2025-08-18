import os, pickle, numpy as np
from environment.env import deck

def generate_eval_data(num_games=500, seed=0):
    rng = np.random.default_rng(seed)
    data = []
    for _ in range(num_games):
        cards = deck.copy()
        rng.shuffle(cards)
        data.append({
            'player_1': sorted(cards[:27]),
            'player_2': sorted(cards[27:54]),
            'player_3': sorted(cards[54:81]),
            'player_4': sorted(cards[81:108]),
        })
    return data

os.makedirs('evaluation', exist_ok=True)
card_play_data_list = generate_eval_data(num_games=500, seed=42)
with open('evaluation/eval.pkl', 'wb') as f:
    pickle.dump(card_play_data_list, f)
print('Saved to evaluation/eval.pkl')