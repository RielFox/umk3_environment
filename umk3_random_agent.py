import random
import matplotlib
import matplotlib.pyplot as plt
from MAMEToolkit.umk3_environment import Environment

roms_path = "../emulator/mame/roms"  # Replace this with the path to your ROMs
env = Environment("random_agent_umk3", roms_path)
env.start()

while True:

    move_action = random.randint(0, 8)
    attack_action = random.randint(0, 6)
    frames, reward, done, round_done, stage_done, game_over, game_completed = env.step(move_action, attack_action)

    '''
    for frame in frames:
        plt.imshow(frame)
        plt.show()
    '''

    if done:
        env.reset()

