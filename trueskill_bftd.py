import json
from pathlib import Path
from modules import system as system_functions
import markdown

data_folder = "data"
result_folder = "result"


with open(f"{data_folder}/tournaments.json", 'rt') as tournaments_file:
    tournaments_dict = json.loads(tournaments_file.read())

trueskill_results, result_summary = system_functions.calculate_trueskill_for_all_games(
    tournaments_dict)

Path(result_folder).mkdir(parents=True, exist_ok=True)
with open(f"{result_folder}/trueskill_results.json", 'wt') as trueskill_results_file:
    trueskill_results_file.write(json.dumps(trueskill_results, indent=2))

with open(f"{result_folder}/result_summary.md", 'wt', encoding='utf-8') as result_summary_file:
    result_summary_file.write(result_summary)

with open(f"{result_folder}/result_summary.html", 'wt', encoding='utf-8') as result_summary_webpage:
    result_summary_webpage.write(markdown.markdown(result_summary))
