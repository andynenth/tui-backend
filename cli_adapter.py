# cli_adapter.py
import ui.cli as cli

def make_declare_inputs(game):
    return {
        player.name: lambda total, is_last, p=player: cli.declare_input(p, total, is_last)
        for player in game.players
    }

def make_play_inputs(game):
    return {
        player.name: lambda p=player: cli.select_play_input(p)
        for player in game.players
    }

def print_score_summary(score_data):
    cli.print_score_summary(score_data)

def print_winner(winners):
    cli.show_winner(winners)
