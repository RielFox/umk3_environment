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
        #Consecutive round wins for each player, 2 round wins needed to win a match
        "winsP1": Address('0x01062310', 'u8'),
        "winsP2": Address('0x01062320', 'u8'),
        #Time remaining ranges from decimal 99 to 00 during normal gameplay under the default settings
        "time_remaining_tens_digit": Address('0x0105F330', 'u8'),
        "time_remaining_ones_digit": Address('0x0105F340', 'u8'),

        "fighting":Address('0x0105F350','u8'),
        "fighting2":Address('0x0105F360','u8')
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




# The Ultimate Mortal Kombat 3 interface for training an agent against the game
class Environment(object):

    def __init__(self, env_id, roms_path, frame_ratio=1, frames_per_step=1, render=True, throttle=True, debug=True):

        self.frame_ratio = frame_ratio
        self.frames_per_step = frames_per_step
        self.throttle = throttle
        self.emu = Emulator(env_id, roms_path, "umk3", setup_memory_addresses(), frame_ratio=frame_ratio, render=render, throttle=throttle, debug=debug)
        self.started = False
        self.expected_health = {"P1": 0, "P2": 0}
        self.expected_wins = {"P1": 0, "P2": 0}
        self.round_done = False
        self.stage_done = False
        self.game_done = False
        self.stage = 1
        self.difficulty = 'Novice'
        self.character = 'Scorpion'
        self.debug = True

    # Runs a set of action steps over a series of time steps
    # Used for transitioning the emulator through non-learnable gameplay, aka. title screens, character selects
    def run_steps(self, steps):
        for step in steps:
            for i in range(step["wait"]):
                self.emu.step([])
            self.emu.step([action.value for action in step["actions"]])

    # Must be called first after creating this class
    # Sends actions to the game until the learnable gameplay starts
    # Returns the first few frames of gameplay
    def start(self):
         if self.throttle:
             for i in range(int(250 / self.frame_ratio)):
                 self.emu.step([])

         self.run_steps(p1_start_game(self.frame_ratio))
         self.run_steps(p1_select_character(self.frame_ratio, self.character))
         self.run_steps(p1_select_difficulty(self.frame_ratio, self.difficulty))

         self.wait_for_fight_start()


         #frames = self.wait_for_fight_start()
         self.started = True
         #return frames

    def wait_for_fight_start(self):
        data = self.emu.step([])
        while data["fighting"] == 0:
            data = self.emu.step([])
            if self.debug:
                print("healthP1:"+str(data["healthP1"])+" healthP2:"+str(data["healthP2"])+" \n")
                print("turboP1: " + str(data["turboP1"]) + " turboP2: " + str(data["turboP2"]) + " \n")
                print("time_remaining_tens_digit: "+str(data["time_remaining_tens_digit"])+" time_remaining_ones_digit: "+str(data["time_remaining_ones_digit"])+" \n")
                print("winsP1: " + str(data["winsP1"]) + " winsP2: " + str(data["winsP2"]) + " \n")
                print("fighting:" +str(data["fighting"]) + " fighting2:"+str(data["fighting2"])+" \n")

        # Steps the emulator along by the requested amount of frames required for the agent to provide actions

    def step(self, move_action, attack_action):
        if self.started:
            if not self.round_done and not self.stage_done and not self.game_done:
                actions = []
                actions += p1_index_to_move_action(move_action)
                actions += p1_index_to_attack_action(attack_action)
                data = self.gather_frames(actions)
                data = self.check_done(data)
                return data["frame"], data["rewards"], self.round_done, self.stage_done, self.game_done
            else:
                raise EnvironmentError("Attempted to step while characters are not fighting")
        else:
            raise EnvironmentError("Start must be called before stepping")

    # Combines the data of multiple time steps
    def add_rewards(old_data, new_data):
        for k in old_data.keys():
            if "rewards" in k:
                for player in old_data[k]:
                    new_data[k][player] += old_data[k][player]
        return new_data

     # Collects the specified amount of frames the agent requires before choosing an action
    def gather_frames(self, actions):
        data = self.sub_step(actions)
        frames = [data["frame"]]
        for i in range(self.frames_per_step - 1):
            #data = add_rewards(data, self.sub_step(actions))
            frames.append(data["frame"])
        data["frame"] = frames[0] if self.frames_per_step == 1 else frames
        return data

    # Steps the emulator along by one time step and feeds in any actions that require pressing
    # Takes the data returned from the step and updates book keeping variables
    def sub_step(self, actions):
        data = self.emu.step([action.value for action in actions])

        p1_diff = (self.expected_health["P1"] - data["healthP1"])
        p2_diff = (self.expected_health["P2"] - data["healthP2"])
        self.expected_health = {"P1": data["healthP1"], "P2": data["healthP2"]}

        rewards = {
            "P1": (p2_diff - p1_diff),
            "P2": (p1_diff - p2_diff)
        }

        data["rewards"] = rewards
        return data

    # Safely closes emulator

    def close(self):
        self.emu.close()
