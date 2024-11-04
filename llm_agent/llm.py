import sys
import os
import argparse
import time
import json


import openai
from tqdm import tqdm

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

SYSTEM_PROMPT = """你是一个德州扑克游戏中的解释器。"""

# pylint: disable=line-too-long
USER_PROMPT = """结合玩家位置、对手位置、玩家手牌、玩家手牌范围、对手手牌范围等信息，你需要通过下面几点对GTO结果中各项行动的原因进行解释：
1. 分析当前的公共牌面有什么影响
2. 根据对手在翻前/翻牌/转牌/河牌面上的行动，分析对手的范围可能包括了哪些价值组合，听牌组合
3. 分析玩家手牌的强弱，以及玩家手牌对对手牌力的影响

下面首先会展示几个正确的例子:
{example}

学习完了上面几个例子，请基于下面的局面信息，按照初步分析和术语表，解释GTO策略中各项动作的原因：
{query}

在举例时，你需要参靠下面的初步分析：
{analysis}

同时，你需要参考下面的术语字典：
{terms}
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


def process_raw(engine_results: dict) -> tuple:
    hand = Hand(engine_results["hand"])
    board = Board(engine_results["board"])
    # 面high是否需要单独处理？
    hand_rankings, draws = evaluate_hand(hand, board)

    # TODO:这里的tops应该用对手数据做输入
    tops = get_top_combinations(
        engine_results["hands"], engine_results["weights"], engine_results["ev"], effective_stack=400, top_n=2
    )
    return hand_rankings, draws, tops


def fill_analysis(result: tuple) -> str:
    analysis = "玩家已经成牌："
    hand_rankings, draws, tops = result
    for key, value in list(reversed(hand_rankings.items())):
        if value:
            analysis = analysis + str(TERM_MAP[key])
            break
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
    return analysis


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
            max_tokens=1024,
        )
        return chat_completion.choices[0].message.content
    except Exception as ex:  # pylint: disable=broad-except # noqa: BLE001
        print(ex)
        time.sleep(3)
    return "error"


def force_correct(content: str) -> str:
    # TODO: correct terms and examples
    # How to match regular expressions?
    return content


def main() -> None:
    """The main function."""
    args = parse_arguments()

    with open("llm_agent/example.txt", encoding="utf-8") as f:
        example = f.read()

    with open("llm_agent/terms.txt", encoding="utf-8") as f:
        terms = f.read()

    with open("llm_agent/engine_results.json", encoding="utf-8") as f:
        engine_results = json.load(f)
        analysis = fill_analysis(process_raw(engine_results))

    # 这里query其实应该从engine_results中生成
    # 所以engine_results里应该包含query中需要的数据，例如位置、玩家手牌等
    # 范围是否应该选取当前的对手范围？
    with open("llm_agent/query.txt", encoding="utf-8") as f:
        query = f.read()

    user_prompt = USER_PROMPT.format(
        example=example,
        query=query,
        terms=terms,
        analysis=analysis,
    )

    print(user_prompt)

    content = explain(sys_prompt=SYSTEM_PROMPT, user_prompt=user_prompt)
    content = force_correct(content)

    with open(args.output_dir, mode="w", encoding="utf-8") as f:
        f.write(content)
        f.close()


main()
