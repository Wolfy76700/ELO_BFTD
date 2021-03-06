from copy import deepcopy
from numpy import log


def calculate_power_points(player_database):
    ratio = 10
    for player_name in player_database.keys():
        mu_value = player_database[player_name].get("rating_mu")
        player_database[player_name]["power_points"] = int(mu_value*ratio)


def get_previous_rating(player_name, player_database):
    if player_name in player_database.keys():
        previous_rating_mu = player_database[player_name].get("rating_mu")
        previous_match_count = player_database[player_name].get(
            "match_count")

    else:
        previous_rating_mu = 1200
        previous_match_count = 0

    return(previous_rating_mu, previous_match_count)


def remove_players_without_matches(player_database):
    og_dict = deepcopy(player_database)
    for player_name in og_dict.keys():
        if player_database[player_name].get("match_count") == 0:
            del player_database[player_name]

def adjust_elo_for_tournament_win(elo, number_participants, ranking=1):
    ratio = 2
    adjust_factor = log(number_participants)/ranking
    participation_factor = log(number_participants)/3
    new_elo = elo+((adjust_factor+participation_factor)*ratio)
    return(new_elo)
