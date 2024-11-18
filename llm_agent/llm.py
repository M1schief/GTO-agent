import sys
import os
import argparse
import time

import random
import pandas as pd

import openai

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gto_facts_converter import Board
from gto_facts_converter import Hand
from gto_facts_converter import evaluate_hand, get_top_combinations

TERM_MAP = {
    "high_card": "高牌",
    "one_pair": "对子",
    "two_pair": "两对",
    "three_of_a_kind": "三条",
    "straight": "顺子",
    "flush": "同花",
    "full_house": "葫芦",
    "four_of_a_kind": "四条",
    "straight_flush": "同花顺",
    "straight_draw": "顺子听牌",
    "flush_draw": "同花听牌",
    "straight_flush_draw": "同花顺听牌",
}

QUERY = """
有效筹码量：{effective_stack}BB
玩家位置：{player_position}
对手位置：{op_position}
玩家手牌：{hand}
翻前：单次加注底池
翻后：{game}
玩家手牌范围：{player_range}
对手手牌范围：{op_range}
GTO的结果：{gto}
"""

SYSTEM_PROMPT = """你是一个德州扑克游戏中的解释器。"""

# pylint: disable=line-too-long
USER_PROMPT = """结合玩家位置、对手位置、玩家手牌、玩家手牌范围、对手手牌范围等信息，你需要通过下面几点对GTO结果中各项行动的原因进行解释：
1. 分析当前的公共牌面有什么影响
2. 根据对手的行动，分析对手的范围可能包括了哪些价值组合，听牌组合
3. 分析玩家手牌的强弱，以及玩家手牌对对手牌力的影响

下面首先会展示几个正确的例子:
{example}

学习完了上面几个例子，请基于下面的局面信息，按照初步分析和术语表，解释GTO结果中各项动作的原因：
{query}

在举例时，你需要参靠下面的初步分析：
{analysis}
"""


def parse_arguments() -> argparse.Namespace:
    """Parse the command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Explain the GTO actions",
    )

    # Model
    parser.add_argument(
        "--model",
        type=str,
        default="deepseek",
        help="The model used to generate explanation",
    )

    # Logging
    parser.add_argument(
        "--output_dir",
        type=str,
        default=None,
        help="Where to store the output.",
    )

    return parser.parse_args()


def process_raw() -> str:
    # read from the engine or the game?
    effective_stack = 100
    player_position = "BTN"
    op_position = "BB"
    player_id = "ip"

    # take player as in-position for now
    player_data = pd.read_csv("llm_agent/ip.csv")
    player_range = player_data["Hand"].dropna().tolist()
    player_weight = player_data["Weight"].dropna().tolist()

    board = player_data["CurrentBoard"].dropna().tolist()
    board = board[0].split()
    action_history = player_data["SelectedActions"].dropna().tolist()
    action_history = action_history[0].split(";")
    player_ev = player_data["EV"].dropna().tolist()

    op_data = pd.read_csv("llm_agent/oop.csv")
    op_range = op_data["Hand"].dropna().tolist()
    op_weight = op_data["Weight"].dropna().tolist()
    op_ev = op_data["EV"].dropna().tolist()

    # random a hand and its GTO results
    action_space = [player_data.columns[-2], player_data.columns[-4], player_data.columns[-6]]
    n = random.randint(0, len(player_data) - 1)
    hand = player_range[n]
    action_probs = [f"{action[:-2]}:{player_data.iloc[n][action]*100}%" for action in action_space]
    gto = ", ".join(action_probs)

    # actions of two players
    if player_id == "ip":
        player_actions = action_history[1::2]
        op_actions = action_history[0::2]
    else:
        player_actions = action_history[0::2]
        op_actions = action_history[1::2]

    # print(player_actions)
    # print(op_actions)

    # game history
    game = f"翻牌面是{board[0]}，{board[1]}，{board[2]}，对手{op_actions[0]}，玩家{player_actions[0]}\n"
    if len(board) >= 4:
        game += f"转牌面是{board[3]}，对手{op_actions[1]}\n"
    if len(board) == 5:
        game += f"河牌面是{board[4]}，对手{op_actions[2]}，玩家{player_actions[2]}"

    # query preparation
    query = QUERY.format(
        effective_stack=effective_stack,
        player_position=player_position,
        op_position=op_position,
        hand=hand,
        game=game,
        player_range=player_range,
        op_range=op_range,
        gto=gto,
    )

    with open("llm_agent/query.txt", "w") as f:
        f.write(query)

    # prepare analysis
    hand = Hand([hand[:2], hand[2:]])
    board = Board(board)
    hand_rankings, draws = evaluate_hand(hand, board)

    analysis = "玩家已经成牌："
    for key, value in list(reversed(hand_rankings.items())):
        if value:
            analysis = analysis + str(TERM_MAP[key])
            break
    print(draws)
    if draws["straight_draw"][0]:
        analysis = analysis + "\n玩家顺子听牌，听" + ",".join(map(str, draws["straight_draw"][1]))
    else:
        analysis += "\n玩家不可能成顺子"
    if draws["flush_draw"][0]:
        analysis = analysis + "\n玩家同花听牌，还需" + str(draws["flush_draw"][1]) + "张"
    else:
        analysis += "\n玩家不可能成同花"
    if draws["striaght_flush_draw"][0]:
        analysis = analysis + "\n玩家同花顺听牌，听" + ",".join(map(str, draws["straight_draw"][1]))
    else:
        analysis += "\n玩家不可能成同花顺"

    # 这里的tops应该用对手数据做输入
    tops = get_top_combinations(op_range, op_weight, op_ev, effective_stack=effective_stack, top_n=2)
    analysis = analysis + "\n需要关注对手的组合：" + str(tops["hands"].tolist())

    with open("llm_agent/analysis.txt", "w") as f:
        f.write(analysis)


def explain(sys_prompt: str, user_prompt: str) -> str:
    client = openai.OpenAI(base_url="https://api.deepseek.com")
    try:
        chat_completion = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt},
            ],
            stream=False,
            temperature=1.0,
            max_tokens=1024,
        )
        return chat_completion.choices[0].message.content
    except Exception as ex:  # pylint: disable=broad-except # noqa: BLE001
        print(ex)
        time.sleep(3)
    return "error"


def force_correct(content: str) -> str:
    # TODO: force correct terms and examples
    # How to match regular expressions?
    return content


def main() -> None:
    """The main function."""
    args = parse_arguments()

    with open("llm_agent/example.txt", encoding="utf-8") as f:
        example = f.read()

    # process_raw()

    with open("llm_agent/query.txt", encoding="utf-8") as f:
        query = f.read()

    with open("llm_agent/analysis.txt", encoding="utf-8") as f:
        analysis = f.read()

    user_prompt = USER_PROMPT.format(
        example=example,
        query=query,
        analysis=analysis,
    )

    print(user_prompt)

    content = explain(sys_prompt=SYSTEM_PROMPT, user_prompt=user_prompt)
    content = force_correct(content)

    with open(args.output_dir, mode="w", encoding="utf-8") as f:
        f.write(content)
        f.close()


main()
