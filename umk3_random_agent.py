import random
import matplotlib
import matplotlib.pyplot as plt
from MAMEToolkit.umk3_environment import Environment

roms_path = "../emulator/mame/roms"  # Replace this with the path to your ROMs
env = Environment("env1", roms_path)
env.start()

while True:

    if env.debug is True:
        print(">Debug: Agent has taken control.\n")

    move_action = random.randint(0, 8)
    attack_action = random.randint(0, 6)
    frames, reward, round_done, stage_done, game_over, game_completed = env.step(move_action, attack_action)

    '''
    for frame in frames:
        plt.imshow(frame)
        plt.show()
    '''
    #print("Round Done: " + str(round_done) + " .\n")

    if game_over:
        env.new_game_after_loss()
    elif stage_done:
        env.next_stage()
    elif round_done:
        env.next_round()

