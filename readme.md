# Discord Text-Based Mini-game Bot

Several disclaimers!

- This repository was created on the fly while trying to make small text-based mini-games in discord.
- As it \was only ever intended to be run while I was there to correct any mistakes that actually cause errors, I am sure there are many more bugs still left that have not been found.
- In addition, the code, while fairly versatile, is not friendly to work with and probably requires many small edits to lots of files to implement features which should be simple, but I never though to add.
- I designed these games to work with between two and six people. Some may work with more, some may not.

So be warned.

Here are the steps to set the code up.

- Install all nessasary python libraries and files using the following commands from the inside the top directory of the project:

```console
pip install -r requirements.txt
python setup.py
```

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
