# utils.py
import numpy as np
import pandas as pd


def evaluate_hand(hand, board):
    # 合并手牌和公共牌
    all_ranks = hand.ranks + board.ranks
    all_suits = hand.suits + board.suits
    all_cards = hand.cards + board.cards

    # 统计点数和花色的频率
    value_counts = get_counts(all_ranks)
    print(all_suits)
    suit_counts = get_counts(all_suits)

    # 判断同花
    is_flush, flush_suit = check_flush(suit_counts)
    if is_flush:
        # 获取所有同花花色的牌点数
        flush_ranks = [rank for rank, suit in zip(all_ranks, all_suits) if suit == flush_suit]
        # 找到最大的牌点数
        flush_rank = max(flush_ranks)
        is_flush_draw = False

    # 判断顺子
    is_straight, straight_high = check_straight(all_ranks)

    # 判断同花顺
    is_straight_flush = False
    if is_flush:
        flush_values = [rank for rank, suit in zip(all_ranks, all_suits) if suit == flush_suit]
        is_straight_flush, straight_flush = check_straight(flush_values)

    # 分析点数频率
    pairs, three_of_a_kind, four_of_a_kind = check_counts(value_counts)
    is_full_house, full_house = check_full_house(three_of_a_kind, pairs)

    # 判断听牌情况
    "Todo: 需要排除已经出现的顺子和同花顺的情况"
    is_straight_draw = check_straight_draw(all_ranks)
    if not is_flush:
        is_flush_draw = check_flush_draw(suit_counts, len(board))
    is_straight_flush_draw = check_straight_flush_draw(all_cards)

    # 返回结果
    hand_rankings = {
        'high_card': max(all_ranks),
        'one_pair': len(pairs) == 1,
        'two_pair': len(pairs) >= 2,
        'three_of_a_kind': len(three_of_a_kind) >= 1,
        'straight': is_straight,
        'flush': is_flush,
        'full_house': full_house,
        'four_of_a_kind': len(four_of_a_kind) >= 1,
        'straight_flush': is_straight_flush
    }

    draws = {
        'straight_draw': is_straight_draw,
        'flush_draw': is_flush_draw,
        'striaght_flush_draw': is_straight_flush_draw
    }

    return hand_rankings, draws


def card_value(rank):
    if rank == 'A':
        return 14  # A 可以作为最大点数
    elif rank == 'K':
        return 13
    elif rank == 'Q':
        return 12
    elif rank == 'J':
        return 11
    elif rank == 'T':
        return 10
    else:
        return int(rank)


def get_counts(items):
    counts = {}
    for item in items:
        counts[item] = counts.get(item, 0) + 1
    return counts


def check_counts(value_counts):
    pairs = []
    three_of_a_kind = []
    four_of_a_kind = []
    for value, count in value_counts.items():
        if count == 2:
            pairs.append(value)
        elif count == 3:
            three_of_a_kind.append(value)
        elif count == 4:
            four_of_a_kind.append(value)
    return pairs, three_of_a_kind, four_of_a_kind


def check_flush(suit_counts):
    for suit, count in suit_counts.items():
        if count >= 5:
            return True, suit
    return False, None


def check_straight(values):
    unique_values = set(values)
    value_list = list(unique_values)
    value_list.sort()

    # 考虑A作为1的情况
    if 14 in value_list:
        value_list.append(1)
        value_list.sort()

    for i in range(len(value_list) - 4):
        window = value_list[i:i + 5]
        if window[4] - window[0] == 4 and len(window) == 5:
            return True, window[4]
    return False, None


def check_full_house(three_of_a_kind, pairs):
    # 确保至少有一组三条
    if len(three_of_a_kind) >= 1:
        # 如果有多个三条，选择最大的
        best_three = max(three_of_a_kind)

        # 如果有对子，选择最大的对子
        if len(pairs) >= 1:
            best_pair = max(pairs)
            return True, (best_three, best_pair)

        # 如果没有对子，但有两个三条，可以把一个三条当作对子
        elif len(three_of_a_kind) > 1:
            # 选择第二大的三条作为对子
            second_best_three = sorted(three_of_a_kind)[-2]
            return True, (best_three, second_best_three)

    return False, None

def check_straight_draw(values, N=-1):
    # 将 A 视为 1 和 14
    hand_ranks = set(values)

    if 14 in values:
        hand_ranks.add(1)
    
    if N == -1:
        # 计算剩余的牌数量
        total_cards = 7  # 2 手牌 + 5 公共牌
        N = total_cards - len(values)
        
    # 如果没有剩余的牌，直接返回 False 和空列表
    if N <= 0:
        return False, None
    
    # 存储结果的列表
    missing_one_card_combinations = []
    missing_two_cards_combinations = []
    
    for start in range(1, 11):  # 顺子的起始点数
        straight = set(range(start, start + 5))
        missing_cards = straight - hand_ranks
        # 只考虑牌面在 1 到 13 的牌
        missing_cards = set(filter(lambda x: 1 <= x <= 13, missing_cards))
        num_missing = len(missing_cards)
        if 0 < num_missing <= N:
            sorted_missing = sorted(missing_cards)
            if num_missing == 1:
                if sorted_missing not in missing_one_card_combinations:
                    missing_one_card_combinations.append(sorted_missing)
            elif num_missing == 2:
                if sorted_missing not in missing_two_cards_combinations:
                    missing_two_cards_combinations.append(sorted_missing)
    
    # 遍历比较，删除重复的较大牌
    for combo_two in missing_two_cards_combinations[:]:
        larger_card = combo_two[-1]
        for combo_one in missing_one_card_combinations:
            if larger_card in combo_one:
                missing_two_cards_combinations.remove(combo_two)
                break  # 跳出内层循环，继续检查下一个组合
    
    # 合并两个缺失牌组合的列表
    missing_combinations = missing_one_card_combinations + missing_two_cards_combinations
    
    # 判断是否存在听顺
    has_straight_draw = bool(missing_combinations)
    
    return has_straight_draw, missing_combinations

def check_straight_flush_draw(cards):
    # 计算剩余的牌数量
    total_cards = 7  # 2 手牌 + 5 公共牌
    N = total_cards - len(cards)

    if N <= 0:
        return False, []

    # 按花色分类牌
    suits = {}
    for value, suit in cards:
        suits.setdefault(suit, []).append(card_value(value[0]))

    has_straight_flush_draw = False
    missing_combinations = []

    # 对每个花色的牌进行听顺检测
    for suit, values in suits.items():
        num_cards_same_suit = len(values)
        if num_cards_same_suit + N < 5:
            continue  # 不可能形成同花，检查下一个花色
        # 调用 check_straight_draw 函数
        has_draw, missing_cards = check_straight_draw(values,N)

        if has_draw:
            has_straight_flush_draw = True
            # 将缺失的牌附加花色信息
            missing_cards_with_suit = [[(rank, suit) for rank in combo] for combo in missing_cards]
            # 合并结果
            missing_combinations.extend(missing_cards_with_suit)

    return has_straight_flush_draw, missing_combinations

def check_flush_draw(suit_counts, board_size):
    for count in suit_counts.values():
        if count >= board_size:
            return True, (5 - count)
    return False

def get_top_combinations(hands, weights, ev, effective_stack, top_n):
    """
    根据手牌范围、权重和EV，计算最靠近二维特征右上角的手牌组合
    :param hands: 手牌范围列表
    :param weights: 对应手牌的权重列表
    :param ev: 对应手牌的EV列表
    :param effective_stack: 用于归一化EV的有效筹码量
    :param top_n: 返回的组合数
    :return: 最靠近右上角的组合及其对应的weights和ev
    """

    # 1. 将输入数据加载为DataFrame
    data = pd.DataFrame({
        'hands': hands,
        'weights': weights,
        'ev': ev
    })

    # 2. 对EV进行归一化
    data['ev_scaled'] = data['ev'] / effective_stack

    # 3. 计算每个组合到(0, 0)的距离
    data['distance'] = np.sqrt(data['weights'] ** 2 + data['ev_scaled'] ** 2)

    # 4. 按距离排序，取出距离最大的 top_n 个组合
    top_combinations = data.nlargest(top_n, 'distance')

    # 5. 返回hands, weights, 和 ev
    return top_combinations[['hands', 'weights', 'ev']]