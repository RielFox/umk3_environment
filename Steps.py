# An enumerable class which specifies the set of action steps required to perform different predefined tasks
# E.g. starting a new game, selecting Mortal Kombat difficulty, selecting character
from MAMEToolkit.umk3_environment.Actions import Actions
import random

umk3_num_total_characters = 19


def p1_start_game(frame_ratio):
    return [
        {"wait": int(180/frame_ratio), "actions": [Actions.COIN_P1]},
        {"wait": int(20/frame_ratio), "actions": [Actions.COIN_P1]},
        {"wait": int(60/frame_ratio), "actions": [Actions.P1_START]}]


def p2_start_game(frame_ratio):
    return [
        {"wait": int(180/frame_ratio), "actions": [Actions.COIN_P1]},
        {"wait": int(20/frame_ratio), "actions": [Actions.COIN_P1]},
        {"wait": int(60/frame_ratio), "actions": [Actions.P2_START]}]


def p1_and_p2_vs_start_game(frame_ratio):
    return [
        {"wait": int(180 / frame_ratio), "actions": [Actions.COIN_P1]},
        {"wait": int(60 / frame_ratio), "actions": [Actions.COIN_P1]},
        {"wait": int(180 / frame_ratio), "actions": [Actions.COIN_P1]},
        {"wait": int(60 / frame_ratio), "actions": [Actions.COIN_P1]},
        {"wait": int(60 / frame_ratio), "actions": [Actions.P1_START]},
        {"wait": int(180 / frame_ratio), "actions": [Actions.P2_START]}]


def p1_vs_continue(frame_ratio):
    return [
        {"wait": int(180 / frame_ratio), "actions": [Actions.COIN_P1]},
        {"wait": int(60 / frame_ratio), "actions": [Actions.COIN_P1]},
        {"wait": int(180 / frame_ratio), "actions": [Actions.P1_START]},
        {"wait": int(180 / frame_ratio), "actions": [Actions.P1_START]}]


def p2_vs_continue(frame_ratio):
    return [
        {"wait": int(180 / frame_ratio), "actions": [Actions.COIN_P1]},
        {"wait": int(60 / frame_ratio), "actions": [Actions.COIN_P1]},
        {"wait": int(180 / frame_ratio), "actions": [Actions.P2_START]},
        {"wait": int(180 / frame_ratio), "actions": [Actions.P2_START]}]


# Select path at 'Choose your destiny' screen
def p1_select_path(frame_ratio, path):
    if path == 'Novice':
        steps = [{"wait": int(300/frame_ratio), "actions": [Actions.P1_HPUNCH]}]
    elif path == 'Warrior':
        steps = [{"wait": int(100 / frame_ratio), "actions": [Actions.P1_RIGHT]},
                 {"wait": int(300 / frame_ratio), "actions": [Actions.P1_HPUNCH]}]
    elif path == 'Master':
        steps = [{"wait": int(100 / frame_ratio), "actions": [Actions.P1_RIGHT]},
                 {"wait": int(100 / frame_ratio), "actions": [Actions.P1_RIGHT]},
                 {"wait": int(300 / frame_ratio), "actions": [Actions.P1_HPUNCH]}]
    elif path == 'MasterII':
        steps = [{"wait": int(100 / frame_ratio), "actions": [Actions.P1_RIGHT]},
                 {"wait": int(100 / frame_ratio), "actions": [Actions.P1_RIGHT]},
                 {"wait": int(100 / frame_ratio), "actions": [Actions.P1_RIGHT]},
                 {"wait": int(300 / frame_ratio), "actions": [Actions.P1_HPUNCH]}]
    else:
        raise EnvironmentError("Invalid path setting. Available paths: 'Novice', 'Warrior', 'Master','MasterII'. \n ")

    return steps


# Select path at 'Choose your destiny' screen
def p2_select_path(frame_ratio, path):
    if path == 'Novice':
        steps = [{"wait": int(300/frame_ratio), "actions": [Actions.P2_HPUNCH]}]
    elif path == 'Warrior':
        steps = [{"wait": int(100 / frame_ratio), "actions": [Actions.P2_RIGHT]},
                 {"wait": int(300 / frame_ratio), "actions": [Actions.P2_HPUNCH]}]
    elif path == 'Master':
        steps = [{"wait": int(100 / frame_ratio), "actions": [Actions.P2_RIGHT]},
                 {"wait": int(100 / frame_ratio), "actions": [Actions.P2_RIGHT]},
                 {"wait": int(300 / frame_ratio), "actions": [Actions.P2_HPUNCH]}]
    elif path == 'MasterII':
        steps = [{"wait": int(100 / frame_ratio), "actions": [Actions.P2_RIGHT]},
                 {"wait": int(100 / frame_ratio), "actions": [Actions.P2_RIGHT]},
                 {"wait": int(100 / frame_ratio), "actions": [Actions.P2_RIGHT]},
                 {"wait": int(300 / frame_ratio), "actions": [Actions.P2_HPUNCH]}]
    else:
        raise EnvironmentError("Invalid path setting. Available paths: 'Novice', 'Warrior', 'Master','MasterII'. \n ")

    return steps


# Select character in Character Select screen
def p1_select_character(frame_ratio, character):
# character: character number, range: 0 - 18

    right1 = 0
    down = 0
    right2 = 0

    # If character number above range of selectable characters, choose a random one
    if character > umk3_num_total_characters - 1:
        character = random.randint(0, umk3_num_total_characters - 1)

    # 'Scorpion', the default character, is number 6
    if 0 <= character <= 6:
        right1 = character
        down = 0
        right2 = 0
    elif 7 <= character <= 8:
        right1 = 1
        down = 1
        right2 = character - 7
    elif 9 <= character <= 13:
        right1 = 1
        down = 2
        right2 = character - 9
    elif 14 <= character <= 18:
        right1 = 1
        down = 3
        right2 = character - 14

    # Wait for character selection screen to show
    steps = [{"wait": int(300/frame_ratio), "actions": []}]

    # Select character
    for i in range(0, right1):
        steps += [{"wait": int(20/frame_ratio), "actions": [Actions.P1_RIGHT]}]

    for k in range(0, down):
        steps += [{"wait": int(20/frame_ratio), "actions": [Actions.P1_DOWN]}]

    for l in range(0, right2):
        steps += [{"wait": int(20/frame_ratio), "actions": [Actions.P1_RIGHT]}]

    # Confirm selection
    steps += [{"wait": int(20/frame_ratio), "actions": [Actions.P1_HPUNCH]}]

    return steps, character


def p2_select_character(frame_ratio, character):
# character: character number, range:0-18

    left1 = 0
    down = 0
    left2 = 0

    # If character number above range of selectable characters, choose a random one
    if character > umk3_num_total_characters - 1:
        character = random.randint(0, umk3_num_total_characters - 1)

    # 'Scorpion', the default character, is number 6
    if 0 <= character <= 6:
        left1 = 6 - character
        down = 0
        left2 = 0
    elif character == 7:
        left1 = 1
        down = 1
        left2 = 1
    elif character == 8:
        left1 = 1
        down = 1
        left2 = 0
    elif 9 <= character <= 13:
        left1 = 1
        down = 2
        left2 = 13 - character
    elif 14 <= character <= 18:
        left1 = 1
        down = 3
        left2 = 18 - character

    # Wait for character selection screen to show
    steps = [{"wait": int(300/frame_ratio), "actions": []}]

    # Select character
    for i in range(0, left1):
        steps += [{"wait": int(20/frame_ratio), "actions": [Actions.P2_LEFT]}]

    for k in range(0, down):
        steps += [{"wait": int(20/frame_ratio), "actions": [Actions.P2_DOWN]}]

    for l in range(0, left2):
        steps += [{"wait": int(20/frame_ratio), "actions": [Actions.P2_LEFT]}]

    # Confirm selection
    steps += [{"wait": int(20/frame_ratio), "actions": [Actions.P2_HPUNCH]}]

    return steps, character


def vs_wait_for_game_over_screens(frame_ratio):
    return [{"wait": int(1200 / frame_ratio), "actions": []}]


def wait_for_game_over_screens(frame_ratio):
    return [{"wait": int(3000 / frame_ratio), "actions": []}]


def wait_for_game_reset(frame_ratio):
    return [{"wait": int(2000 / frame_ratio), "actions": []}]


def wait_for_game_completed_screens(frame_ratio):
    return [{"wait": int(1500 / frame_ratio), "actions": []}]


def set_difficulty(frame_ratio, new_difficulty, previous_difficulty):
    # If the new difficulty is the same as the previous difficulty, no difficulty changes need to be made
    if new_difficulty == previous_difficulty:
        steps = []
    else:
        # Enter Test Menu -> Game Adjustments -> Computer Difficulty
        steps = [{"wait": 0, "actions": [Actions.SERVICE]},
                 {"wait": int(20 / frame_ratio), "actions": [Actions.P1_DOWN]},
                 {"wait": int(20 / frame_ratio), "actions": [Actions.P1_DOWN]},
                 {"wait": int(20 / frame_ratio), "actions": [Actions.P1_DOWN]},
                 {"wait": int(20 / frame_ratio), "actions": [Actions.P1_LPUNCH]},
                 {"wait": int(20 / frame_ratio), "actions": [Actions.P1_DOWN]},
                 {"wait": int(20 / frame_ratio), "actions": [Actions.P1_DOWN]},
                 {"wait": int(20 / frame_ratio), "actions": [Actions.P1_DOWN]},
                 {"wait": int(20 / frame_ratio), "actions": [Actions.P1_DOWN]},
                 {"wait": int(20 / frame_ratio), "actions": [Actions.P1_DOWN]}]

        # Default difficulty is Medium (2) [0-Very Easy,1-Easy,2-Medium,3-Hard,4-Very Hard]

        # If the new difficulty is higher than previous difficulty,
        # press UP the appropriate number of times to increase the difficulty
        if new_difficulty > previous_difficulty:

            steps += [{"wait": int(20 / frame_ratio), "actions": [Actions.P1_LPUNCH]}]

            for i in range(previous_difficulty,new_difficulty):
                steps += [{"wait": int(20 / frame_ratio), "actions": [Actions.P1_UP]}]

            steps += [{"wait": int(20 / frame_ratio), "actions": [Actions.P1_LPUNCH]}]
        # If the new difficulty is lower than previous difficulty,
        # press DOWN the appropriate number of times to decrease the difficulty
        elif new_difficulty < previous_difficulty:

            steps += [{"wait": int(20 / frame_ratio), "actions": [Actions.P1_LPUNCH]}]

            for i in range(new_difficulty, previous_difficulty):
                steps += [{"wait": int(20 / frame_ratio), "actions": [Actions.P1_DOWN]}]

            steps += [{"wait": int(20 / frame_ratio), "actions": [Actions.P1_LPUNCH]}]

        # Exit the Test Menu
        steps += [{"wait": int(1000 / frame_ratio), "actions": [Actions.P1_DOWN]},
                  {"wait": int(20 / frame_ratio), "actions": [Actions.P1_LPUNCH]},
                  {"wait": int(20 / frame_ratio), "actions": [Actions.P1_DOWN]},
                  {"wait": int(20 / frame_ratio), "actions": [Actions.P1_DOWN]},
                  {"wait": int(20 / frame_ratio), "actions": [Actions.P1_DOWN]},
                  {"wait": int(20 / frame_ratio), "actions": [Actions.P1_DOWN]},
                  {"wait": int(20 / frame_ratio), "actions": [Actions.P1_DOWN]},
                  {"wait": int(20 / frame_ratio), "actions": [Actions.P1_LPUNCH]}]

    return new_difficulty, steps









