"""Test for Player entity"""
from player import Player


def test_player_creation():
    """Test player can be created"""
    player = Player("Bob", is_bot=True)
    assert player.name == "Bob"
    assert player.is_bot == True
    assert player.score == 0
    assert player.hand == []
    print("✅ test_player_creation passed")


def test_player_scoring():
    """Test player scoring"""
    player = Player("Alice")
    player.add_to_score(15)
    assert player.score == 15
    player.add_to_score(10)
    assert player.score == 25
    print("✅ test_player_scoring passed")


if __name__ == "__main__":
    test_player_creation()
    test_player_scoring()
    print("\n✅ All player tests passed!")
