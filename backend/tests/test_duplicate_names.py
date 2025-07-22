import pytest
from engine.room import Room
from engine.player import Player


def test_duplicate_names_allowed():
    """Test that duplicate names are allowed in a room"""
    room = Room("TEST123", "Host")

    # Should not raise error anymore
    room.join_room("John")
    room.join_room("John")  # Second John should be allowed

    # Check both players exist
    johns = [p for p in room.players if p and p.name == "John"]
    assert len(johns) == 2


def test_avatar_colors_assigned():
    """Test that avatar colors are assigned to human players"""
    player = Player("TestPlayer", is_bot=False)
    assert player.avatar_color is not None
    assert player.avatar_color in [
        "blue",
        "purple",
        "orange",
        "red",
        "green",
        "teal",
        "pink",
        "yellow",
    ]


def test_bots_no_color():
    """Test that bots don't get avatar colors"""
    bot = Player("Bot 1", is_bot=True)
    assert bot.avatar_color is None


def test_room_summary_includes_colors():
    """Test that room summary includes avatar colors"""
    room = Room("TEST123", "Host")
    room.join_room("Player2")

    summary = room.summary()
    for player_data in summary["players"]:
        if player_data and not player_data["is_bot"]:
            assert "avatar_color" in player_data
