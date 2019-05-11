import random
from MAMEToolkit.umk3_environment import Environment

roms_path = "../emulator/mame/roms"  # Replace this with the path to your ROMs
env = Environment("env1", roms_path)
env.start()

while True:
    move_action = random.randint(0, 8)
    attack_action = random.randint(0, 6)
    #frames, reward, round_done, stage_done, game_done = env.step(move_action, attack_action)
