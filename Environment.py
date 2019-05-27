from MAMEToolkit.emulator.Emulator import Emulator
from MAMEToolkit.emulator.Address import Address
from MAMEToolkit.umk3_environment.Steps import *
from MAMEToolkit.umk3_environment.Actions import Actions


# Returns the list of memory addresses required to train on Ultimate Mortal Kombat 3 v2.2 (umk3)
def setup_memory_addresses():
    return {
        #Health values range from 0xA6 (decimal 166) to 0x00 during normal gameplay
        "healthP1": Address('0x01060A60', 's16'),
        "healthP2": Address('0x01061610', 's16'),
        #Stamina values for performing combos range from 0x30 to 0x00 during normal gameplay
        "turboP1": Address('0x01060A70', 's16'),
        "turboP2": Address('0x01061620', 's16'),
        #Consecutive round wins for each player, 2 round wins needed to win a stage
        "total_round_winsP1": Address('0x01062310', 'u8'),
        "total_round_winsP2": Address('0x01062320', 'u8'),
        #Round wins for each player for the current stage, 2 round wins needed to win a stage
        "current_round_winsP1": Address('0x01060A90', 'u8'),
        "current_round_winsP2": Address('0x01061640', 'u8'),
        #Time remaining ranges from decimal 99 to 00 during normal gameplay under the default settings
        "time_remaining_tens_digit": Address('0x0105F330', 'u8'),
        "time_remaining_ones_digit": Address('0x0105F340', 'u8'),
        #A flag value used for rendering some of the background of a stage during a fight
        #It is 1 during a stage, becomes 0 in between stages but remains 1 in-between rounds
        "fighting": Address('0x0105F350', 'u8')
    }

# Converts and index (action) into the relevant movement action enum
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

# Converts and index (action) into the relevant attack action Enum, depending on the player
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


# Combines the data of multiple time steps
def add_rewards(old_data, new_data):
    for k in old_data.keys():
        if "rewards" in k:
            for player in old_data[k]:
                new_data[k][player] += old_data[k][player]
    return new_data


# The Ultimate Mortal Kombat 3 interface for training an agent against the game
class Environment(object):

    def __init__(self, env_id, roms_path, player='P1', frame_ratio=10, frames_per_step=4, render=True, throttle=True, debug=True):

        self.frame_ratio = frame_ratio
        self.frames_per_step = frames_per_step
        self.throttle = throttle
        self.emu = Emulator(env_id, roms_path, "umk3", setup_memory_addresses(), frame_ratio=frame_ratio, render=render,
                            throttle=throttle, debug=debug)
        self.started = False
        self.expected_health = {"P1": 0, "P2": 0}
        self.expected_wins = {"P1": 0, "P2": 0}
        self.expected_wins_check_done = {"P1": 0, "P2": 0}
        self.expected_time_remaining = 0
        self.round_done = False
        self.stage_done = False
        self.game_over = False
        self.game_completed = False

        self.player = player
        self.p1_total_rewards_this_round = 0
        self.p2_total_rewards_this_round = 0
        self.total_rewards_this_game = 0

        self.stage = 1
        self.path = 'Novice'
        self.character = 'Scorpion'
        self.debug = True

    # Runs a set of action steps over a series of time steps
    # Used for transitioning the emulator through non-learnable gameplay, aka. title screens, character selects
    def run_steps(self, steps):
        for step in steps:
            for i in range(step["wait"]):
                self.emu.step([])
            self.emu.step([action.value for action in step["actions"]])

    def new_game(self):
        if self.debug:
            print(">Debug: Starting a new game.\n")
        self.run_steps(p1_start_game(self.frame_ratio))
        self.run_steps(p1_select_character(self.frame_ratio, self.character))
        self.run_steps(p1_select_path(self.frame_ratio, self.path))
        self.wait_for_fight_start()
        self.expected_health = {"P1": 0, "P2": 0}
        self.expected_wins = {"P1": 0, "P2": 0}
        self.round_done = False
        self.stage_done = False
        self.game_over = False
        self.game_completed = False
        self.started = True

    # Must be called first after creating this class
    # Sends actions to the game until the learnable gameplay starts
    # Returns the first few frames of gameplay
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
        self.expected_health = {"P1": 0, "P2": 0}
        self.expected_wins = {"P1": 0, "P2": 0}
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
        self.round_done = False
        self.expected_health = {"P1": 0, "P2": 0}
        return self.wait_for_next_round_start()

    def wait_for_next_round_start(self):
        if self.debug:
            print(">Debug: Waiting for next round to start...\n")
        data = self.emu.step([])
        self.time_remaining = (int(data["time_remaining_tens_digit"]) * 10) + int(data["time_remaining_ones_digit"])
        while int(data["healthP1"]) != 166 and int(data["healthP2"]) != 166 and self.time_remaining != 99:
            data = self.emu.step([])

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
    def step(self, move_action, attack_action):
        if self.started:
            if not self.round_done and not self.stage_done and not self.game_over and not self.game_completed:
                actions = []
                actions += p1_index_to_move_action(move_action)
                actions += p1_index_to_attack_action(attack_action)
                data = self.gather_frames(actions)
                data = self.p1_check_done(data)

                if self.debug:
                    print(">Debug: healthP1:" + str(data["healthP1"]) + " healthP2:" + str(data["healthP2"]) + " \n")
                    print(">Debug: turboP1: " + str(data["turboP1"]) + " turboP2: " + str(data["turboP2"]) + " \n")
                    print(">Debug: time_remaining_tens_digit: " + str(
                        data["time_remaining_tens_digit"]) + " time_remaining_ones_digit: " + str(
                        data["time_remaining_ones_digit"]) + " \n")
                    print(">Debug: winsP1: " + str(data["current_round_winsP1"]) + " winsP2: " + str(
                        data["current_round_winsP2"]) + " \n")
                    print(">Debug: fighting:" + str(data["fighting"]) + " \n")

                return data["frame"], data["rewards"], self.round_done, self.stage_done, self.game_over, self.game_completed
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

        p1_diff_reward = (self.expected_health["P1"] - data["healthP1"])
        p2_diff_reward = (self.expected_health["P2"] - data["healthP2"])
        self.expected_health = {"P1": data["healthP1"], "P2": data["healthP2"]}

        if data["current_round_winsP1"] == self.expected_wins["P1"] + 1:
            p1_round_win_reward = 100
            p2_round_win_reward = -100
        elif data["current_round_winsP2"] == self.expected_wins["P2"] + 1:
            p2_round_win_reward = 100
            p1_round_win_reward = -100
        else:
            p1_round_win_reward = 0
            p2_round_win_reward = 0

        self.expected_wins["P1"] = data["current_round_winsP1"]
        self.expected_wins["P2"] = data["current_round_winsP2"]

        self.time_remaining = (int(data["time_remaining_tens_digit"]) * 10) + int(data["time_remaining_ones_digit"])

        print("tr: " + str(self.time_remaining) + " etr: " + str(self.expected_time_remaining))

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

        #Return the total rewards of each player for this timestep in a rewards dictionary
        rewards = {
            "P1": (p2_diff_reward - p1_diff_reward) + p1_time_remaining_reward + p1_round_win_reward,
            "P2": (p1_diff_reward - p2_diff_reward) + p2_time_remaining_reward + p2_round_win_reward
        }

        if self.debug:
            print(">Debug: Rewards for P1 this timestep: " + str(rewards["P1"]) + "\n")
            print(">Debug: Rewards for P2 this timestep: " + str(rewards["P2"]) + "\n")

        data["rewards"] = rewards
        return data

    # Checks whether the round or game has finished
    def p1_check_done(self, data):

        self.time_remaining = (int(data["time_remaining_tens_digit"]) * 10) + int(data["time_remaining_ones_digit"])

        if data["current_round_winsP1"] == self.expected_wins_check_done["P1"] + 1:
            self.expected_wins_check_done["P1"] = data["current_round_winsP1"]

            if data["current_round_winsP1"] == 2:
                self.stage_done = True
                self.stage += 1

                if self.debug:
                    print(">Debug: Stage won. Advancing to stage " + str(self.stage) + ". \n")
            else:
                self.round_done = True

                if self.debug:
                    print(">Debug: Round won. Advancing to next round. \n")

        elif data["current_round_winsP2"] == self.expected_wins_check_done["P2"] + 1:
            self.expected_wins_check_done["P2"] = data["current_round_winsP2"]

            if data["current_round_winsP2"] == 2:
                self.game_over = True

                if self.debug:
                    print(">Debug: Stage lost. Quiting game. \n")
            else:
                self.round_done = True

                if self.debug:
                    print(">Debug: Round lost. Advancing to next round. \n")
        elif (data["healthP1"] == 0 and data["healthP2"] == 0) or self.time_remaining == 0:
            if self.debug:
                print(">Debug: Draw! Advancing to next round. \n")
            self.round_done = True

        return data

    # Safely closes emulator
    def close(self):
        self.emu.close()
