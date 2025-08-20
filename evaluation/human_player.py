from environment.move_detector import get_move_info
from environment.utils import EnvCard2RealCard


class HumanPlayer:

    def __init__(self):
        self.position = None

    def act(self, info_set):
        self._display_game_state(info_set)

        valid_actions = info_set.legal_actions

        print("\navailable actions：")
        for i, action in enumerate(valid_actions):
            print(f"{i}: {[EnvCard2RealCard[k] for k in action]}")

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
        print(f'players remain: {info_set.players_remain}')
        for i in range(-5, 0):
            try:
                if info_set.players_seq[i]:
                    print("=" * 50)
                    print(f'player: {info_set.players_seq[i]}')
                    print(f'action: {[EnvCard2RealCard[k] for k in info_set.card_play_action_seq[i]]}')
                    print(f"type: {get_move_info(info_set.card_play_action_seq[i])['type']}")
                    print("=" * 50)

            except:
                pass

        print("=" * 50)
