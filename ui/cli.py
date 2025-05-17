# ui/cli.py

def show_round_banner(round_number):
    print(f"\n===== ROUND {round_number} =====")

def print_declare_phase_banner():
    print("\n🔸 --- Declare Phase ---")

def print_error(message):
    print(f"❌ {message}")

def print_turn_winner(winner, winning_play, pile_count, round_scores):
    print(f">>> 🎉 {winner.name} captures the turn with {winning_play} (+{pile_count} pts). Current score: {round_scores[winner.name]}")

def print_end_of_round_banner():
    print("\n🏁 --- End of Round ---")

def print_game_starter(player):
    print(f"{player.name} starts the game (has GENERAL_RED)")

def print_total_scores(players):
    print("\n📊 --- Total Scores ---")
    for player in players:
        print(f"{player.name}: {player.score} pts")


def print_redeal_request(player):
    print(f"🔁 {player.name} has requested a redeal!")

def print_turn_banner(turn_number):
    print(f"\n--- Turn {turn_number} ---")

def print_score_summary(score_data):
    print_end_of_round_banner()
    print("\n📊 Round Summary:")
    for p in score_data:
        print(f"{p['player'].name} → declared {p['declared']}, got {p['actual']} → {p['delta']:+} pts (×{p['multiplier']}), total: {p['total']}")


def declare_input(player, max_total, is_last_player):
    display_hand(player)
    while True:
        try:
            if player.zero_declares_in_a_row >= 2:
                print("❗ You declared 0 twice already. You cannot declare 0 again.")
                options = [1, 2, 3, 4, 5, 6, 7, 8]
            else:
                options = [0, 1, 2, 3, 4, 5, 6, 7, 8]

            value = int(input(f"{player.name}, declare (options: {options}): "))
            if value not in options:
                continue

            if is_last_player and max_total + value == 8:
                print("❌ Total declarations cannot be exactly 8.")
                continue

            return value
        except ValueError:
            continue

def display_hand(player):
    print(f"\n🃏 {player.name} hand:")
    sorted_hand = sorted(
        [(i, piece) for i, piece in enumerate(player.hand)],
        key=lambda pair: (pair[1].color != "RED", -pair[1].point)
    )

    for shown_idx, (real_idx, piece) in enumerate(sorted_hand):
        print(f"{shown_idx}: {piece}")

def select_play_input(player):
    display_hand(player)
    print_declared_points(player)
    sorted_hand = sorted(
        [(i, piece) for i, piece in enumerate(player.hand)],
        key=lambda pair: (pair[1].color != "RED", -pair[1].point)
    )
    while True:
        try:
            entry = input("Enter the indices of pieces you want to play (space-separated): ")
            selected_indices = list(map(int, entry.strip().split()))
            if not selected_indices:
                print("❌ You must play at least 1 piece.")
                continue
            if len(set(selected_indices)) != len(selected_indices):
                print("❌ Duplicate indices are not allowed.")
                continue

            # แปลงจาก index ที่โชว์ → index จริงใน player.hand
            real_indices = [sorted_hand[i][0] for i in selected_indices]
            selected = [player.hand[i] for i in real_indices]
            return selected
        except (ValueError, IndexError):
            print("❌ Invalid selection.")

def print_first_player(player):
    print(f"{player.name} starts the game (has RED_GENERAL)")
    
def print_welcome_message():
    print("=== Welcome to Tui Pro  ===")
    
def print_round_number(round_number):
    print(f"\n===== ROUND {round_number} =====")
    
def print_declared_points(player):
    print(f"{player.name} declares {player.declared} piles.")
    
def print_played_pieces(player, selected, valid, play_type):
    sorted_play = sorted(selected, key=lambda p: (p.color != "RED", -p.point))
    print(f"{player.name}'s play: {sorted_play} → {'✅' if valid else '❌'} ({play_type})")
    
def print_the_winner(winner, winning_play):
    print(f">>> Winner: {winner.name} with {winning_play}")
    
def ask_redeal(player):
    display_hand(player)
    answer = input(f"{player.name}, do you want to Redeal? (y/n): ").strip().lower()
    return answer == 'y'

def show_winner(winners):
    if not winners:
        print("\n🤷‍♂️ No winner this game.")
    elif len(winners) == 1:
        winner = winners[0]
        print(f"\n🏆 {winner.name} wins the game with {winner.score} points!")
    else:
        names = ", ".join(p.name for p in winners)
        print(f"\n🤝 It's a tie! {names} win together with {winners[0].score} points!")

