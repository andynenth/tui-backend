#!/usr/bin/env python3
"""Test that avatar colors are never duplicated for players in the same room"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine.room import Room
from engine.player import Player


def test_no_duplicate_colors():
    """Test that no duplicate colors are assigned when multiple players join"""
    room = Room("test_room", "Host")

    # Host should have a color
    host_color = room.players[0].avatar_color
    print(f"✅ Host color: {host_color}")
    assert host_color is not None

    # Add more human players
    player_names = ["Alice", "Bob", "Charlie", "Dave", "Eve", "Frank", "Grace"]
    assigned_colors = [host_color]

    for i, name in enumerate(player_names):
        # Replace bots with humans
        slot = i + 1
        if slot < 4:
            room.assign_slot(slot, name)
            player = room.players[slot]
            print(f"✅ {name} assigned to slot {slot}, color: {player.avatar_color}")

            # Check no duplicate
            assert (
                player.avatar_color not in assigned_colors
            ), f"Duplicate color {player.avatar_color} assigned to {name}"
            assigned_colors.append(player.avatar_color)

    print(f"\n✅ All assigned colors: {assigned_colors}")
    print(f"✅ Unique colors: {set(assigned_colors)}")
    assert len(assigned_colors) == len(
        set(assigned_colors)
    ), "Duplicate colors detected!"


def test_color_reassignment_on_rejoin():
    """Test that colors are reused when players leave and rejoin"""
    room = Room("test_room2", "Host")

    # Add players
    room.assign_slot(1, "Player2")
    room.assign_slot(2, "Player3")
    room.assign_slot(3, "Player4")

    # Record initial colors
    initial_colors = []
    for i in range(4):
        player = room.players[i]
        if player and not player.is_bot:
            initial_colors.append(player.avatar_color)
            print(f"Initial: {player.name} has color {player.avatar_color}")

    # Player2 leaves
    left_player_color = room.players[1].avatar_color
    room.assign_slot(1, None)
    print(f"\n✅ Player2 (color: {left_player_color}) left")

    # New player joins
    room.assign_slot(1, "NewPlayer")
    new_player_color = room.players[1].avatar_color
    print(f"✅ NewPlayer joined with color: {new_player_color}")

    # The new player could get the color that was freed up
    current_colors = []
    for i in range(4):
        player = room.players[i]
        if player and not player.is_bot:
            current_colors.append(player.avatar_color)

    # Check no duplicates in current state
    assert len(current_colors) == len(
        set(current_colors)
    ), "Duplicate colors after rejoin!"
    print(f"✅ No duplicate colors after player replacement")


def test_fallback_when_all_colors_taken():
    """Test fallback mechanism when more than 8 human players somehow exist"""
    # This is an edge case - normally max 4 players per room
    # But let's test the fallback logic

    all_colors = ["blue", "purple", "orange", "red", "green", "teal", "pink", "yellow"]

    # Create players manually to test edge case
    players = []
    for i, color in enumerate(all_colors):
        player = Player(f"Player{i}", is_bot=False, available_colors=[color])
        players.append(player)
        print(f"Player{i}: {player.avatar_color}")

    # 9th player should use fallback
    player9 = Player("Player9", is_bot=False, available_colors=[])
    print(f"\n✅ Player9 (no colors available): {player9.avatar_color}")
    assert player9.avatar_color in all_colors, "Fallback color not from valid set"


def test_bots_have_no_color():
    """Test that bots don't get avatar colors"""
    room = Room("test_room3", "Host")

    for i in range(4):
        player = room.players[i]
        if player:
            if player.is_bot:
                assert (
                    player.avatar_color is None
                ), f"Bot {player.name} should not have color"
                print(f"✅ Bot {player.name} has no color (None)")
            else:
                assert (
                    player.avatar_color is not None
                ), f"Human {player.name} should have color"
                print(f"✅ Human {player.name} has color: {player.avatar_color}")


if __name__ == "__main__":
    print("🎨 Testing Avatar Color Assignment System\n")

    print("Test 1: No duplicate colors")
    print("-" * 40)
    test_no_duplicate_colors()

    print("\n\nTest 2: Color reassignment on rejoin")
    print("-" * 40)
    test_color_reassignment_on_rejoin()

    print("\n\nTest 3: Fallback when all colors taken")
    print("-" * 40)
    test_fallback_when_all_colors_taken()

    print("\n\nTest 4: Bots have no color")
    print("-" * 40)
    test_bots_have_no_color()

    print("\n\n✅ All avatar color tests passed!")
