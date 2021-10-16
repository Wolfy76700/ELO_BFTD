from modules import challonge as challonge
from modules import smashgg as smashgg
from modules import common as common


def get_ratings_list_from_player_database(player_database):
    ratings_list = []
    for player_name in player_database.keys():
        if ratings_list:
            for i in range(len(ratings_list)):
                added = False
                if player_database[player_name].get("rating_mu") > player_database[ratings_list[i]].get("rating_mu"):
                    ratings_list.insert(i, player_name)
                    added = True
                    break
            if not added:
                ratings_list.append(player_name)
        else:
            ratings_list.append(player_name)
    return(ratings_list)


def calculate_elo_for_game(game_dict):
    player_database = {}
    for tournament_name in game_dict.keys():
        if game_dict[tournament_name].get("type") == "Challonge":
            challonge.calculate_elo_for_challonge_tournament(
                game_dict[tournament_name], player_database)
        elif game_dict[tournament_name].get("type") == "Smashgg":
            smashgg.calculate_elo_for_smashgg_tournament(
                game_dict[tournament_name], player_database)
    common.remove_players_without_matches(player_database)
    common.calculate_power_points(player_database)
    ranks_list = get_ratings_list_from_player_database(player_database)
    return(player_database, ranks_list)


def calculate_elo_for_all_games(tournaments_dict):
    result = {}
    result_summary = '# GENERATED RANKINGS:\n\n'
    for game_name in tournaments_dict.keys():
        player_database, ranks_list = calculate_elo_for_game(
            tournaments_dict[game_name])
        result[game_name] = {
            "rankings": ranks_list,
            "detail": player_database
        }
        result_summary = result_summary + \
            f"## RANKINGS FOR {game_name.upper()}\n\n"
        for index in range(len(ranks_list)):
            player_name = ranks_list[index]
            result_summary = result_summary + \
                f"{index+1}. {player_name} (Power points: {player_database[player_name].get('power_points')})  \n"

        result_summary = result_summary + '\n'

    result_summary = result_summary.strip()

    return(result, result_summary)
