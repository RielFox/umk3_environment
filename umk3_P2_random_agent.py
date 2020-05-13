import random
import matplotlib
import numpy as np
import os
import matplotlib.pyplot as plt
from MAMEToolkit.umk3_environment import Environment

roms_path = "../emulator/mame/roms"  # Replace this with the path to your ROMs
env = Environment("random_agent_umk3", roms_path, self_play=False, player='P2')
env.start()

episodes = 2000

episode = 0
episode_return = 0
name = "Random_Agent_P2"
returns_list = []

#Keeps track of the average return over the last 100 episodes
#[ Useful because the actual returns will vary by a lot ]
#Gives a more stable plot of the return over time
def smooth(x):
    # last 100
    n = len(x)
    y = np.zeros(n)
    for i in range(n):
        start = max(0, i - 99)
        y[i] = float(x[start:(i+1)].sum()) / (i - start + 1)
    return y

def plot_average_returns(returns_list, title):
    # Plot the smoothed returns
    x = np.array(returns_list)
    y = smooth(x)
    plt.title(title)
    plt.plot(x, label='original')
    plt.plot(y, label='smoothed')
    plt.legend()
    # Create directory to store plots if it does not exist
    if not os.path.exists('plots'):
        os.makedirs('plots')
    # Save to directory
    plt.savefig('plots/' + title + '.png')
    # Clear plot
    plt.clf()

while episode < episodes:

    move_action = random.randint(0, 8)
    attack_action = random.randint(0, 6)
    frames, reward, done, round_done, stage_done, game_over, game_completed = env.step(move_action, attack_action)
    episode_return += reward['P2']

    '''
    for frame in frames:
        plt.imshow(frame)
        plt.show()
    '''

    if done:
        env.reset()
        returns_list.append(episode_return)
        episode_return = 0
        episode += 1
        if episode % 500 == 0:
            plot_average_returns(returns_list, name+'_'+str(episode))

env.close()
plot_average_returns(returns_list, name)