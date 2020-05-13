import random
import matplotlib
import numpy as np
import os
import matplotlib.pyplot as plt
from MAMEToolkit.umk3_environment import Environment

roms_path = "../emulator/mame/roms"  # Replace this with the path to your ROMs
env = Environment("random_agent_umk3", roms_path, self_play=True)
env.start()

episodes = 15

episode = 0
p1_episode_return = 0
p2_episode_return = 0
name = "Random_Agent_Vs"

while episode < episodes:

    if env.env_player is 'Vs':
        p1_move_action = random.randint(0, 8)
        p1_attack_action = random.randint(0, 6)
        p2_move_action = random.randint(0, 8)
        p2_attack_action = random.randint(0, 6)

        frames, reward, done, round_done, stage_done, game_over, game_completed = env.vs_step(
            p1_move_action, p1_attack_action, p2_move_action, p2_attack_action)
        p1_episode_return += reward['P1']
        p2_episode_return += reward['P2']
    elif env.env_player is 'P1':
        move_action = random.randint(0, 8)
        attack_action = random.randint(0, 6)
        frames, reward, done, round_done, stage_done, game_over, game_completed = env.step(move_action, attack_action)
        p1_episode_return += reward['P1']
    else:
        move_action = random.randint(0, 8)
        attack_action = random.randint(0, 6)
        frames, reward, done, round_done, stage_done, game_over, game_completed = env.step(move_action, attack_action)
        p2_episode_return += reward['P2']

    '''
    for frame in frames:
        plt.imshow(frame)
        plt.show()
    '''

    if done:
        env.reset()
        p1_episode_return = 0
        p2_episode_return = 0
        episode += 1


env.close()
