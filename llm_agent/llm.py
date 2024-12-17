import sys
import os
import argparse
import time

import random
import re
import pandas as pd

import openai

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gto_facts_converter import Board
from gto_facts_converter import Hand
from gto_facts_converter import evaluate_hand_with_board_filter, get_top_combinations

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
    "over_pair": "超对",
    "top_pair": "顶对",
}

STAGE_MAP = ["翻牌", "转牌", "河牌"]

QUERY = """有效筹码量：{effective_stack}BB
玩家位置：{player_position}
对手位置：{op_position}
玩家手牌：{hand}
翻后：{game}
玩家手牌范围：{player_range}
对手手牌范围：{op_range}
GTO的结果：{gto}"""

SYSTEM_PROMPT = """你是一个德州扑克游戏中的解释器。"""

# pylint: disable=line-too-long
USER_PROMPT = """结合玩家位置、对手位置、玩家手牌、玩家手牌范围、对手手牌范围等信息，你需要通过下面几点对GTO结果中各项行动的原因进行解释：
1. 分析公共牌面的干燥性和连接性

翻牌面是Td，6c，4s
转牌面是Ah，Td，6c，4s
转牌面没有同花的可能

2. 根据对手的行动，分析对手的范围可能包括了哪些价值组合，听牌组合，需要关注对手的组合有：

ATs，AT两对
66o，三条6
AAo，三条A
TTo，三条T
KQs，顺子听牌，听J

3. 分析各阶段玩家手牌的强弱，以及玩家手牌对对手牌力的影响

翻牌时玩家已经成牌：高牌J
玩家顺子听牌，听78，或8Q，或QK
玩家同花听，听Qd, 8d, 10d, 2d, 5d, 3d, Kd, 7d, 6d, Ad, 4d中的2张
玩家同花顺听牌，听7d8d，或8dQd，或QdKd

转牌时玩家已经成牌：高牌A
玩家不可能成顺子
玩家不可能成同花

请基于下面的局面信息，按照初步分析，解释GTO结果中各项动作的原因：
{query}
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
        default="llm_agent/outcome.txt",
        help="Where to store the output.",
    )

    return parser.parse_args()


def prepare_analysis_utils(hand: str, board: list) -> str:
    hand_rankings, draws = evaluate_hand_with_board_filter(Hand([hand[:2], hand[2:]]), Board(board))
    analysis = TERM_MAP[hand_rankings["max_comb"]] + str(hand_rankings[hand_rankings["max_comb"]])
    if draws["straight_draw"]:
        analysis = analysis + "\n玩家顺子听牌，听" + "，或".join(["".join(x) for x in draws["straight_draw"]])
    else:
        analysis += "\n玩家不可能成顺子"
    if draws["flush_draw"][0]:
        data = draws["flush_draw"]
        analysis = (
            analysis
            + "\n玩家同花听，听"
            + ", ".join(f"{num}{data[1]}" for num in data[0])
            + "中的"
            + str(data[2])
            + "张"
        )
    else:
        analysis += "\n玩家不可能成同花"
    if draws["straight_flush_draw"]:
        analysis = (
            analysis
            + "\n玩家同花顺听牌，听"
            + "，或".join(
                [f"{card1[0]}{card1[1]}{card2[0]}{card2[1]}" for card1, card2 in draws["straight_flush_draw"]]
            )
        )
    else:
        analysis += "\n玩家不可能成同花顺"
    return analysis


def process_raw() -> str:
    # read from the game engine
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
    stage = STAGE_MAP[len(board) - 3]
    action_history = player_data["SelectedActions"].dropna().tolist()
    action_history = action_history[0].split(";")
    player_ev = player_data["EV"].dropna().tolist()

    op_data = pd.read_csv("llm_agent/oop.csv")
    op_range = op_data["Hand"].dropna().tolist()
    op_weight = op_data["Weight"].dropna().tolist()
    op_ev = op_data["EV"].dropna().tolist()

    # random a hand and its GTO results
    # n = random.randint(0, len(player_data) - 1)
    n = 166
    hand = player_range[n]

    pattern = r"%"
    action_space = [action for action in player_data.columns if re.search(pattern, action)]
    action_probs = [f"{action[:-2]}:{player_data.iloc[n][action]*100}%" for action in action_space]
    gto = ", ".join(action_probs)

    assert player_id == "ip"
    # game history
    game = f"翻牌面是{board[0]}，{board[1]}，{board[2]}，对手{action_history[0]}"
    if len(board) >= 4:
        game += f"，玩家{action_history[1]}\n"
        game += f"转牌面是{board[3]}，{board[0]}，{board[1]}，{board[2]}，对手{action_history[2]}"
    if len(board) == 5:
        game += f"，玩家{action_history[3]}\n"
        game += f"河牌面是{board[4]}，{board[3]}，{board[0]}，{board[1]}，{board[2]}，对手{action_history[4]}"

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
    analysis = "翻牌时玩家已经成牌："
    analysis += prepare_analysis_utils(hand, board[:3])
    if len(board) >= 4:
        analysis += "\n\n转牌时玩家已经成牌："
        analysis += prepare_analysis_utils(hand, board[:4])
    if len(board) >= 5:
        analysis += "\n\n河牌时玩家已经成牌："
        analysis += prepare_analysis_utils(hand, board)

    # 这里的tops应该用对手数据做输入
    tops = get_top_combinations(op_range, op_weight, op_ev, effective_stack=effective_stack, top_n=5)
    print(tops)
    analysis = analysis + "\n\n" + stage + "时需要关注对手的组合：\n"
    for item in tops["label"].drop_duplicates().tolist():
        analysis = analysis + item + "，\n"

    with open("llm_agent/analysis.txt", "w") as f:
        f.write(analysis)

    return stage


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
            temperature=1.3,
            max_tokens=2048,
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

    # with open("llm_agent/example.txt", encoding="utf-8") as f:
    #     example = f.read()

    # stage = process_raw()
    stage = "转牌"

    with open("llm_agent/query.txt", encoding="utf-8") as f:
        query = f.read()

    with open("llm_agent/analysis.txt", encoding="utf-8") as f:
        analysis = f.read()

    user_prompt = USER_PROMPT.format(
        stage=stage,
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
