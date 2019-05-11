from MAMEToolkit.emulator import list_actions

roms_path = "/home/rielfox4/anaconda3/envs/tensorflow/lib/python3.6/site-packages/MAMEToolkit/emulator/mame/roms"  # Replace this with the path to your ROMs
game_id = "umk3"
print(list_actions(roms_path, game_id))