from MAMEToolkit.umk3_environment.Actions import Actions

# An enumerable class which specifies the set of action steps required to perform different predefined tasks
# E.g. starting a new game, selecting Mortal Kombat difficulty, selecting character


def p1_start_game(frame_ratio):
    return [
        {"wait": int(180/frame_ratio), "actions": [Actions.COIN_P1]},
        {"wait": int(20/frame_ratio), "actions": [Actions.COIN_P1]},
        {"wait": int(60/frame_ratio), "actions": [Actions.P1_START]}]


def p1_select_path(frame_ratio,path):
    if path == 'Novice':
        steps = [{"wait": int(300/frame_ratio), "actions": [Actions.P1_HPUNCH]}]

    return steps


def p1_select_character(frame_ratio,character):

    if character == 'Scorpion':
        right = 6
        down = 0
    else:
        right = 2
        down = 0

    #Wait for character selection screen to show
    steps = [{"wait": int(300/frame_ratio), "actions": []}]

    #Select character
    for i in range(0,right):
        steps += [{"wait": int(20/frame_ratio), "actions": [Actions.P1_RIGHT]}]

    for k in range(0,down):
        steps += [{"wait": int(20/frame_ratio), "actions": [Actions.P1_DOWN]}]

    #Confirm selection
    steps += [{"wait": int(20 / frame_ratio), "actions": [Actions.P1_HPUNCH]}]

    return steps


def wait_for_game_over_screens(frame_ratio):
    return [{"wait": int(10*30), "actions": []}]


