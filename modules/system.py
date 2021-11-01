from modules import challonge as challonge
from modules import smashgg as smashgg
from modules import common as common
import pykakasi
import unicodedata

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
        print(tournament_name)
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

def convert_markdownextra_table_to_csv(markdownextra_table):
    csv_table = ''
    for line in markdownextra_table.splitlines():
        if ":---:" not in line:
            csv_table = csv_table + line.replace(" | ", ',').replace("\|", '|') + "\n"
    return (csv_table)

def convert_name_to_romaji(name):
    japanese_detected = False
    for character in name:
        character_name = unicodedata.name(character)
        if ("HIRAGANA LETTER" in character_name) or ("KATAKANA LETTER" in character_name):
            japanese_detected = True

    if japanese_detected:
        kks = pykakasi.kakasi()
        conversions = kks.convert(name)
        romaji = ''
        for item in conversions:
            romaji = romaji + item.get('hepburn').capitalize()
        return(romaji)
    else:
        return(name)

def calculate_elo_for_all_games(tournaments_dict, csv_save_folder=None):
    result = {}
    result_summary = '# GENERATED RANKINGS\n\n'
    for game_name in tournaments_dict.keys():
        player_database, ranks_list = calculate_elo_for_game(
            tournaments_dict[game_name])
        result[game_name] = {
            "rankings": ranks_list,
            "detail": player_database
        }
        result_summary = result_summary + \
            f"## RANKINGS FOR {game_name.upper()}\n\n"
        result_table_markdownextra = "Rank | Player | Power Points\n:---: | :----: | :----:\n"
        for index in range(len(ranks_list)):
            player_name = ranks_list[index]
            player_name_latin = convert_name_to_romaji(player_name)
            player_name_escape = player_name_latin.replace('|', '\|')
            result_table_markdownextra = result_table_markdownextra + \
                f"{index+1} | {player_name_escape} | {player_database[player_name].get('power_points')}\n"

        if csv_save_folder:
            csv_table = convert_markdownextra_table_to_csv(result_table_markdownextra)
            with open(f"{csv_save_folder}/result_{game_name}.csv", 'wt', encoding='utf-8') as csv_table_file:
                csv_table_file.write(csv_table)

        result_summary = result_summary + result_table_markdownextra
        result_summary = result_summary + '\n'

    result_summary = result_summary.strip()

    return(result, result_summary)
