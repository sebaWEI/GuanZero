# test_game_flow.py

import sys
import os

# --- 设置导入路径 ---
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
# --------------------

from environment.env import Env

# --- 第一步：定义我们的“导演”AI ---

class AggressiveAgent:
    """一个非常有攻击性的AI，总是尝试出最长的合法动作，以便快速打完牌。"""
    def __init__(self, position):
        self.position = position

    def act(self, info_set):
        legal_actions = info_set.legal_actions
        if not legal_actions:
            return None # 理论上不应该发生

        # 找到最长的合法动作（牌最多的那个）
        best_action = max(legal_actions, key=len)
        print(f"[{self.position}] (攻击型AI) 选择动作: {best_action}")
        return best_action

class PassiveAgent:
    """一个非常保守的AI，如果能不出(Pass)，就尽量不出。"""
    def __init__(self, position):
        self.position = position

    def act(self, info_set):
        legal_actions = info_set.legal_actions
        if not legal_actions:
            return None

        # 检查是否可以'Pass' (用空列表[]表示)
        if [] in legal_actions:
            print(f"[{self.position}] (保守型AI) 选择动作: Pass")
            return []
        else:
            # 如果不能Pass，就随便出个最短的
            best_action = min(legal_actions, key=len)
            print(f"[{self.position}] (保守型AI) 选择动作: {best_action}")
            return best_action

# --- 第二步：编写测试函数 ---

def test_player_finishes_and_game_continues():
    """
    测试场景：player_1先出完牌，剩下的player_2, player_3, player_4继续游戏。
    """
    print("\n--- 测试场景：一个玩家出局后，游戏继续 ---")

    # 1. 创建一个特殊的 Env，手动替换掉 DummyAgent
    #    我们不直接用 Env()，而是修改它的 players 属性
    from environment.game import GameEnv
    
    # 创建我们的“演员阵容”
    players = {
        'player_1': AggressiveAgent('player_1'), # 让 player_1 尽快打完
        'player_2': PassiveAgent('player_2'),
        'player_3': PassiveAgent('player_3'),
        'player_4': PassiveAgent('player_4'),
    }
    
    # 创建一个使用我们“导演”AI的游戏引擎
    game_env = GameEnv(players)
    
    # 2. 手动初始化牌局
    #    为了让测试更可控，我们可以发一些固定的、不平衡的牌
    #    这里先用随机发牌来演示
    import numpy as np
    from environment.env import deck # 假设deck在env.py中
    
    _deck = deck.copy()
    np.random.shuffle(_deck)
    # 给player_1发一些很容易打完的牌（比如很多炸弹或长顺子）
    # 为了简单，我们先用标准发牌
    player_hand_dict = {
        'player_1': _deck[:27],
        'player_2': _deck[27:54],
        'player_3': _deck[54:81],
        'player_4': _deck[81:108],
    }
    game_env.card_play_init(player_hand_dict)
    print("牌局已初始化。Player 1 将采取攻击性策略。")

    # 3. 游戏主循环
    step_count = 0
    while not game_env.game_over:
        step_count += 1
        current_player_id = game_env.acting_player_position
        
        print(f"\n--- 第 {step_count} 步, 轮到: {current_player_id} ---")
        print(f"    剩余玩家: {game_env.players_remain}")

        # 直接调用底层的step，因为它会调用我们设置好的AI的act方法
        try:
            game_env.step()
        except Exception as e:
            print(f"[失败] game_env.step() 发生异常: {e}")
            import traceback
            traceback.print_exc()
            break
            
        # 我们可以加一些断言来检查状态
        if len(game_env.info_sets[current_player_id].player_hand_cards) == 0:
            print(f"*** {current_player_id} 已经打完所有牌！***")
            # 断言：出完牌的玩家应该已经不在 players_remain 列表里了
            assert current_player_id not in game_env.players_remain, \
                f"{current_player_id} 出完了牌，但仍在 'players_remain' 列表中！"
            print(f"[成功] {current_player_id} 已被正确地从 'players_remain' 移除。")

    # 4. 游戏结束后打印最终结果
    if game_env.game_over:
        print("\n--- 游戏正常结束 ---")
        print(f"最终名次: {game_env.players_rank}")
    else:
        print("\n--- 测试因异常中断 ---")


# --- 第三步：运行测试 ---
if __name__ == "__main__":
    test_player_finishes_and_game_continues()