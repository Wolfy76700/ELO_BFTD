import requests
import trueskill
import json
from datetime import datetime
from modules import common as common

legacy_smashgg_api = "https://api.smash.gg/"

data_folder = "data"

with open(f"{data_folder}/challonge_to_smashgg.json", 'rt') as challonge_names_file:
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

            previous_rating_mu, previous_rating_sigma, previous_match_count = common.get_previous_rating(
                pr_name, player_database)

            player_database[pr_name] = {
                "rating_mu": previous_rating_mu,
                "rating_sigma": previous_rating_sigma,
                "match_count": previous_match_count
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


def calculate_trueskill_per_group(group, id_to_name_dict, player_database):
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
                rating_1 = trueskill.Rating(mu=player_database.get(player_1_name).get(
                    "rating_mu"), sigma=player_database.get(player_1_name).get("rating_sigma"))
                rating_2 = trueskill.Rating(mu=player_database.get(player_2_name).get(
                    "rating_mu"), sigma=player_database.get(player_1_name).get("rating_sigma"))
                if match_dict.get("winnerId") == match_dict.get("entrant1Id"):
                    if player_1_score and player_2_score and [player_1_score, player_2_score] != [0, 0]:
                        for i in range(player_2_score):
                            rating_2, rating_1 = trueskill.rate_1vs1(
                                rating_2, rating_1)
                        for i in range(player_1_score):
                            rating_1, rating_2 = trueskill.rate_1vs1(
                                rating_1, rating_2)
                    else:
                        rating_1, rating_2 = trueskill.rate_1vs1(
                            rating_1, rating_2)
                elif match_dict.get("winnerId") == match_dict.get("entrant2Id"):
                    if player_1_score and player_2_score and [player_1_score, player_2_score] != [0, 0]:
                        for i in range(player_1_score):
                            rating_1, rating_2 = trueskill.rate_1vs1(
                                rating_1, rating_2)
                        for i in range(player_2_score):
                            rating_2, rating_1 = trueskill.rate_1vs1(
                                rating_2, rating_1)
                    else:
                        rating_2, rating_1 = trueskill.rate_1vs1(
                            rating_2, rating_1)
                player_database[player_1_name] = {
                    "rating_mu": rating_1.mu,
                    "rating_sigma": rating_1.sigma,
                    "smashgg_id": match_dict.get("entrant1Id"),
                    "match_count": player_database[player_1_name].get("match_count") + 1
                }
                player_database[player_2_name] = {
                    "rating_mu": rating_2.mu,
                    "rating_sigma": rating_2.sigma,
                    "smashgg_id": match_dict.get("entrant2Id"),
                    "match_count": player_database[player_2_name].get("match_count") + 1
                }


def calculate_trueskill_for_smashgg_tournament(tournament_dict, player_database={}):
    base_url = f'{tournament_dict.get("main_url")}?expand[]=groups'
    tournament_data = get_smashgg(base_url)
    groups = tournament_data.get("entities").get("groups")
    id_to_name_dict = {}
    for group in groups:
        get_player_list_from_group(group, id_to_name_dict, player_database)
        calculate_trueskill_per_group(group, id_to_name_dict, player_database)
