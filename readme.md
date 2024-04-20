## Discord Text-Based Minigame Bot

Several discalimers!

- This repository was created on the fly while trying to make small text-based minigames in discord.
- As it was only ever intended to be run while I was there to correct any mistakes that actually cause errors, I am sure there are many more bugs still left that have not been found.
- In addition, the code, while fairly versatile, is not friendly to work with and probably requires many small edits to lots of files to implement features which should be simple, but I never though to add.
- I designed these games to work with between two and six people. Some may work with more, some may not.

So be warned.

Here are the steps to set the code up.

- Install all nessasary python libraries.
  - "fogleman_TWL06_scrabble" is not an available library, but is merely the "twl.py" file from "https://github.com/fogleman/TWL06" by Michael Fogleman
- Download missing data resources.
  - I have excluded 'data/lichess_db_puzzle.csv' from this repository as it is rather large.
    - I found this chess puzzle .csv at "https://database.lichess.org/#puzzles".
    - It could, in theory, be replaced by any csv with chess puzzles in the correct format.
    - The format is:
    > "PuzzleId,FEN,Moves,Rating, RatingDeviation,Popularity,NbPlays,Themes,GameUrl,OpeningTags"
    - I only use FEN, Moves, Rating, and Popularity.
    - Moves are seperated by spaces, and the first move is the opponents move.
- Create your "discord_config_local.py" file in the main directory like so:
  - add your bot's discord api token

``` python
    discord_config = {
        "token" : "<your discord bot's api token here>", #https://discord.com/developers/docs/intro
    }
```

- Then create you "config_local.py" file in the main directory like so:
  - add the channel id your game should run out of
  - add the player id's of who will be playing
  - add the player id's of who should have command access

``` python
    config:'ConfigDict' = {
        'command_users' : [00000,00000],#user id's of users who can use commands
        'main_channel_id' : 00000, #channel id of the channel the games will run in
        'players' : [#user id's of players
            00000,
            00000,
            00000,
            00000
        ]
    }
```

- Run 'main.py' to launch a game!
