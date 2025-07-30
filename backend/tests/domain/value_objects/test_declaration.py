"""
Tests for the Declaration value object.
"""

import pytest
from domain.value_objects.declaration import Declaration, DeclarationSet


class TestDeclaration:
    """Test the Declaration value object."""

    def test_create_valid_declaration(self):
        """Test creating a valid declaration."""
        decl = Declaration.create("Alice", 3)

        assert decl.player_name == "Alice"
        assert decl.pile_count == 3
        assert decl.is_forced is False
        assert decl.is_zero is False
        assert decl.is_maximum is False

    def test_create_zero_declaration(self):
        """Test creating a zero declaration."""
        decl = Declaration.create("Bob", 0)

        assert decl.pile_count == 0
        assert decl.is_zero is True
        assert decl.is_maximum is False

    def test_create_maximum_declaration(self):
        """Test creating a maximum declaration."""
        decl = Declaration.create("Carol", 8)

        assert decl.pile_count == 8
        assert decl.is_zero is False
        assert decl.is_maximum is True

    def test_forced_declaration(self):
        """Test creating a forced declaration."""
        decl = Declaration.create("Dave", 1, is_forced=True)

        assert decl.pile_count == 1
        assert decl.is_forced is True

    def test_invalid_pile_count(self):
        """Test that invalid pile counts raise errors."""
        # Negative
        with pytest.raises(ValueError, match="between 0 and 8"):
            Declaration.create("Alice", -1)

        # Too high
        with pytest.raises(ValueError, match="between 0 and 8"):
            Declaration.create("Alice", 9)

        # Non-integer
        with pytest.raises(ValueError, match="must be an integer"):
            Declaration("Alice", "3", False)

    def test_empty_player_name(self):
        """Test that empty player name raises error."""
        with pytest.raises(ValueError, match="Player name cannot be empty"):
            Declaration.create("", 3)

    def test_matches_actual(self):
        """Test checking if declaration matches actual."""
        decl = Declaration.create("Alice", 3)

        assert decl.matches_actual(3) is True
        assert decl.matches_actual(2) is False
        assert decl.matches_actual(4) is False

    def test_get_difference(self):
        """Test getting difference between declared and actual."""
        decl = Declaration.create("Alice", 3)

        assert decl.get_difference(3) == 0  # Perfect match
        assert decl.get_difference(5) == 2  # Captured 2 more
        assert decl.get_difference(1) == -2  # Captured 2 less

    def test_immutability(self):
        """Test that Declaration is immutable."""
        decl = Declaration.create("Alice", 3)

        with pytest.raises(AttributeError):
            decl.pile_count = 4

        with pytest.raises(AttributeError):
            decl.player_name = "Bob"

    def test_to_dict(self):
        """Test converting to dictionary."""
        decl = Declaration.create("Alice", 3, is_forced=True)
        data = decl.to_dict()

        assert data == {"player_name": "Alice", "pile_count": 3, "is_forced": True}

    def test_from_dict(self):
        """Test creating from dictionary."""
        data = {"player_name": "Bob", "pile_count": 5, "is_forced": False}

        decl = Declaration.from_dict(data)
        assert decl.player_name == "Bob"
        assert decl.pile_count == 5
        assert decl.is_forced is False

    def test_string_representation(self):
        """Test string representation."""
        decl1 = Declaration.create("Alice", 3)
        assert str(decl1) == "Alice declares 3"

        decl2 = Declaration.create("Bob", 1, is_forced=True)
        assert str(decl2) == "Bob declares 1 (forced)"


class TestDeclarationSet:
    """Test the DeclarationSet value object."""

    def test_create_valid_set(self):
        """Test creating a valid declaration set."""
        declarations = [
            Declaration.create("Alice", 2),
            Declaration.create("Bob", 3),
            Declaration.create("Carol", 1),
            Declaration.create("Dave", 1),
        ]

        decl_set = DeclarationSet.create(declarations)
        assert len(decl_set.declarations) == 4
        assert decl_set.get_total() == 7  # 2+3+1+1

    def test_empty_set_raises_error(self):
        """Test that empty declaration set raises error."""
        with pytest.raises(ValueError, match="cannot be empty"):
            DeclarationSet.create([])

    def test_total_equals_eight_raises_error(self):
        """Test that total of 8 raises error."""
        declarations = [
            Declaration.create("Alice", 2),
            Declaration.create("Bob", 3),
            Declaration.create("Carol", 2),
            Declaration.create("Dave", 1),  # Total = 8
        ]

        with pytest.raises(ValueError, match="Total declarations cannot equal 8"):
            DeclarationSet.create(declarations)

    def test_duplicate_players_raises_error(self):
        """Test that duplicate player declarations raise error."""
        declarations = [
            Declaration.create("Alice", 2),
            Declaration.create("Bob", 3),
            Declaration.create("Alice", 1),  # Duplicate
        ]

        with pytest.raises(ValueError, match="Duplicate player declarations"):
            DeclarationSet.create(declarations)

    def test_get_declaration_for(self):
        """Test getting declaration for specific player."""
        declarations = [Declaration.create("Alice", 2), Declaration.create("Bob", 3)]

        decl_set = DeclarationSet.create(declarations)

        alice_decl = decl_set.get_declaration_for("Alice")
        assert alice_decl is not None
        assert alice_decl.pile_count == 2

        # Non-existent player
        eve_decl = decl_set.get_declaration_for("Eve")
        assert eve_decl is None

    def test_has_all_players(self):
        """Test checking if all players have declared."""
        declarations = [
            Declaration.create("Alice", 2),
            Declaration.create("Bob", 3),
            Declaration.create("Carol", 1),
        ]

        decl_set = DeclarationSet.create(declarations)

        assert decl_set.has_all_players(["Alice", "Bob", "Carol"]) is True
        assert decl_set.has_all_players(["Alice", "Bob"]) is True
        assert decl_set.has_all_players(["Alice", "Bob", "Carol", "Dave"]) is False

    def test_immutability(self):
        """Test that DeclarationSet is immutable."""
        declarations = [Declaration.create("Alice", 2), Declaration.create("Bob", 3)]

        decl_set = DeclarationSet.create(declarations)

        # Tuple is immutable
        with pytest.raises(AttributeError):
            decl_set.declarations = []

    def test_to_dict(self):
        """Test converting to dictionary."""
        declarations = [Declaration.create("Alice", 2), Declaration.create("Bob", 3)]

        decl_set = DeclarationSet.create(declarations)
        data = decl_set.to_dict()

        assert data["total"] == 5
        assert len(data["declarations"]) == 2
        assert data["declarations"][0]["player_name"] == "Alice"

    def test_from_dict(self):
        """Test creating from dictionary."""
        data = {
            "declarations": [
                {"player_name": "Alice", "pile_count": 2, "is_forced": False},
                {"player_name": "Bob", "pile_count": 3, "is_forced": True},
            ],
            "total": 5,
        }

        decl_set = DeclarationSet.from_dict(data)
        assert len(decl_set.declarations) == 2
        assert decl_set.get_total() == 5
        assert decl_set.declarations[1].is_forced is True
