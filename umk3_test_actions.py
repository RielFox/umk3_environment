import random
import matplotlib
import matplotlib.pyplot as plt
import time
from MAMEToolkit.umk3_environment import Environment

seconds_between_key_press = 3

roms_path = "../emulator/mame/roms"  # Replace this with the path to your ROMs
env = Environment("random_agent_umk3", roms_path)
env.start()

for i in range(0, 9*7):

    move_action = int(i / 7)
    attack_action = i % 7

    print('Taking move action:' + str(move_action) + ', attack action:' + str(attack_action))

    frames, reward, done, round_done, stage_done, game_over, game_completed = env.step(move_action, attack_action)

    if done:
        env.reset()

    t_end = time.time() + seconds_between_key_press

    while time.time() < t_end:
        frames, reward, done, round_done, stage_done, game_over, game_completed = env.step(move_action, attack_action)
        if done:
            env.reset()

    '''
    for frame in frames:
        plt.imshow(frame)
        plt.show()
    '''



