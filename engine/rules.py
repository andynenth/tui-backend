# rules.py
# ------------------------------
# Available Play Types
# ------------------------------
# SINGLE             → 1 piece
# PAIR               → 2 same name and color
# THREE_OF_A_KIND    → 3 SOLDIERs of same color
# STRAIGHT           → 3 of GENERAL, ADVISOR, ELEPHANT or CHARIOT, HORSE, CANNON (same color)
# FOUR_OF_A_KIND     → 4 SOLDIERs of same color
# EXTENDED_STRAIGHT  → 4 pieces of the same group (GENERAL–ELEPHANT or CHARIOT–CANNON),
#                      same color, 1 piece must be duplicated (e.g., HORSE appears twice)
# EXTENDED_STRAIGHT_5 → 5 pieces of the same group and color, with 2 pieces duplicated 
#                       (e.g., HORSE and CANNON appear twice), still only 3 unique types
# FIVE_OF_A_KIND     → 5 SOLDIERs of same color
# DOUBLE_STRAIGHT    → 2 CHARIOTs, 2 HORSEs, 2 CANNONs (same color)


from collections import Counter

# -------------------------------------------------
# Priority order of play types (used for comparison)
# -------------------------------------------------

PLAY_TYPE_PRIORITY = [
    "SINGLE",
    "PAIR",
    "THREE_OF_A_KIND",
    "STRAIGHT",
    "FOUR_OF_A_KIND",
    "EXTENDED_STRAIGHT",
    "EXTENDED_STRAIGHT_5",
    "FIVE_OF_A_KIND",
    "DOUBLE_STRAIGHT"
]


# -------------------------------------------------
# Determine the type of a given play
# -------------------------------------------------

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

    if len(pieces) == 5:
        if is_five_of_a_kind(pieces):
            return "FIVE_OF_A_KIND"
        elif is_extended_straight_5(pieces):
            return "EXTENDED_STRAIGHT_5"

    if len(pieces) == 6 and is_double_straight(pieces):
        return "DOUBLE_STRAIGHT"

    return "INVALID"

def is_valid_play(pieces):
    return get_play_type(pieces) != "INVALID"

# -------------------------------------------------
# Play type validation functions
# -------------------------------------------------

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

def is_extended_straight_5(pieces):
    if len(pieces) != 5:
        return False

    color = pieces[0].color
    names = [p.name for p in pieces]
    counter = Counter(names)
    name_set = set(names)

    valid_groups = [
        {"GENERAL", "ADVISOR", "ELEPHANT"},
        {"CHARIOT", "HORSE", "CANNON"}
    ]

    return (
        all(p.color == color for p in pieces) and
        any(name_set.issubset(group) for group in valid_groups) and
        sorted(counter.values()) == [1, 2, 2]  # two duplicates
    )

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

# -------------------------------------------------
# Compare two plays of the same type
# -------------------------------------------------

def compare_plays(p1, p2):
    # Determine the play types of both inputs
    type1 = get_play_type(p1)
    type2 = get_play_type(p2)

    # If the play types are different, they cannot be compared
    if type1 != type2:
        return -1  # Invalid comparison

    # For extended straights (both 4-piece and 5-piece), 
    # compare using only the top 3 unique piece types (no duplicates)
    if type1 in ["EXTENDED_STRAIGHT", "EXTENDED_STRAIGHT_5"]:
        
        def core_sum(pieces):
            names_seen = set()  # Track unique piece names
            total = 0           # Accumulator for the score of top 3 unique pieces

            # Sort pieces by point value descending
            for p in sorted(pieces, key=lambda x: -x.point):
                if p.name not in names_seen:
                    names_seen.add(p.name)
                    total += p.point
                # Stop once we have 3 different types
                if len(names_seen) == 3:
                    break

            return total

        # Calculate scores based on core 3 unique types only
        sum1 = core_sum(p1)
        sum2 = core_sum(p2)

    else:
        # For all other play types, sum the total point values normally
        sum1 = sum(p.point for p in p1)
        sum2 = sum(p.point for p in p2)

    # Determine which play has the higher score
    if sum1 > sum2:
        return 1  # p1 wins
    elif sum2 > sum1:
        return 2  # p2 wins
    else:
        return 0  # Tie


