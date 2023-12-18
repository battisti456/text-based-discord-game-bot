This repository was created on the fly while trying to make small text-based minigames in discord.
As it was only ever intended to be run while I was there to correct any mistakes that actually cause errors, I am sure there are many more bugs still left that have not been found.
In addition, the code, while fairly versatile, is not friendly to work with and probably requires many small edits to lots of files to implement features which should be simple, but I never though to add. 
So be warned.

To begin using it:
- install all nessasary python libraries
    - 'fogleman_TWL06_scrabble' is not an available library, but is merely the twl.py file from "https://github.com/fogleman/TWL06" by Michael fogleman
- download missing data resources
    - I have excluded 'data/lichess_db_puzzle.csv' from this repository as it is rather large. I found it at "https://database.lichess.org/#puzzles". It could, in theory, be replaced by any csv with chess puzzles. The format is "PuzzleId,FEN,Moves,Rating,RatingDeviation,Popularity,NbPlays,Themes,GameUrl,OpeningTags", and I don't use all of these values. I only use FEN, Moves, Rating, and Popularity. Moves are seperated by spaces, and the first move is the opponents move.
- create your "gamebotconfig.json" file like so:

'''json
{
    "token" : "<your discord bot's api token here>",
    "channel_id" : <the channel id your game will run in>,
    "log_file": "gamebotlog.txt",
    "log_level":10,
    "players": {
        "<player1 name>" : <player1's id>,
        "<player2 name>" : <player2's id>,
        "<player3 name>" : <player3's id>,
        "<player4 name>" : <player4's id>,
    },
    "temp_path":"temp",
    "data_path":"data",
}
'''