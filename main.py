# main.py
from engine.game import Game
from engine.win_conditions import is_game_over, get_winners
import cli_adapter as cli

def main():
    game = Game()

    while not is_game_over(game):
        game.round_number += 1
        print(f"\n===== ROUND {game.round_number} =====")

        while True:
            game._deal_pieces()
            game._set_round_start_player()
            if game._check_redeal():
                continue
            break

        score_data = game.play_round(
            declare_inputs=cli.make_declare_inputs(game),
            play_inputs=cli.make_play_inputs(game)
        )

        cli.print_score_summary(score_data)

    winners = get_winners(game)
    cli.print_winner(winners)

if __name__ == "__main__":
    main()
