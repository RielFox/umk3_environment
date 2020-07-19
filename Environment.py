from MAMEToolkit.emulator.Emulator import Emulator
from MAMEToolkit.emulator.Address import Address
from MAMEToolkit.umk3_environment.Steps import *
from MAMEToolkit.umk3_environment.Actions import Actions
import numpy as np
import os


# Returns the list of memory addresses required to train on Ultimate Mortal Kombat 3 v2.2 (umk3)
def setup_memory_addresses():
    return {
        # Health values range from 0xA6 (decimal 166) to 0x00 during normal gameplay
        "healthP1": Address('0x01060A60', 's16'),
        "healthP2": Address('0x01061610', 's16'),
        # Stamina values for performing combos range from 0x30 to 0x00 during normal gameplay
        "turboP1": Address('0x01060A70', 's16'),
        "turboP2": Address('0x01061620', 's16'),
        # Consecutive round wins for each player, 2 round wins needed to win a stage
        "total_round_winsP1": Address('0x01062310', 'u8'),
        "total_round_winsP2": Address('0x01062320', 'u8'),
        # Round wins for each player for the current stage, 2 round wins needed to win a stage
        "current_round_winsP1": Address('0x01060A90', 'u8'),
        "current_round_winsP2": Address('0x01061640', 'u8'),
        # Time remaining ranges from decimal 99 to 00 during normal gameplay under the default settings
        "time_remaining_tens_digit": Address('0x0105F330', 'u8'),
        "time_remaining_ones_digit": Address('0x0105F340', 'u8'),
        # A flag value used for rendering some of the background of a stage during a fight
        # It is 1 during a stage, becomes 0 in between stages but remains 1 in-between rounds
        "fighting": Address('0x0105F350', 'u8')
    }


# Converts int index (action) into the relevant movement action Enum for Player 1
def p1_index_to_move_action(action):
    return {
        0: [],
        1: [Actions.P1_LEFT],
        2: [Actions.P1_LEFT, Actions.P1_UP],
        3: [Actions.P1_UP],
        4: [Actions.P1_UP, Actions.P1_RIGHT],
        5: [Actions.P1_RIGHT],
        6: [Actions.P1_RIGHT, Actions.P1_DOWN],
        7: [Actions.P1_DOWN],
        8: [Actions.P1_DOWN, Actions.P1_LEFT]
    }[action]


# Converts int index (action) into the relevant attack action Enum for Player 1
def p1_index_to_attack_action(action):
    return {
        0: [],
        1: [Actions.P1_HPUNCH],
        2: [Actions.P1_LPUNCH],
        3: [Actions.P1_HKICK],
        4: [Actions.P1_LKICK],
        5: [Actions.P1_BLOCK],
        6: [Actions.P1_RUN]
    }[action]


# Converts int index (action) into the relevant movement action Enum for Player 1
def p2_index_to_move_action(action):
    return {
        0: [],
        1: [Actions.P2_LEFT],
        2: [Actions.P2_LEFT, Actions.P2_UP],
        3: [Actions.P2_UP],
        4: [Actions.P2_UP, Actions.P2_RIGHT],
        5: [Actions.P2_RIGHT],
        6: [Actions.P2_RIGHT, Actions.P2_DOWN],
        7: [Actions.P2_DOWN],
        8: [Actions.P2_DOWN, Actions.P2_LEFT]
    }[action]


# Converts int index (action) into the relevant attack action Enum for Player 1
def p2_index_to_attack_action(action):
    return {
        0: [],
        1: [Actions.P2_HPUNCH],
        2: [Actions.P2_LPUNCH],
        3: [Actions.P2_HKICK],
        4: [Actions.P2_LKICK],
        5: [Actions.P2_BLOCK],
        6: [Actions.P2_RUN]
    }[action]


# Combines the data of multiple time steps
def add_rewards(old_data, new_data):
    for k in old_data.keys():
        if "rewards" in k:
            for player in old_data[k]:
                new_data[k][player] += old_data[k][player]
    return new_data


class Player(object):

    def __init__(self, player, character_selection, total_characters):

        self.total_characters = total_characters
        # A list of the names of all UMK3 vanilla selectable characters in order
        self.umk3_character_list = ['Kitana', 'Reptile', 'SonyaBlade', 'JaxBriggs', 'Nightwolf', 'Jade', 'Scorpion',
                                    'Kano', 'SubZero', 'Sektor', 'Sindel', 'Stryker', 'Cyrax', 'KungLao', 'Kabal',
                                    'Sheeva', 'ShangTsung', 'LiuKang', 'Smoke']
        # Initialize if playing as 'P1' or 'P2'
        self.player = player
        # Initialize character index and name
        self.character_index = character_selection
        if 0 <= self.character_index < self.total_characters:
            self.character_name = self.umk3_character_list[self.character_index]
            self.one_hot_character_selection = np.eye(self.total_characters)[self.character_index]
        else:
            self.character_name = 'Unknown'
            self.one_hot_character_selection = np.zeros(self.total_characters)

        # Initialize useful values for the environment to keep track the state of each player
        self.expected_health = 0
        self.expected_wins = 0
        self.expected_wins_check_done = 0
        self.total_rewards_this_round = 0
        self.total_rewards_this_game = 0

    def set_character(self, character_selection):
        self.character_index = character_selection
        if 0 <= self.character_index < self.total_characters:
            self.character_name = self.umk3_character_list[self.character_index]
            self.one_hot_character_selection = np.eye(self.total_characters)[self.character_index]
        else:
            self.character_name = 'Unknown'
            self.one_hot_character_selection = np.zeros(self.total_characters)


# The Ultimate Mortal Kombat 3 interface for training an agent against the game
class Environment(object):

    def __init__(self, env_id, roms_path, self_play=True, vs_rounds_before_single_player=2, player='P1', character = 19, 
                 frame_ratio=2, frames_per_step=1, render=True, throttle=False, debug=True, new_training=True):

        self.p1_character_selection = character  # 'Scorpion' (default) is 6 #19 and over for random character
        self.p2_character_selection = character

        # This will need Xvfb X11 virtual server installed on GNU/Linux system
        if not render:
            os.system("Xvfb :1 -screen 0 800x600x16 +extension RANDR &")
            os.environ["DISPLAY"] = ":1"

        self.env_id = env_id
        self.self_play = self_play
        self.frame_ratio = frame_ratio
        self.frames_per_step = frames_per_step
        self.throttle = throttle
        self.debug = debug
        self.emu = Emulator(env_id, roms_path, "umk3", setup_memory_addresses(), frame_ratio=frame_ratio, render=render,
                            throttle=throttle, debug=debug)
        self.started = False

        self.expected_time_remaining = 0
        self.time_remaining = 0
        self.done = False
        self.round_done = False
        self.stage_done = False
        self.game_over = False
        self.game_completed = False
        self.finished_single_player = False
        self.num_total_characters = umk3_num_total_characters

        # Create two Player objects with useful values for each player (a player can be an agent or the game's AI)
        self.P1 = Player('P1', self.p1_character_selection, self.num_total_characters)
        self.P2 = Player('P2', self.p2_character_selection, self.num_total_characters)
        self.env_player = player  # If environment's agent controls 'P1', 'P2' or both in 2 Player self-play 'Vs'

        # Player is initialized to 'Vs' if self_play is True
        if self.self_play is True:
            self.env_player = 'Vs'

        # Number of self-play Vs rounds to be played before the agent plays a single player benchmark in story mode
        self.vs_rounds_before_single_player = vs_rounds_before_single_player
        self.current_vs_rounds_before_single_player = vs_rounds_before_single_player

        # Stage is counting only if playing in single-player mode
        # If 'Vs' mode, Stage remains at 0
        self.stage = 0 if player is 'Vs' else 1

        self.last_vs_game_winner = ''
        self.highest_stage = 0
        self.path = 'Novice'
        self.difficulty = 0
        self.expected_difficulty = 0  # Assumes UMK3 starts with Very Easy pre-selected

        self.paths = ['Novice', 'Warrior', 'Master', 'MasterII']
        self.difficulties = ['Very Easy', 'Easy', 'Medium', 'Hard', 'Very Hard']

        # If the game somehow reaches round 5 in a stage (3 draws), it resets after round 5 ends
        self.round_this_stage = 1
        self.reset_this_round = False

        self.total_episodes_played = 0
        self.memory_values = []

        # Track if any milsetones have been logged to decide if to create a new file or append
        self.new_training = new_training

        if not self.new_training and os.path.exists(os.path.join('milestones', self.env_id + '_milestones.txt')):
            self.logged_first_milestone = True
        else:
            self.logged_first_milestone = False

    # Runs a set of action steps over a series of time steps
    # Used for transitioning the emulator through non-learnable gameplay, aka. title screens, character selects
    def run_steps(self, steps):
        for step in steps:
            for i in range(step["wait"]):
                self.emu.step([])
            self.emu.step([action.value for action in step["actions"]])

    def new_game(self):

        assert (self.env_player is 'P1' or self.env_player is 'P2' or self.env_player is 'Vs')

        self.expected_difficulty, difficulty_steps = set_difficulty(self.frame_ratio, self.difficulty,
                                                                    self.expected_difficulty)
        self.run_steps(difficulty_steps)

        # If player is P1, execute steps to start story-mode with Player 1
        if self.env_player is 'P1':
            # Select single-player character, only if environment is not in self-play mode
            # If environment is in self-play, character is pre-selected as the one chosen by the player
            # who won the last Vs game
            if not self.self_play:
                self.run_steps(p1_start_game(self.frame_ratio))
                p1_character_select_steps, p1_character_index = \
                    p1_select_character(self.frame_ratio, self.p1_character_selection)
                self.P1.set_character(p1_character_index)
                if self.debug:
                    print(">Debug: Starting a new single-player game... Difficulty: " +
                          self.difficulties[self.difficulty] + ", Path: " + self.path +
                          ", Player: " + self.env_player + ", Character: " + self.P1.character_name + " \n")
                self.run_steps(p1_character_select_steps)
            else:
                if self.debug:
                    print(">Debug: Continuing to single-player game from Vs... Difficulty: " +
                          self.difficulties[self.difficulty] + ", Path: " + self.path + ", Player: " +
                          self.env_player + ", Character: " + self.P1.character_name + " \n")
            # Select story mode path
            self.run_steps(p1_select_path(self.frame_ratio, self.path))
        # If player is P2, execute steps to start story-mode with Player 2
        elif self.env_player is 'P2':
            # Select single-player character, only if environment is not in self-play mode
            # If environment is in self-play, character is pre-selected as the one chosen by the player
            # who won the last Vs game
            if not self.self_play:
                self.run_steps(p2_start_game(self.frame_ratio))
                p2_character_select_steps, p2_character_index = \
                    p2_select_character(self.frame_ratio, self.p2_character_selection)
                self.P2.set_character(p2_character_index)
                if self.debug:
                    print(">Debug: Starting a new single-player game... Difficulty: " +
                          self.difficulties[self.difficulty] + ", Path: " + self.path +
                          ", Player: " + self.env_player + ", Character: " + self.P2.character_name + " \n")
                self.run_steps(p2_character_select_steps)
            else:
                if self.debug:
                    print(">Debug: Continuing to single-player game from Vs... Difficulty: " +
                          self.difficulties[self.difficulty] + ", Path: " + self.path +
                          ", Player: " + self.env_player + ", Character: " + self.P2.character_name + " \n")
            # Select story mode path
            self.run_steps(p2_select_path(self.frame_ratio, self.path))
        # If player is set to Vs (in Self-Play mode), execute steps to start 2-Player Vs mode
        else:
            self.run_steps(p1_and_p2_vs_start_game(self.frame_ratio))
            p1_character_select_steps, p1_character_index = p1_select_character(
                self.frame_ratio, self.p1_character_selection)
            self.P1.set_character(p1_character_index)
            p2_character_select_steps, p2_character_index = p2_select_character(
                self.frame_ratio, self.p2_character_selection)
            self.P2.set_character(p2_character_index)
            if self.debug:
                print(">Debug: Starting a new Vs game... Mode: " + self.env_player + ", P1 Character: " +
                      self.P1.character_name + ", P2 Character: " + self.P2.character_name + " \n")
            self.run_steps(p1_character_select_steps)
            self.run_steps(p2_character_select_steps)

        self.wait_for_fight_start()

        self.P1.expected_health, self.P2.expected_health = 0, 0
        #self.expected_health = {"P1": 0, "P2": 0}
        self.P1.expected_wins, self.P2.expected_wins = 0, 0
        #self.expected_wins = {"P1": 0, "P2": 0}
        self.P1.expected_wins_check_done, self.P2.expected_wins_check_done = 0, 0
        #self.expected_wins_check_done = {"P1": 0, "P2": 0}
        self.done = False
        self.round_done = False
        self.stage_done = False
        self.game_over = False
        self.game_completed = False
        self.started = True
        self.expected_time_remaining = 0
        self.time_remaining = 0
        self.round_this_stage = 1
        self.P1.total_rewards_this_round, self.P2.total_rewards_this_round = 0, 0
        #self.total_rewards_this_round = {"P1": 0, "P2": 0}
        self.P1.total_rewards_this_game, self.P2.total_rewards_this_game = 0, 0
        #self.total_rewards_this_game = 0
        self.finished_single_player = False
        self.reset_this_round = False
        # Stage is counting only if playing in single-player mode
        # If 'Vs' mode, Stage remains at 0
        self.stage = 0 if self.env_player is 'Vs' else 1

    # Must be called first after creating this class
    # Sends actions to the game until the learnable gameplay starts
    def start(self):
        if self.throttle:
            for i in range(int(250 / self.frame_ratio)):
                self.emu.step([])
        self.new_game()

    def wait_for_fight_start(self):
        data = self.emu.step([])
        while data["fighting"] == 0:
            data = self.emu.step([])

    def next_stage(self):
        self.P1.expected_health, self.P2.expected_health = 0, 0
        #self.expected_health = {"P1": 0, "P2": 0}
        self.P1.expected_wins, self.P2.expected_wins = 0, 0
        #self.expected_wins = {"P1": 0, "P2": 0}
        self.P1.expected_wins_check_done, self.P2.expected_wins_check_done = 0, 0
        #self.expected_wins_check_done = {"P1": 0, "P2": 0}
        self.round_this_stage = 1
        self.done = False
        self.round_done = False
        self.stage_done = False
        return self.wait_for_next_stage_start()

    def wait_for_next_stage_start(self):
        if self.debug:
            print(">Debug: Waiting for next stage to start...\n")
        data = self.emu.step([])
        while data["fighting"] == 1:
            data = self.emu.step([])
        while data["fighting"] == 0:
            data = self.emu.step([])

    def next_round(self):
        self.round_this_stage += 1
        self.reset_this_round = True if self.round_this_stage > 4 else False
        if self.reset_this_round and self.debug:
            print(">Debug: Game has reached round 5 in a stage, will reset at end of this round!")
        self.done = False
        self.round_done = False
        self.P1.expected_health, self.P2.expected_health = 0, 0
        #self.expected_health = {"P1": 0, "P2": 0}

        return self.wait_for_next_round_start()

    def wait_for_next_round_start(self):
        if self.debug:
            print(">Debug: Waiting for next round to start...\n")
        data = self.emu.step([])
        self.time_remaining = (int(data["time_remaining_tens_digit"]) * 10) + int(data["time_remaining_ones_digit"])
        while int(data["healthP1"]) != 166 and int(data["healthP2"]) != 166 and self.time_remaining != 99:
            data = self.emu.step([])
            self.time_remaining = (int(data["time_remaining_tens_digit"]) * 10) + int(data["time_remaining_ones_digit"])

    def new_game_after_loss(self):
        if self.debug:
            print(">Debug: Waiting for game over screens...\n")
        self.run_steps(wait_for_game_over_screens(self.frame_ratio))
        self.new_game()

    def new_game_after_completion(self):
        if self.debug:
            print(">Debug: Waiting for game completed screens...\n")
        self.run_steps(wait_for_game_completed_screens(self.frame_ratio))
        self.new_game()

    # Steps the emulator along by the requested amount of frames required for the agent to provide actions
    # For single-player
    def step(self, move_action, attack_action):
        assert (self.env_player is 'P1' or self.env_player is 'P2')
        if self.started:
            if not self.round_done and not self.stage_done and not self.game_over and not self.game_completed:
                actions = []
                if self.env_player is 'P1':
                    actions += p1_index_to_move_action(move_action)
                    actions += p1_index_to_attack_action(attack_action)
                elif self.env_player is 'P2':
                    actions += p2_index_to_move_action(move_action)
                    actions += p2_index_to_attack_action(attack_action)
                data = self.gather_frames(actions)
                data = self.check_done(data)
                '''
                if self.debug:
                    print(">Debug: healthP1:" + str(data["healthP1"]) + " healthP2:" + str(data["healthP2"]) + " \n")
                    print(">Debug: turboP1: " + str(data["turboP1"]) + " turboP2: " + str(data["turboP2"]) + " \n")
                    print(">Debug: time_remaining_tens_digit: " + str(
                        data["time_remaining_tens_digit"]) + " time_remaining_ones_digit: " + str(
                        data["time_remaining_ones_digit"]) + " \n")
                    print(">Debug: winsP1: " + str(data["current_round_winsP1"]) + " winsP2: " + str(
                        data["current_round_winsP2"]) + " \n")
                    print(">Debug: fighting:" + str(data["fighting"]) + " \n")
                    '''
                return data["frame"], data[
                    "rewards"], self.done, self.round_done, self.stage_done, self.game_over, self.game_completed
            else:
                raise EnvironmentError("Attempted to step while characters are not fighting")
        else:
            raise EnvironmentError("Start must be called before stepping")

    # Steps the emulator along by the requested amount of frames required for the agent to provide actions
    # For two-player self-play
    def vs_step(self, p1_move_action, p1_attack_action, p2_move_action, p2_attack_action):
        assert (self.env_player is 'Vs')
        if self.started:
            if not self.round_done and not self.stage_done and not self.game_over and not self.game_completed:
                actions = []
                actions += p1_index_to_move_action(p1_move_action)
                actions += p1_index_to_attack_action(p1_attack_action)
                actions += p2_index_to_move_action(p2_move_action)
                actions += p2_index_to_attack_action(p2_attack_action)
                data = self.gather_frames(actions)
                data = self.check_done(data)
                '''
                if self.debug:
                    print(">Debug: healthP1:" + str(data["healthP1"]) + " healthP2:" + str(data["healthP2"]) + " \n")
                    print(">Debug: turboP1: " + str(data["turboP1"]) + " turboP2: " + str(data["turboP2"]) + " \n")
                    print(">Debug: time_remaining_tens_digit: " + str(
                        data["time_remaining_tens_digit"]) + " time_remaining_ones_digit: " + str(
                        data["time_remaining_ones_digit"]) + " \n")
                    print(">Debug: winsP1: " + str(data["current_round_winsP1"]) + " winsP2: " + str(
                        data["current_round_winsP2"]) + " \n")
                    print(">Debug: fighting:" + str(data["fighting"]) + " \n")
                '''
                return data["frame"], data[
                    "rewards"], self.done, self.round_done, self.stage_done, self.game_over, self.game_completed
            else:
                raise EnvironmentError("Attempted to step while characters are not fighting")
        else:
            raise EnvironmentError("Start must be called before stepping")

    # Collects the specified amount of frames the agent requires before choosing an action
    def gather_frames(self, actions):
        data = self.sub_step(actions)
        frames = [data["frame"]]
        for i in range(self.frames_per_step - 1):
            data = add_rewards(data, self.sub_step(actions))
            frames.append(data["frame"])
        data["frame"] = frames[0] if self.frames_per_step == 1 else frames
        return data

    # Steps the emulator along by one time step and feeds in any actions that require pressing
    # Takes the data returned from the step and updates book keeping variables while returning rewards
    def sub_step(self, actions):
        data = self.emu.step([action.value for action in actions])
        self.memory_values = data

        p1_diff_reward = (self.P1.expected_health - data["healthP1"])
        p2_diff_reward = (self.P2.expected_health - data["healthP2"])
        #p1_diff_reward = (self.expected_health["P1"] - data["healthP1"])
        #p2_diff_reward = (self.expected_health["P2"] - data["healthP2"])

        self.P1.expected_health, self.P2.expected_health = data["healthP1"], data["healthP2"]
        #self.expected_health = {"P1": data["healthP1"], "P2": data["healthP2"]}

        if data["current_round_winsP1"] == self.P1.expected_wins + 1:
        #if data["current_round_winsP1"] == self.expected_wins["P1"] + 1:
            p1_round_win_reward = 200
            p2_round_win_reward = -200
        elif data["current_round_winsP2"] == self.P2.expected_wins + 1:
        #elif data["current_round_winsP2"] == self.expected_wins["P2"] + 1:
            p2_round_win_reward = 200
            p1_round_win_reward = -200
        else:
            p1_round_win_reward = 0
            p2_round_win_reward = 0

        self.P1.expected_wins, self.P2.expected_wins = data["current_round_winsP1"], data["current_round_winsP2"]
        #self.expected_wins["P1"] = data["current_round_winsP1"]
        #self.expected_wins["P2"] = data["current_round_winsP2"]

        self.time_remaining = (int(data["time_remaining_tens_digit"]) * 10) + int(data["time_remaining_ones_digit"])

        if self.time_remaining == self.expected_time_remaining - 1:

            if data["healthP1"] < data["healthP2"]:
                p1_time_remaining_reward = -1
                p2_time_remaining_reward = 1

            elif data["healthP1"] > data["healthP2"]:
                p1_time_remaining_reward = 1
                p2_time_remaining_reward = -1
            else:
                p1_time_remaining_reward = 0
                p2_time_remaining_reward = 0
        else:
            p1_time_remaining_reward = 0
            p2_time_remaining_reward = 0

        self.expected_time_remaining = self.time_remaining

        # Return the total rewards of each player for this timestep in a rewards dictionary
        # Rewards range roughly from +360 to -360, thus normalizing by dividing by 360
        # Also round rewards to 5 decimal places
        rewards = {
            "P1": round(((p2_diff_reward - p1_diff_reward) + p1_time_remaining_reward + p1_round_win_reward) / 360, 5),
            "P2": round(((p1_diff_reward - p2_diff_reward) + p2_time_remaining_reward + p2_round_win_reward) / 360, 5)
        }

        # Update total rewards for this round and this game
        self.P1.total_rewards_this_round += rewards['P1']
        self.P2.total_rewards_this_round += rewards['P2']
        self.P1.total_rewards_this_game += rewards['P1']
        self.P2.total_rewards_this_game += rewards['P2']
        #self.total_rewards_this_round['P1'] += rewards['P1']
        #self.total_rewards_this_round['P2'] += rewards['P2']
        '''
        if self.debug:
            print(">Debug: Rewards for P1 this timestep: " + str(rewards["P1"]) + "\n")
            print(">Debug: Rewards for P2 this timestep: " + str(rewards["P2"]) + "\n")
        '''
        data["rewards"] = rewards
        return data

    def on_round_done(self):
        if self.debug:
            print(">Debug: Round " + str(self.round_this_stage) + " done!")
            print(">Debug: Total rewards for P1 ths round: " + str(self.P1.total_rewards_this_round))
            print(">Debug: Total rewards for P2 ths round: " + str(self.P2.total_rewards_this_round) + ' \n')
            #print(">Debug: Total rewards for P1 ths round: " + str(self.total_rewards_this_round['P1']) + ' \n')
            #print(">Debug: Total rewards for P2 ths round: " + str(self.total_rewards_this_round['P2']) + ' \n')
        # Set that the round is done
        self.done = True
        # Increment the episodes played
        self.total_episodes_played += 1
        # Reset the round's rewards
        self.P1.total_rewards_this_round, self.P2.total_rewards_this_round = 0, 0
        #self.total_rewards_this_round = {"P1": 0, "P2": 0}
        # Keep up with game reset if it has reached round 5 in a stage
        if self.reset_this_round:
            if self.debug:
                print(">Debug: Game is being reset as it has reached round 5 in a stage! \n")
            self.reset_this_round = False
            self.run_steps(wait_for_game_reset(self.frame_ratio))
            self.new_game()

    def on_single_player_stage_win(self):
        # Log milestone if a new highest stage has been reached
        if self.stage > self.highest_stage:
            self.log_stage_milestone()
            self.highest_stage = self.stage
        # Check if it reached the final stage of a path
        if self.path is 'Novice' and self.stage == 8 or \
                self.path is 'Warrior' and self.stage == 9 or \
                self.path is 'Master' and self.stage == 10 or \
                self.path is 'MasterII' and self.stage == 11:
            # Set the game completed flag to true
            self.game_completed = True
            self.finished_single_player = True
            # Log a game completion milestone
            self.log_milestone()
            if self.debug:
                print(">Debug: Game completed on  " + str(self.path) + " path and on "
                      + str(self.difficulties[self.difficulty]) + " difficulty!")
                if self.env_player is 'P1':
                    print(">Debug: Total rewards for " + self.env_player + " this game: " +
                          str(self.P1.total_rewards_this_game) + "\n")
                else:
                    print(">Debug: Total rewards for " + self.env_player + " this game: " +
                          str(self.P2.total_rewards_this_game) + "\n")
            # If the game mode is set to self-play, set the env_player to Vs to start a Vs game next
            if self.self_play:
                self.env_player = 'Vs'
            # If the game has been completed, play on a harder path if there is a harder path
            if self.path is not 'MasterII':
                path_index = self.paths.index(self.path)
                path_index += 1
                self.path = self.paths[path_index]
            # Else, if the Very Hard difficulty hasn't been reached,
            # increase the difficulty and reset the path back to 'Novice'
            elif self.difficulty < 4:
                self.difficulty += 1
                self.path = 'Novice'
        # Else advance to the next stage
        else:
            self.stage_done = True
            self.stage += 1
            if self.debug:
                print(">Debug: Stage won. Advancing to stage " + str(self.stage) + ". \n")

    def on_single_player_stage_loss(self):
        self.game_over = True
        self.finished_single_player = True
        if self.debug:
            if self.env_player is 'P1':
                print(">Debug: Total rewards for " + self.env_player + " this game: " +
                      str(self.P1.total_rewards_this_game))
            else:
                print(">Debug: Total rewards for " + self.env_player + " this game: " +
                      str(self.P2.total_rewards_this_game))
            print(">Debug: Stage lost. Quiting game. \n")
        # If the game mode is set to self-play, set the env_player to Vs to start a Vs game next
        if self.self_play:
            self.env_player = 'Vs'

    def on_single_player_round_win(self):
        self.round_done = True
        if self.debug:
            print(">Debug: Round won. Advancing to next round. \n")

    def on_single_player_round_loss(self):
        self.round_done = True
        if self.debug:
            print(">Debug: Round lost. Advancing to next round. \n")

    def vs_continue(self, last_game_winner):
        if self.debug:
            print(">Debug: Advancing to next Vs game. \n")

        if last_game_winner is 'P1':
            self.run_steps(p2_vs_continue(self.frame_ratio))
        elif last_game_winner is 'P2':
            self.run_steps(p1_vs_continue(self.frame_ratio))
        else:
            raise EnvironmentError("Attempted to continue to new Vs game without a valid last game's winner")

        p1_character_select_steps, p1_character_index = p1_select_character(
            self.frame_ratio, self.p1_character_selection)
        self.P1.set_character(p1_character_index)
        #self.p1_character_name = self.umk3_character_list[self.p1_character]
        p2_character_select_steps, p2_character_index = p2_select_character(
            self.frame_ratio, self.p2_character_selection)
        self.P2.set_character(p2_character_index)
        #self.p2_character_name = self.umk3_character_list[self.p2_character]
        self.run_steps(p1_character_select_steps)
        self.run_steps(p2_character_select_steps)

        self.wait_for_fight_start()
        self.P1.expected_health, self.P2.expected_health = 0, 0
        self.P1.expected_wins, self.P2.expected_wins = 0, 0
        self.P1.expected_wins_check_done, self.P2.expected_wins_check_done = 0, 0
        #self.expected_health = {"P1": 0, "P2": 0}
        #self.expected_wins = {"P1": 0, "P2": 0}
        #self.expected_wins_check_done = {"P1": 0, "P2": 0}
        self.done = False
        self.game_over = False
        self.started = True
        self.reset_this_round = False
        self.round_this_stage = 1
        self.expected_time_remaining = 0
        self.time_remaining = 0
        self.P1.total_rewards_this_round, self.P2.total_rewards_this_round = 0, 0
        self.P1.total_rewards_this_game, self.P2.total_rewards_this_game = 0, 0
        #self.total_rewards_this_round = {"P1": 0, "P2": 0}
        #self.total_rewards_this_game = 0
        self.stage = 0

    def single_player_after_vs(self):
        if self.debug:
            print(">Debug: Waiting for game over screen...\n")
        self.run_steps(vs_wait_for_game_over_screens(self.frame_ratio))
        self.new_game()

    def vs_after_single_player(self):
        self.current_vs_rounds_before_single_player = self.vs_rounds_before_single_player
        self.new_game_after_loss()

    def on_vs_stage_done(self, last_game_winner):
        # Set the game over flag to True
        self.game_over = True
        # Deduct 1 from the number of Vs games before benchmarking in single player
        self.current_vs_rounds_before_single_player -= 1
        # Set the last Vs stage's winner
        self.last_vs_game_winner = last_game_winner
        # Output total rewards for this stage
        if self.debug:
            print(">Debug: Total rewards for P1 this game: " +
                  str(self.P1.total_rewards_this_game))
            print(">Debug: Total rewards for P2 this game: " +
                  str(self.P2.total_rewards_this_game))
        # If more Vs games remain to be played, continue with Vs game
        if self.current_vs_rounds_before_single_player > 0:
            if self.debug:
                print(">Debug: Vs stage done. " + str(self.current_vs_rounds_before_single_player) +
                      " Vs stage(s) remaining. \n")
        # Else, continue to single player benchmarking with the winner of the last Vs game
        else:
            self.env_player = last_game_winner
            if self.debug:
                print(">Debug: Vs stages done. Continuing to story with last Vs stage's winner: " + self.env_player)

    def on_vs_round_done(self):
        self.round_done = True
        if self.debug:
            print(">Debug: Vs round done. Advancing to next round. \n")

    # Checks whether the round or game has finished
    def check_done(self, data):

        # Get the time currently remaining from the two memory locations holding each of the two digits (from 99 to 00)
        self.time_remaining = int(data["time_remaining_tens_digit"]) * 10 + int(data["time_remaining_ones_digit"])

        # If a round has ended
        if data["current_round_winsP1"] == self.P1.expected_wins_check_done + 1 \
                or data["current_round_winsP2"] == self.P2.expected_wins_check_done + 1 \
                or (data["healthP1"] == 0 and data["healthP2"] == 0) \
                or (data["healthP1"] == data["healthP2"] and self.time_remaining == 0):
            # (data["healthP1"] == 0 and data["healthP2"] == 0) or self.time_remaining == 0
            # self.time_remaining == 0 check may trigger a bug
            self.on_round_done()

        if self.done:
            # If the round wins of P1 have incremented, P1 has won a round!
            if data["current_round_winsP1"] == self.P1.expected_wins_check_done + 1:
                if self.debug:
                    print(">Debug: Game End Condition Met -> P1 wins have incremented in game's memory.")
                    print("P1 Health:" + str(data["healthP1"]) + " P2 Health:" + str(
                        data["healthP2"]) + " Current Time:" + str(self.time_remaining))
                self.P1.expected_wins_check_done = data["current_round_winsP1"]

                # If the agent is playing as player 1
                if self.env_player is 'P1':
                    # If it has reached 2 round wins, P1 (agent) has won the stage
                    if data["current_round_winsP1"] == 2:
                        self.on_single_player_stage_win()
                    # If P1 (agent) hasn't reached the round win limit, proceed to the next round
                    else:
                        self.on_single_player_round_win()
                # Else if the agent is playing as player 2
                elif self.env_player is 'P2':
                    # If it has reached 2 round wins, P1 (agent) has won the stage
                    if data["current_round_winsP1"] == 2:
                        self.on_single_player_stage_loss()
                    # If P1 (agent) hasn't reached the round win limit, proceed to the next round
                    else:
                        self.on_single_player_round_loss()
                # Else if this Vs self-play
                else:
                    # If it has reached 2 round wins, P1 has won the Vs stage
                    if data["current_round_winsP1"] == 2:
                        self.on_vs_stage_done('P1')
                    # If P1 hasn't reached the round win limit, proceed to the next round
                    else:
                        self.on_vs_round_done()

            # If the round wins of P2 have incremented, P2 has won a round!
            elif data["current_round_winsP2"] == self.P2.expected_wins_check_done + 1:
                if self.debug:
                    print(">Debug: Game End Condition Met -> P2 wins have incremented in game's memory.")
                    print("P1 Health:" + str(data["healthP1"]) + " P2 Health:" + str(
                        data["healthP2"]) + " Current Time:" + str(self.time_remaining))
                self.P2.expected_wins_check_done = data["current_round_winsP2"]

                # If the agent is playing as player 2
                if self.env_player is 'P2':
                    # If it has reached 2 round wins, P2 (agent) has won the stage
                    if data["current_round_winsP2"] == 2:
                        self.on_single_player_stage_win()
                    # If P2 (agent) hasn't reached the round win limit, proceed to the next round
                    else:
                        self.on_single_player_round_win()
                # Else if the agent is playing as player 1
                elif self.env_player is 'P1':
                    # If agent is P1 and P2 (CPU) wins 2 rounds, the game is over for the agent
                    if data["current_round_winsP2"] == 2:
                        self.on_single_player_stage_loss()
                    # If P2 (CPU) hasn't reached the round win limit, proceed to the next round
                    else:
                        self.on_single_player_round_loss()
                # Else if this Vs self-play
                else:
                    # If it has reached 2 round wins, P2 has won the Vs stage
                    if data["current_round_winsP2"] == 2:
                        self.on_vs_stage_done('P2')
                    # If P2 hasn't reached the round win limit, proceed to the next round
                    else:
                        self.on_vs_round_done()

            # If no round wins have incremented but both players' health has reached 0
            # or the time has reached 00 and both players have equal health, it's a draw!
            elif data["healthP1"] == 0 and data["healthP2"] == 0:
                if self.debug:
                    print(">Debug: Game End Condition Met -> Both P1 and P2 health values have reached 0 (Draw).")
                    print("P1 Health:" + str(data["healthP1"]) + " P2 Health:" + str(
                        data["healthP2"]) + " Current Time:" + str(self.time_remaining))
                    print(">Debug: Draw! Advancing to next round. \n")
                self.round_done = True
            elif data["healthP1"] == data["healthP2"] and self.time_remaining == 0:
                if self.debug:
                    print(
                        ">Debug: Game End Condition Met -> Time has ran out with P1 and P2 health values equal (Draw).")
                    print("P1 Health:" + str(data["healthP1"]) + " P2 Health:" + str(
                        data["healthP2"]) + " Current Time:" + str(self.time_remaining))
                    print(">Debug: Draw! Advancing to next round. \n")
                self.round_done = True
            else:
                raise EnvironmentError('Done flag enabled but game done condition not detected in check_done')

        return data

    def reset(self):
        if self.game_over:
            if not self.self_play:
                self.new_game_after_loss()
            else:
                if self.env_player is 'Vs' and not self.finished_single_player:
                    self.vs_continue(self.last_vs_game_winner)
                elif self.env_player is 'Vs' and self.finished_single_player:
                    self.vs_after_single_player()
                else:
                    self.single_player_after_vs()
        elif self.game_completed:
            self.new_game_after_completion()
        elif self.stage_done:
            self.next_stage()
        elif self.round_done:
            self.next_round()
        else:
            raise EnvironmentError("Reset called while gameplay still running")

    def log_stage_milestone(self):
        assert(self.env_player is 'P1' or self.env_player is 'P2')
        # Create milestones folder if it does not exist
        if not os.path.exists('milestones'):
          os.mkdir('milestones')
        # Create a text file called the [name of the environment] + "_milestones" if it does not exist
        # Open the text file with write permission
        if not self.logged_first_milestone:
            # If this is a new training, create or overwrite existing milestones file
            f = open(os.path.join('milestones', self.env_id + '_milestones.txt'), 'w+')
        else:
            # If this is a continuation from a previous session and a milestone file exists, 
            # append to the milestones file
            f = open(os.path.join('milestones', self.env_id + '_milestones.txt'), 'a+')
            # Create a newline
            f.write('\n')
        # Write the milestone
        f.write(self.env_id + " has managed to defeat stage " + str(self.stage) + " after " +
                str(self.total_episodes_played) + " total episodes playing as " + self.env_player + " with " +
                self.P1.character_name if self.env_player is 'P1' else self.P2.character_name + ".\r\n")
        # Close the milestones file
        f.close()

    def log_milestone(self):
        assert(self.env_player is 'P1' or self.env_player is 'P2')
        # Create milestones folder if it does not exist
        if not os.path.exists('milestones'):
          os.mkdir('milestones')
        # Create a text file called the [name of the environment] + "_milestones" if it does not exist
        # Open the text file with write permission
        if not self.logged_first_milestone:
            # If this is a new training, create or overwrite existing milestones file
            f = open(os.path.join('milestones', self.env_id + '_milestones.txt'), 'w+')
        else:
            # If this is a continuation from a previous session and a milestone file exists, 
            # append to the milestones file
            f = open(os.path.join('milestones', self.env_id + '_milestones.txt'), 'a+')
            # Create a newline
            f.write('\n')
        # Write the milestone
        f.write(self.env_id + " has managed to complete the " + str(self.path) + " path on the "
                + str(self.difficulties[self.difficulty]) + " difficulty after " + str(self.total_episodes_played)
                + " total episodes as " + self.env_player + " with " + self.P1.character_name if self.env_player is 'P1'
                else self.P2.character_name + ".\r\n")
        # Close the milestones file
        f.close()

    # Safely closes emulator
    def close(self):
        self.emu.close()
