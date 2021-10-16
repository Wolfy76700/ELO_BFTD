import trueskill
import json
from urllib.parse import urlencode
from urllib.request import Request, HTTPBasicAuthHandler, build_opener
from datetime import datetime
from modules import common as common

data_folder = "data"

with open(f"{data_folder}/_challonge_api_key.txt", 'rt') as challonge_key_file:
    challonge_key_file_contents = challonge_key_file.readline().strip().split(":")
    challonge_username = challonge_key_file_contents[0]
    challonge_api_key = challonge_key_file_contents[1]

with open(f"{data_folder}/challonge_to_smashgg.json", 'rt') as challonge_names_file:
    alt_names = json.loads(challonge_names_file.read())

challonge_tournament_list_url = "https://api.challonge.com/v1/tournaments.json"


def order_challonge_tournament_matches_by_date(matches_request_list):
    ordered_list = []
    for match in matches_request_list:
        if ordered_list:
            for i in range(len(ordered_list)):
                added = False
                if datetime.fromisoformat(match.get("match").get("updated_at")) > datetime.fromisoformat(ordered_list[i].get("match").get("updated_at")):
                    ordered_list.insert(i, match)
                    added = True
                    break
            if not added:
                ordered_list.append(match)
        else:
            ordered_list.append(match)
    return(ordered_list)


def get_challonge(url, username, api_key):
    request_obj = Request(url)

    request_obj.get_method = lambda: "GET"

    auth_handler = HTTPBasicAuthHandler()
    auth_handler.add_password(
        realm="Application",
        uri=request_obj.get_full_url(),
        user=username,
        passwd=api_key
    )
    opener = build_opener(auth_handler)

    request = opener.open(request_obj)

    if request.status == 200:
        return(json.loads(request.read()))
    else:
        raise(
            f'Get request on URL {url} was unsuccessful, Status Code: {request.status}')


def get_challonge_tournament_id(main_url, subdomain=None):
    if subdomain:
        tournament_list_request_content = get_challonge(
            f"{challonge_tournament_list_url}?subdomain={subdomain}", challonge_username, challonge_api_key)
    else:
        tournament_list_request_content = get_challonge(
            f"{challonge_tournament_list_url}", challonge_username, challonge_api_key)

    for element in tournament_list_request_content:
        if element.get("tournament").get("url") == main_url:
            return(element.get("tournament").get("id"))


def calculate_trueskill_for_challonge_tournament(tournament_dict, player_database={}):
    subdomain = tournament_dict.get("subdomain")
    main_url = tournament_dict.get("main_url")
    tournament_id = get_challonge_tournament_id(main_url, subdomain)

    if subdomain:
        player_request_url = f'https://api.challonge.com/v1/tournaments/{tournament_id}/participants.json?subdomain={subdomain}'
    else:
        player_request_url = f'https://api.challonge.com/v1/tournaments/{tournament_id}/participants.json'
    players_in_tournament_request = get_challonge(
        player_request_url, challonge_username, challonge_api_key)

    id_to_name_dict = {}

    for participant in players_in_tournament_request:
        participant_dict = participant.get("participant")
        if participant_dict.get("checked_in"):
            main_name = None
            for key in alt_names.keys():
                if alt_names[key].get("alt_names") and participant_dict.get("name") in alt_names[key].get("alt_names"):
                    main_name = key
            if main_name:
                player_name = main_name
            else:
                player_name = participant_dict.get("name")

            id_to_name_dict[participant_dict.get("id")] = player_name

            previous_rating_mu, previous_rating_sigma, previous_match_count = common.get_previous_rating(
                player_name, player_database)

            player_database[player_name] = {
                "rating_mu": previous_rating_mu,
                "rating_sigma": previous_rating_sigma,
                "match_count": previous_match_count
            }

    if subdomain:
        matches_request_url = f'https://api.challonge.com/v1/tournaments/{tournament_id}/matches.json?subdomain={subdomain}'
    else:
        matches_request_url = f'https://api.challonge.com/v1/tournaments/{tournament_id}/matches.json'
    matches_in_tournament_request = get_challonge(
        matches_request_url, challonge_username, challonge_api_key)
    matches_in_tournament_request = order_challonge_tournament_matches_by_date(
        matches_in_tournament_request)

    for match in matches_in_tournament_request:
        match_dict = match.get("match")
        player_1_name = id_to_name_dict.get(match_dict.get("player1_id"))
        player_2_name = id_to_name_dict.get(match_dict.get("player2_id"))
        if player_1_name and player_2_name:
            rating_1 = trueskill.Rating(mu=player_database.get(player_1_name).get(
                "rating_mu"), sigma=player_database.get(player_1_name).get("rating_sigma"))
            rating_2 = trueskill.Rating(mu=player_database.get(player_2_name).get(
                "rating_mu"), sigma=player_database.get(player_1_name).get("rating_sigma"))
            if match_dict.get("winner_id") == match_dict.get("player1_id"):
                if match_dict.get("scores_csv") and match_dict.get("scores_csv") != "0-0":
                    score = match_dict.get("scores_csv").split("-")
                    for i in range(int(score[1])):
                        rating_2, rating_1 = trueskill.rate_1vs1(
                            rating_2, rating_1)
                    for i in range(int(score[0])):
                        rating_1, rating_2 = trueskill.rate_1vs1(
                            rating_1, rating_2)
                else:
                    rating_1, rating_2 = trueskill.rate_1vs1(rating_1, rating_2)
            elif match_dict.get("winner_id") == match_dict.get("player2_id"):
                if match_dict.get("scores_csv") and match_dict.get("scores_csv") != "0-0":
                    score = match_dict.get("scores_csv").split("-")
                    for i in range(int(score[0])):
                        rating_1, rating_2 = trueskill.rate_1vs1(
                            rating_1, rating_2)
                    for i in range(int(score[1])):
                        rating_2, rating_1 = trueskill.rate_1vs1(
                            rating_2, rating_1)
                else:
                    rating_2, rating_1 = trueskill.rate_1vs1(rating_2, rating_1)
            player_database[player_1_name] = {
                "rating_mu": rating_1.mu,
                "rating_sigma": rating_1.sigma,
                "match_count": player_database[player_1_name].get("match_count")+1
            }
            player_database[player_2_name] = {
                "rating_mu": rating_2.mu,
                "rating_sigma": rating_2.sigma,
                "match_count": player_database[player_2_name].get("match_count")+1
            }