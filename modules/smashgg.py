import requests
import elo
import json
from datetime import datetime
from modules import common as common
from copy import deepcopy

legacy_smashgg_api = "https://api.smash.gg/"

data_folder = "data"

with open(f"{data_folder}/challonge_to_smashgg.json", 'rt', encoding="utf-8") as challonge_names_file:
    challonge_names = json.loads(challonge_names_file.read())


def get_smashgg(base_url):
    full_url = f"{legacy_smashgg_api}{base_url}"
    request = requests.get(full_url)
    if request.status_code == 200:
        return(json.loads(request.text))
    else:
        raise(
            f'Get request on URL {full_url} was unsuccessful, Status Code: {request.status_code}')


def get_player_list_from_group(group, id_to_name_dict={}, player_database={}):
    group_id = group.get("id")
    group_request_url = f'phase_group/{group_id}?expand[]=entrants'
    group_request_data = get_smashgg(group_request_url)
    entrants = group_request_data.get("entities").get("entrants")
    for entrant in entrants:
        if entrant.get("id") not in id_to_name_dict and not entrant.get("isDisqualified"):
            challonge_name = None
            for challonge_player in challonge_names.keys():
                if challonge_names[challonge_player].get("smashgg_id") == entrant.get("id") and challonge_names[challonge_player].get("smashgg_id"):
                    challonge_name = challonge_player

            if challonge_name:
                pr_name = challonge_name
            else:
                pr_name = entrant.get("name").encode('utf-8').decode('utf-8')

            id_to_name_dict[entrant.get("id")] = pr_name

            previous_rating_mu, previous_match_count = common.get_previous_rating(
                pr_name, player_database)

            player_database[pr_name] = {
                "rating_mu": previous_rating_mu,
                "match_count": previous_match_count,
                "match_count_current": 0
            }


def order_smashgg_group_matches_by_date(smashgg_group_list):
    ordered_list = []
    for match in smashgg_group_list:
        if ordered_list:
            for i in range(len(ordered_list)):
                added = False
                if match.get("updatedAtMicro") > ordered_list[i].get("updatedAtMicro"):
                    ordered_list.insert(i, match)
                    added = True
                    break
            if not added:
                ordered_list.append(match)
        else:
            ordered_list.append(match)
    return(ordered_list)


def calculate_elo_per_group(group, id_to_name_dict, player_database):
    group_id = group.get("id")
    group_request_url = f'phase_group/{group_id}?expand[]=sets'
    group_request_data = get_smashgg(group_request_url)
    sets = group_request_data.get("entities").get("sets")
    sets = order_smashgg_group_matches_by_date(sets)

    for match_dict in sets:
        if match_dict.get("entrant1Id") and match_dict.get("entrant2Id"):
            player_1_name = id_to_name_dict.get(match_dict.get("entrant1Id"))
            player_2_name = id_to_name_dict.get(match_dict.get("entrant2Id"))
            player_1_score = match_dict.get("entrant1Score")
            player_2_score = match_dict.get("entrant2score")
            if player_1_name and player_2_name and player_1_score != -1 and player_2_score != -1 and match_dict.get("winnerId") and match_dict.get("loserId"):
                rating_1 = player_database.get(player_1_name).get("rating_mu")
                rating_2 = player_database.get(player_2_name).get("rating_mu")
                if match_dict.get("winnerId") == match_dict.get("entrant1Id"):
                    if player_1_score and player_2_score and [player_1_score, player_2_score] != [0, 0]:
                        for i in range(player_2_score):
                            rating_2, rating_1 = elo.rate_1vs1(
                                rating_2, rating_1)
                        for i in range(player_1_score):
                            rating_1, rating_2 = elo.rate_1vs1(
                                rating_1, rating_2)
                    else:
                        rating_1, rating_2 = elo.rate_1vs1(
                            rating_1, rating_2)
                elif match_dict.get("winnerId") == match_dict.get("entrant2Id"):
                    if player_1_score and player_2_score and [player_1_score, player_2_score] != [0, 0]:
                        for i in range(player_1_score):
                            rating_1, rating_2 = elo.rate_1vs1(
                                rating_1, rating_2)
                        for i in range(player_2_score):
                            rating_2, rating_1 = elo.rate_1vs1(
                                rating_2, rating_1)
                    else:
                        rating_2, rating_1 = elo.rate_1vs1(rating_2, rating_1)
                player_database[player_1_name] = {
                    "rating_mu": rating_1,
                    "smashgg_id": match_dict.get("entrant1Id"),
                    "match_count": player_database[player_1_name].get("match_count") + 1,
                    "match_count_current": player_database[player_1_name].get("match_count_current")+1
                }
                player_database[player_2_name] = {
                    "rating_mu": rating_2,
                    "smashgg_id": match_dict.get("entrant2Id"),
                    "match_count": player_database[player_2_name].get("match_count") + 1,
                    "match_count_current": player_database[player_1_name].get("match_count_current")+1
                }


def get_tournament_winner_id(main_url):
    base_url = f'{main_url}?expand[]=entrants'
    tournament_data = get_smashgg(base_url)
    entrants = tournament_data.get("entities").get("entrants")
    number_participants = len(entrants)
    winner_id = None
    for entrant in entrants:
        if entrant.get("finalPlacement") == 1:
            winner_id = entrant.get("id")
    return (number_participants, winner_id)

def apply_bonus_based_on_placings(main_url, id_to_name_dict, player_database):
    base_url = f'{main_url}?expand[]=entrants'
    tournament_data = get_smashgg(base_url)
    entrants = tournament_data.get("entities").get("entrants")
    number_participants = len(id_to_name_dict)
    for entrant in entrants:
        if entrant.get("id") in id_to_name_dict.keys():
            placement = entrant.get("finalPlacement")
            player_name = id_to_name_dict[entrant.get("id")]
            if placement:
                player_database[player_name]["rating_mu"] = common.adjust_elo_for_tournament_win(player_database[player_name]["rating_mu"], number_participants, ranking=placement)  # Bonus for placing in the tourney


def calculate_elo_for_smashgg_tournament(tournament_dict, player_database={}):
    base_url = f'{tournament_dict.get("main_url")}?expand[]=groups'
    tournament_data = get_smashgg(base_url)
    groups = tournament_data.get("entities").get("groups")
    id_to_name_dict = {}
    for group in groups:
        get_player_list_from_group(group, id_to_name_dict, player_database)
        calculate_elo_per_group(group, id_to_name_dict, player_database)

    for player_name in player_database.keys():
        if player_database[player_name].get("match_count_current"):
            if player_database[player_name].get("match_count_current") == 0:
                id_to_name_dict_bak = deepcopy(id_to_name_dict)
                for id in id_to_name_dict_bak.keys():
                    if id_to_name_dict_bak[id] == player_name:
                        del id_to_name_dict[id]
            del player_database[player_name]["match_count_current"]

    if id_to_name_dict:
        apply_bonus_based_on_placings(tournament_dict.get("main_url"), id_to_name_dict, player_database)
