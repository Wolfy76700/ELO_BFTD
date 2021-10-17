# ELO_BFTD

Source code for the ranking system used at WolfTV, which merges results from Challonge and Smash.gg

The ranking system is based on the ELO system and was implemented thanks to the `elo` library by sublee. The starting point value is 1200.

ELO is boosted once a tournament finishes based on your final rank in the tournament and the number of participants in that tournament. The formula for the ELO boost is `new_elo = old_elo + (2 * ln(nb_participants)/final_rank)`

## How to run the main script

1. Download Python 3.9 or higher
1. Navigate to the root of this git folder
1. Create a new virtual environment using the command `pipenv install`
1. Set up the data files (Refer to the next section)
1. Run the main script using `pipenv run python ./elo_bftd.py`

## Useful data files

In order to use the `trueskill_bftd.py` script and its associated modules, you will need to add a few files in the `data` folder

### `data/_challonge_api_key.txt`

This is where you put your Challonge API key, the contents of the file should look like this:

```
{username}:{api_key}
```

### `data/challonge_to_smashgg.json`

Use this file to map Challonge usernames to their Smash.gg player ID or other tags they use on Challonge. The contents of the file should look like this:

```
{
    "Player_1": {
        "smashgg_id": 1,
        "alt_names": [
            "Mario",
            "Kratos",
            "Banjo"
        ]
    },
    "Player_2": {
        "smashgg_id": 2,
        "alt_names": [
            "Luigi",
            "Atreus",
            "Kazooie"
        ]
    }
}
```

### `data/tournaments.json`

This is where you set the tournaments you want to count in your rankings. The contents of the file should look like this: (Note that each section is referred to as "game" in the code)

```
{
    "game_1": {
        "My_Smashgg_Bracket_1": {
            "type": "Smashgg",
            "main_url": "tournament/my-smashgg-tournament/event/game-1"
        },
        "My_Challonge_Bracket_1": {
            "type": "Challonge",
            "main_url": "MyChallonge1",
            "subdomain": "MySubdomain"
        }
    },
    "game_2": {
        "My_Smashgg_Bracket_2": {
            "type": "Smashgg",
            "main_url": "tournament/my-smashgg-tournament/event/game-2"
        },
        "My_Challonge_Bracket_2": {
            "type": "Challonge",
            "main_url": "MyChallonge2"
        }
    },
}
```

**TIP:** If you're running tournaments as part of a Challonge community, you will need to get your subdomain name or ID. In order to find it, go to your Community Settings, in the tab "Basic Information" and look for the "Subdomain" field. Note that you cannot customize your subdomain if you're not a Challonge Premier subscriber