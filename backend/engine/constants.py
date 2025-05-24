# -------------------------------------------------
# Piece Point Values
# -------------------------------------------------
# This dictionary maps each unique piece (by name and color) to its point value.
# These values are used to determine:
# - Strength when comparing plays
# - Turn winners
# - Sorting for combo resolution
#
# Higher numbers = stronger pieces.
# Note: RED pieces are generally stronger than BLACK pieces of the same type.
# -------------------------------------------------

PIECE_POINTS = {
    "GENERAL_RED": 14,
    "GENERAL_BLACK": 13,
    "ADVISOR_RED": 12,
    "ADVISOR_BLACK": 11,
    "ELEPHANT_RED": 10,
    "ELEPHANT_BLACK": 9,
    "CHARIOT_RED": 8,
    "CHARIOT_BLACK": 7,
    "HORSE_RED": 6,
    "HORSE_BLACK": 5,
    "CANNON_RED": 4,
    "CANNON_BLACK": 3,
    "SOLDIER_RED": 2,
    "SOLDIER_BLACK": 1,
}
