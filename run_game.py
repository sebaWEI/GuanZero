# run_game.py
    
from environment.move_detector import get_move_type
from environment.utils import *
from environment.move_generator import MoveGenerator
import random

my_cards = []
wild_card_of_game = 1#wild card can be changed if you want to test different wild card
for i in range(10):
    my_cards.append(random.randint(0, 53))
wild_card_number = my_cards.count(wild_card_of_game)
while (wild_card_number <=1):
    my_cards.append(wild_card_of_game)
    wild_card_number += 1#add wild card to my cards to make our moves more interesting
print(f"my cards: {my_cards}")
Generator = MoveGenerator(my_cards)

move_to_detect_set=Generator.gen_moves()

def main(move_to_detect):
    detector = get_move_type(move_to_detect)
    move_to_show = [EnvCard2RealCard[i] for i in move_to_detect]
    print(f"Move to Detect: {move_to_show}")
    print(f"Detected Move Type: {detector['type']}, Rank: {detector['rank']})")

if __name__ == "__main__":
    print("Starting Move Detector Test")
    for move in move_to_detect_set:
        main(move)
    print("Move Detector Test Completed")
   