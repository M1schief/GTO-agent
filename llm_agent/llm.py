import argparse
import time

import openai
from tqdm import tqdm

from ..gto_facts_converter.board import Board
from ..gto_facts_converter.hand import Hand
from ..gto_facts_converter.utils import evaluate_hand, get_top_combinations

SYSTEM_PROMPT = """你是一个德州扑克游戏中的解释器。"""

# pylint: disable=line-too-long
USER_PROMPT = """你需要结合玩家位置、对手位置、玩家手牌、玩家手牌范围、对手手牌范围等信息，对GTO结果中各项行动的原因进行详细的解释。你需要按照下面的模板的格式进行解释：
1. 分析当前的公共牌面有什么影响
2. 根据对手在翻前/翻牌/转牌/河牌面上的行动，分析对手的范围可能包括了哪些价值组合，听牌组合
3. 分析玩家手牌的强弱，以及玩家手牌对对手牌力的影响

下面首先会展示几个正确的例子:
{example}

学习完了上面几个例子，请基于下面的局面信息，按照术语表和模板，解释GTO策略中各项动作的原因：
{query}

做解释时，你需要参考下面的术语字典：
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


def process_raw(raw: dict) -> tuple:
    hand = Hand(raw["hand"])
    board = Board(raw["board"])
    hand_rankings, draws = evaluate_hand(hand, board)

    tops = get_top_combinations(raw["hand"], raw["weights"], hand["ev"], effective_stack=400, top_n=2)
    # TODO: Fill a template with hand_rankings, draws and tops.


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
            temperature=0.9,
            max_tokens=1024,
        )
        return chat_completion.choices[0].message.content
    except Exception as ex:  # pylint: disable=broad-except # noqa: BLE001
        print(ex)
        time.sleep(3)
    return "error"


def main() -> None:
    """The main function."""
    args = parse_arguments()

    with open("example.txt", encoding="utf-8") as f:
        example = f.read()

    with open("query.txt", encoding="utf-8") as f:
        query = f.read()

    with open("terms.txt", encoding="utf-8") as f:
        terms = f.read()

    user_prompt = USER_PROMPT.format(
        example=example,
        query=query,
        terms=terms,
    )

    print(user_prompt)

    content = explain(sys_prompt=SYSTEM_PROMPT, user_prompt=user_prompt)

    with open(args.output_dir, mode="w", encoding="utf-8") as f:
        f.write(content)
        f.close()


main()
