from environment.move_detector import get_move_info
from environment.utils import EnvCard2RealCard, Typenum2RealType


class HumanPlayer:

    def __init__(self):
        self.position = None

    def act(self, info_set):
        self._display_game_state(info_set)

        valid_actions = info_set.legal_actions

        print("\navailable actions：")
        for i, action in enumerate(valid_actions):
            if action == []:
                print(f"{i}: pass")
            else:
                type = Typenum2RealType[get_move_info(action, wild_card_of_game=info_set.wild_card_of_game)['type']]
                print_action = ''
                for card in [EnvCard2RealCard[k] for k in action]:
                    print_action += (card + ', ')
                print_action = print_action[:-2]
                print(f"{i}: {type}     {print_action}")

        while True:
            try:
                choice = int(input("\nchoose your action (input the action's code): "))
                if 0 <= choice < len(valid_actions):
                    return valid_actions[choice]
                print("invalid input!")
            except ValueError:
                print("please enter valid number")

    def _display_game_state(self, info_set):
        print("\n" + "=" * 50)
        print("game state now：")
        print(f"your position: {info_set.player_position}")
        players_remain = ''
        for player in info_set.players_remain:
            players_remain += (player + ', ')
        players_remain = players_remain[:-2]
        print(f'players remain: {players_remain}')
        for i in range(-5, 0):
            try:
                if info_set.players_seq[i]:
                    print("=" * 50)
                    print(f'player: {info_set.players_seq[i]}')
                    if info_set.card_play_action_seq[i] == []:
                        print('pass')
                    else:
                        action = ''
                        for card in [EnvCard2RealCard[k] for k in info_set.card_play_action_seq[i]]:
                            action += (card + ', ')
                        action = action[:-2]
                        print(f'action: {action}')
                        print(
                            f"type: {Typenum2RealType[get_move_info(info_set.card_play_action_seq[i], wild_card_of_game=info_set.wild_card_of_game)['type']]}")
            except:
                pass

        print("=" * 50)
