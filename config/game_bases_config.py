from config.config_tools import GameBasesConfigDict, merge_local

game_bases_config:GameBasesConfigDict = {
    'chess_base' : {
        'p_white_color': '#e9e4d4',
        'p_black_color': '#98623c',
        'p_white_hollow': False,
        'p_black_hollow': False,
        'b_white_color': 'beige',
        'b_black_color': '#c19a6b',
        'image_size': 1000,
        'border_width': 75,
        'back_grnd_color': '#4a3728',
        'text_color': 'lightgrey',
        'p_size': 1,
        'p_font': "data/fonts/chess_merida_unicode.ttf",
        't_size': 0.75,
        't_font': None,
        'white_perspective': True,
        'p_white_outline': 2,
        'p_black_outline': 2,
        'p_white_outline_color': 'black',
        'p_black_outline_color': 'black',
        'last_move_color': '#eedc00d0',
        'check_color': '#ff000066'
    }
}

merge_local('game_bases_config',game_bases_config)#type: ignore