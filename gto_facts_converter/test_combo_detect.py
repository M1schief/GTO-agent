import pytest
from board import Board
from hand import Hand
from utils import evaluate_hand

def test_high_card_straight():
    # 示例 1: 测试一手高牌和公共牌
    hand1 = Hand(['Ah', 'Kd'])
    board1 = Board(['5c', '6d', '7h', '8s', '9c'])
    hand_rankings1, draws1 = evaluate_hand(hand1, board1)
    assert hand_rankings1 == {'high_card': 14, 'one_pair': False, 'two_pair': False, 'three_of_a_kind': False, 'straight': True, 'flush': False, 'full_house': None, 'four_of_a_kind': False, 'straight_flush': False}
    assert draws1 == {'straight_draw': False, 'flush_draw': False}

def test_one_pair_straight_flush():
    # 示例 2: 测试一手对子和公共牌
    hand2 = Hand(['2h', '2s'])
    board2 = Board(['5h', '6h', '7h', '8h', '9d'])
    hand_rankings2, draws2 = evaluate_hand(hand2, board2)
    assert hand_rankings2 == {'high_card': 9, 'one_pair': True, 'two_pair': False, 'three_of_a_kind': False, 'straight': True, 'flush': True, 'full_house': None, 'four_of_a_kind': False, 'straight_flush': False}
    assert draws2 == {'straight_draw': (True, [1, 10]), 'flush_draw': False}

def test_royal_flush():
    # 示例 3: 测试同花顺
    hand3 = Hand(['Th', 'Jh'])
    board3 = Board(['Ah', 'Kh', 'Qh', '2d', '3s'])
    hand_rankings3, draws3 = evaluate_hand(hand3, board3)
    assert hand_rankings3 == {'high_card': 14, 'one_pair': False, 'two_pair': False, 'three_of_a_kind': False, 'straight': True, 'flush': True, 'full_house': None, 'four_of_a_kind': False, 'straight_flush': True}
    assert draws3 == {'straight_draw': False, 'flush_draw': False}

def test_four_of_a_kind():
    # 示例 4: 测试四条
    hand4 = Hand(['8d', '8s'])
    board4 = Board(['8h', '8c', '7h', '2s', '9c'])
    hand_rankings4, draws4 = evaluate_hand(hand4, board4)
    assert hand_rankings4 == {'high_card': 9, 'one_pair': False, 'two_pair': False, 'three_of_a_kind': False, 'straight': False, 'flush': False, 'full_house': None, 'four_of_a_kind': True, 'straight_flush': False}
    assert draws4 == {'straight_draw': False, 'flush_draw': False}

def test_flush_draw():
    # 示例 5: 测试三张公共牌的情况（翻牌）
    hand5 = Hand(['Kc', 'Qc'])
    board5 = Board(['Ac', '5h', '7c'])
    hand_rankings5, draws5 = evaluate_hand(hand5, board5)
    assert hand_rankings5 == {'high_card': 14, 'one_pair': False, 'two_pair': False, 'three_of_a_kind': False, 'straight': False, 'flush': False, 'full_house': None, 'four_of_a_kind': False, 'straight_flush': False}
    assert draws5 == {'straight_draw': False, 'flush_draw': False}

def test_straight_flush_draw():
    # 示例 6: 测试四张公共牌的情况（转牌）
    hand6 = Hand(['9h', 'Th'])
    board6 = Board(['Jh', 'Qh', '2c', '3d'])
    hand_rankings6, draws6 = evaluate_hand(hand6, board6)
    assert hand_rankings6 == {'high_card': 12, 'one_pair': False, 'two_pair': False, 'three_of_a_kind': False, 'straight': False, 'flush': False, 'full_house': None, 'four_of_a_kind': False, 'straight_flush': False}
    assert draws6 == {'straight_draw': (True, [1, 13]), 'flush_draw': (True, 1)}

if __name__ == "__main__":
    pytest.main()
