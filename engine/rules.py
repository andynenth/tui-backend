from collections import Counter

# ------------------------------
# ENUM หรือ TYPE สำหรับ valid play
# ------------------------------

PLAY_TYPE_PRIORITY = [
    "SINGLE",
    "PAIR",
    "THREE_OF_A_KIND",
    "STRAIGHT",
    "FOUR_OF_A_KIND",
    "EXTENDED_STRAIGHT",
    "FIVE_OF_A_KIND",
    "DOUBLE_STRAIGHT"
]

# ------------------------------
# ฟังก์ชันตรวจชนิดของ play
# ------------------------------

def get_play_type(pieces):
    if len(pieces) == 1:
        return "SINGLE"

    if len(pieces) == 2 and is_pair(pieces):
        return "PAIR"

    if len(pieces) == 3:
        if is_three_of_a_kind(pieces):
            return "THREE_OF_A_KIND"
        elif is_straight(pieces):
            return "STRAIGHT"

    if len(pieces) == 4:
        if is_four_of_a_kind(pieces):
            return "FOUR_OF_A_KIND"
        elif is_extended_straight(pieces):
            return "EXTENDED_STRAIGHT"

    if len(pieces) == 5 and is_five_of_a_kind(pieces):
        return "FIVE_OF_A_KIND"

    if len(pieces) == 6 and is_double_straight(pieces):
        return "DOUBLE_STRAIGHT"

    return "INVALID"

# ------------------------------
# ฟังก์ชันตรวจว่า valid ไหม
# ------------------------------

def is_valid_play(pieces):
    return get_play_type(pieces) != "INVALID"

# ------------------------------
# ประเภท play ต่าง ๆ
# ------------------------------

def is_pair(pieces):
    return pieces[0].name == pieces[1].name and pieces[0].color == pieces[1].color

def is_three_of_a_kind(pieces):
    return all(p.name == "SOLDIER" and p.color == pieces[0].color for p in pieces)

def is_straight(pieces):
    names = [p.name for p in pieces]
    valid_groups = [
        {"GENERAL", "ADVISOR", "ELEPHANT"},
        {"CHARIOT", "HORSE", "CANNON"}
    ]
    return (
        all(p.color == pieces[0].color for p in pieces) and
        any(set(names) == group for group in valid_groups)
    )

def is_four_of_a_kind(pieces):
    return all(p.name == "SOLDIER" and p.color == pieces[0].color for p in pieces)

def is_extended_straight(pieces):
    color = pieces[0].color
    names = [p.name for p in pieces]
    counter = Counter(names)
    for group in [{"GENERAL", "ADVISOR", "ELEPHANT"}, {"CHARIOT", "HORSE", "CANNON"}]:
        if all(n in group for n in names) and all(p.color == color for p in pieces):
            if any(v == 2 for v in counter.values()):
                return True
    return False

def is_five_of_a_kind(pieces):
    return all(p.name == "SOLDIER" and p.color == pieces[0].color for p in pieces)



def is_double_straight(pieces):
    if len(pieces) != 6:
        return False

    if not all(p.color == pieces[0].color for p in pieces):
        return False

    names = [p.name for p in pieces]
    counter = Counter(names)
    return set(counter.keys()) == {"CHARIOT", "HORSE", "CANNON"} and all(v == 2 for v in counter.values())


# ------------------------------
# เปรียบเทียบ play สองชุด
# ------------------------------

def compare_plays(p1, p2):
    """เปรียบเทียบ 2 play ที่ชนิดเดียวกัน"""
    type1 = get_play_type(p1)
    type2 = get_play_type(p2)

    if type1 != type2:
        return -1  # invalid comparison

    sum1 = sum(p.point for p in p1)
    sum2 = sum(p.point for p in p2)

    if sum1 > sum2:
        return 1
    elif sum2 > sum1:
        return 2
    else:
        return 0  # draw
