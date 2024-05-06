# Discord Text-Based Minigame Bot

Several discalimers!

- This repository was created on the fly while trying to make small text-based minigames in discord.
- As it was only ever intended to be run while I was there to correct any mistakes that actually cause errors, I am sure there are many more bugs still left that have not been found.
- In addition, the code, while fairly versatile, is not friendly to work with and probably requires many small edits to lots of files to implement features which should be simple, but I never though to add.
- I designed these games to work with between two and six people. Some may work with more, some may not.

So be warned.

Here are the steps to set the code up.

- Install all nessasary python libraries using the following command from the inside the top directory of the project:

```console
pip install -r requirements.txt
```

- Download missing data resources.
  - I have excluded 'data/lichess_db_puzzle.csv' from this repository as it is rather large.
    - I found this chess puzzle .csv at "https://database.lichess.org/#puzzles".
    - It could, in theory, be replaced by any csv with chess puzzles in the correct format.
    - The format is:
    > "PuzzleId,FEN,Moves,Rating, RatingDeviation,Popularity,NbPlays,Themes,GameUrl,OpeningTags"
    - I only use FEN, Moves, Rating, and Popularity.
    - Moves are seperated by spaces, and the first move is the opponents move.
  - Download wornet with

'''python
import nltk
nltk.download('wordnet')
'''

- Create your "local_config.yaml" file in the base directory as shown

``` yaml
discord_config:
  token: "" #insert your token here
config:
  command_users: [0,0] #list you command users's discord ids in here
  main_channel_id: 0 #add the bot's main channel id here
  players: [ #add your players discord id's here
    0,
    0,
    0
  ]
```

- Run 'main.py' to launch a game!
