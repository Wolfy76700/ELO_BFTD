import json
from pathlib import Path
from modules import system as system_functions
from markdown import markdown as markdown_converter

data_folder = "data"
result_folder = "result"


with open(f"{data_folder}/tournaments.json", 'rt') as tournaments_file:
    tournaments_dict = json.loads(tournaments_file.read())

elo_results, result_summary = system_functions.calculate_elo_for_all_games(
    tournaments_dict, csv_save_folder=result_folder)

Path(result_folder).mkdir(parents=True, exist_ok=True)
with open(f"{result_folder}/elo_results.json", 'wt') as elo_results_file:
    elo_results_file.write(json.dumps(elo_results, indent=2))

with open(f"{result_folder}/result_summary.md", 'wt', encoding='utf-8') as result_summary_file:
    result_summary_file.write(result_summary)

with open(f"{result_folder}/result_summary.html", 'wt', encoding='utf-8') as result_summary_webpage:
    result_summary_webpage.write(markdown_converter(result_summary, extensions=['extra']))
