## Discord Text-Based Minigame Bot


Several discalimers!
- This repository was created on the fly while trying to make small text-based minigames in discord.
- As it was only ever intended to be run while I was there to correct any mistakes that actually cause errors, I am sure there are many more bugs still left that have not been found.
- In addition, the code, while fairly versatile, is not friendly to work with and probably requires many small edits to lots of files to implement features which should be simple, but I never though to add. 

So be warned.

To begin using it:
- install all nessasary python libraries
    - 'fogleman_TWL06_scrabble' is not an available library, but is merely the twl.py file from "https://github.com/fogleman/TWL06" by Michael fogleman
- download missing data resources
    - I have excluded 'data/lichess_db_puzzle.csv' from this repository as it is rather large.
        - I found it at "https://database.lichess.org/#puzzles". It could, in theory, be replaced by any csv with chess puzzles.
        - The format is "PuzzleId,FEN,Moves,Rating, RatingDeviation,Popularity,NbPlays,Themes,GameUrl,OpeningTags", and I don't use all of these values.
        - I only use FEN, Moves, Rating, and Popularity.
        - Moves are seperated by spaces, and the first move is the opponents move.
- create your "gamebotconfig.json" file like so:
    - Add the channel id you wan't the bot to run in
    - Add your bot's discord api token
    - Add your players with their user id's (the name you give them in the player map doesn't actually matter in the code)

``` json
    {
        "token" : "<your discord bot's api token here>",
        "channel_id" : 00000,
        "log_file": "gamebotlog.txt",
        "log_level": 10,
        "players": {
            "<player1 name>" : 000000,
            "<player2 name>" : 000000,
            "<player3 name>" : 000000,
            "<player4 name>" : 000000,
        },
        "temp_path":"temp",
        "data_path":"data",
    }
```

- And the run 'main.py'