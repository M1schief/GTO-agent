from board import Board
from hand import Hand
from utils import evaluate_hand

def playground():
    # 示例 1: 测试一手高牌和公共牌
    hand1 = Hand(['Ah', 'Kd'])
    board1 = Board(['5c', '6d', '7h', '8s', '9c'])
    print(f"Hand: {hand1}")
    print(f"Board: {board1}")
    hand_rankings1, draws1 = evaluate_hand(hand1, board1)
    print("Hand Rankings:", hand_rankings1)
    print("Draws:", draws1)
    print("=" * 50)

    # 示例 2: 测试一手对子和公共牌
    hand2 = Hand(['2h', '2s'])
    board2 = Board(['5h', '6h', '7h', '8h', '9d'])
    print(f"Hand: {hand2}")
    print(f"Board: {board2}")
    hand_rankings2, draws2 = evaluate_hand(hand2, board2)
    print("Hand Rankings:", hand_rankings2)
    print("Draws:", draws2)
    print("=" * 50)

    # 示例 3: 测试同花顺
    hand3 = Hand(['Th', 'Jh'])
    board3 = Board(['Ah', 'Kh', 'Qh', '2d', '3s'])
    print(f"Hand: {hand3}")
    print(f"Board: {board3}")
    hand_rankings3, draws3 = evaluate_hand(hand3, board3)
    print("Hand Rankings:", hand_rankings3)
    print("Draws:", draws3)
    print("=" * 50)

    # 示例 4: 测试四条
    hand4 = Hand(['8d', '8s'])
    board4 = Board(['8h', '8c', '7h', '2s', '9c'])
    print(f"Hand: {hand4}")
    print(f"Board: {board4}")
    hand_rankings4, draws4 = evaluate_hand(hand4, board4)
    print("Hand Rankings:", hand_rankings4)
    print("Draws:", draws4)
    print("=" * 50)

    # 示例 5: 测试三张公共牌的情况（翻牌）
    hand5 = Hand(['Kc', 'Qc'])
    board5 = Board(['Ac', '5h', '7c'])
    print(f"Hand: {hand5}")
    print(f"Board: {board5}")
    hand_rankings5, draws5 = evaluate_hand(hand5, board5)
    print("Hand Rankings:", hand_rankings5)
    print("Draws:", draws5)
    print("=" * 50)

    # 示例 6: 测试四张公共牌的情况（转牌）
    hand6 = Hand(['9h', 'Th'])
    board6 = Board(['Jh', 'Qh', '2c', '3d'])
    print(f"Hand: {hand6}")
    print(f"Board: {board6}")
    hand_rankings6, draws6 = evaluate_hand(hand6, board6)
    print("Hand Rankings:", hand_rankings6)
    print("Draws:", draws6)
    print("=" * 50)


if __name__ == "__main__":
    playground()
