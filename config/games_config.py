from config.config_tools import GamesConfigDict, merge_local

games_config:GamesConfigDict = {
    "chess_puzzle_elimination": {
        'data_path':"lichess_db_puzzle.csv",
        'rating_range':(400,800),
        'popularity_range':None,
        'num_to_sample':500,
        'num_move_options':5,
        'puzzle_rating_cap_escalation':200
    },
    "altered_image_guess" : {
        "num_rounds" : 10,
        "min_image_size" : (300,300),
        "num_choices" : 8,
        "zoom_crop_box_size" : (30,30),
        "zoom_crop_box_display_size": (400,400),
        "zoom_crop_no_edge_portion" : 0.2,
        "blur_radius" : 50,
        "removal_color" : (0,0,0,0),
        "removal_keep_portion" : 0.05,
        "bad_conversion_resize" : 0.5,
        "polka_dot_size_scalar" : (0.06,0.1),
        "pixels_in_image_per_polka_dot" : 5000,
        "pattern_radial_portion_visable": 0.2,
        "pattern_radial_num_rays" : 100,
        "scribble_num_lines" : 40,
        "scribble_points_per_line" : 10,
        "scribble_width" : 20,
        "tile_ratio" : 0.03,
        "num_colors_to_sample" : 16,
        "polygons_border_size_range" : (0.05,0.2),
        "polygons_cover_portion" : 0.8,
        "swirl_side_exclusion_ratio" : 0.25,
        "swirl_rotation_scale" : 2,
        "swirl_rotation_offset" : 0.5

    },
    "container_bidding" : {
        'num_containers' : 5,
        'data_path':"container_contents.json",
        'starting_money':100,
        'percentile_var':10,
        'end_of_game_interest':20
    },
    "elimination_blackjack" : {
        'hand_limit' : 21,
        'num_players_per_deck' : 7
    },
    "elimination_letter_adder" : {
        'num_letters' : 4,
        'start_letters' : 4
    },
    "elimination_rock_paper_scissors" : {},
    "elimination_trivia": {},
    "emoji_communications": {
        'num_rounds': 1,
        'num_options' : 5,
        'points_for_guess': 2,
        "points_per_guesser":1,
        "points_for_all_guess":1,
        "bonus_num":3,
        "bonus_points_per_guesser":2,
        "max_emoji":10,
        'swap_range':(2,3),
        'give_avoid_options':True
    },
    "guess_the_word" : {
        'num_rounds' : 3,
        'min_word_len' : 6,
        'max_word_len' : 12,
        'num_definitions' : 3,
        'guess_feedback' : True,
        'length_hint' : True
    },
    "longest_word" : {
        'num_letters' : 10,
        'number_of_rounds' : 3,
        'num_letters_can_refresh' : 5
    },
    "prediction_texas_holdem" : {
        'num_rounds' : 3,
        'player_cards' : 2,
        'shared_cards' : 5
    },
    "the_great_kitten_race" : {
        'data_path' : "kitten_race_obstacles.json",
        'num_obstacles' : 5
    },
    "tricky_trivia": {
        'points_fool':1,
        'points_guess':3,
        'num_questions':3
    }
}

merge_local('games_config',games_config)#type: ignore
