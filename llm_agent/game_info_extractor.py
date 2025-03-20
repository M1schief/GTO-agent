from typing import Dict, Any, List
import re
import json

import openai


def extract_poker_info() -> Dict[str, Any]:
    input_text = input(
        "请输入当前信息，请至少包含双方位置、玩家手牌、公共牌面和双方动作："
    )

    game_info_empty = {
        "user_position": "",
        "opponent_position": "",
        "user_hand": "",
        "flop": "",
        "turn": "",
        "river": "",
        "actions": [],
    }

    prompt = f"""Extract the following poker information from the given text and format it as a JSON object:
    - User's position (BTN, SB, BB, etc.)
    - Opponent's position (BTN, SB, BB, etc.)
    - User's hand (2 cards)
    - Flop cards (3 cards)
    - Turn card (1 card, optional)
    - River card (1 card, optional)
    - Actions (list of actions like Bet, Call, Raise, etc.)

    Input text: {input_text}

    Return only the JSON object in the following format:
    {{
        "user_position": "position",
        "opponent_position": "position",
        "flop": "cards",
        "turn": "card",
        "river": "card",
        "actions": ["action1", "action2", ...],
        "user_hand": "cards"
    }}
    """

    client = openai.OpenAI(base_url="https://api.deepseek.com")

    try:
        chat_completion = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": "You are a poker information extraction assistant. Extract and format poker game information into JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            stream=False,
            temperature=1.3,
            max_tokens=512,
        )
        result = chat_completion.choices[0].message.content
        match = re.search(r"\{.*\}", result, re.DOTALL)
        if match:
            game_info = json.loads(match.group(0))
            return game_info
        else:
            return "Error extracting poker information: {str(e)}"

    except Exception as e:
        print(f"Error extracting poker information: {str(e)}")
        return game_info_empty


def main():
    # Example usage
    print("Please enter the poker game information:")
    result = extract_poker_info()
    json.dump(result, open("game_info.json", "w"))
    print("\nExtracted Information:")
    print(result)


if __name__ == "__main__":
    main()
