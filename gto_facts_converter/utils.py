# utils.py

def evaluate_hand(hand, board):
    # 合并手牌和公共牌
    all_ranks = hand.ranks + board.ranks
    all_suits = hand.suits + board.suits

    # 统计点数和花色的频率
    value_counts = get_counts(all_ranks)
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
        'flush_draw': is_flush_draw
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


def check_straight_draw(values):
    unique_values = set(values)
    value_list = list(unique_values)
    missing_values = set()

    value_list.sort()

    # 考虑A作为1的情况
    if 14 in value_list:
        value_list.append(1)
        value_list.sort()

    for i in range(len(value_list) - 3):
        window = value_list[i:i + 4]

        if window[3] - window[0] == 3:

            if value_list[0] > 1:
                missing_values.add(value_list[0] - 1)
            if value_list[-1] < 14:
                missing_values.add(value_list[-1] + 1)
                return True, sorted(missing_values)
        elif window[3] - window[0] == 4:
            missing_values = set(range(window[0], window[0] + 5)) - set(window)
            # if len(missing_values) == 1:
            return True, missing_values
    return False


def check_flush_draw(suit_counts, board_size):
    for count in suit_counts.values():
        if count == board_size:
            return True, (5 - board_size)
    return False
