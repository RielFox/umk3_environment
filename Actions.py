from enum import Enum
from MAMEToolkit.emulator.Action import Action


# Enumerable class that specifies which actions can be used to interact with the game
# Specifies the Lua engine port and field names required for performing an action
class Actions(Enum):
    # Misc
    SERVICE = Action(':IN2', 'Service Mode')

    COIN_P1 = Action(':IN2', 'Coin 1')
    COIN_P2 = Action(':IN2', 'Coin 2')

    P1_START = Action(':IN2', '1 Player Start')
    P2_START = Action(':IN2', '2 Players Start')

    VOLUME_UP = Action(':IN2', 'Volume Up')
    VOLUME_DOWN = Action(':IN2', 'Volume Down')

    # Movement
    P1_UP = Action(':IN0', 'P1 Up')
    P1_DOWN = Action(':IN0', 'P1 Down')
    P1_LEFT = Action(':IN0', 'P1 Left')
    P1_RIGHT = Action(':IN0', 'P1 Right')

    P2_UP = Action(':IN0', 'P2 Up')
    P2_DOWN = Action(':IN0', 'P2 Down')
    P2_LEFT = Action(':IN0', 'P2 Left')
    P2_RIGHT = Action(':IN0', 'P2 Right')

    # Fighting
    P1_LPUNCH = Action(':IN1', 'P1 Low Punch')
    P1_HPUNCH = Action(':IN0', 'P1 High Punch')
    P1_LKICK = Action(':IN1', 'P1 Low Kick')
    P1_HKICK = Action(':IN0', 'P1 High Kick')
    P1_BLOCK = Action(':IN0', 'P1 Block')
    P1_RUN = Action(':IN1', 'P1 Run')

    P2_LPUNCH = Action(':IN1', 'P2 Low Punch')
    P2_HPUNCH = Action(':IN0', 'P2 High Punch')
    P2_LKICK = Action(':IN1', 'P2 Low Kick')
    P2_HKICK = Action(':IN0', 'P2 High Kick')
    P2_BLOCK = Action(':IN0', 'P2 Block')
    P2_RUN = Action(':IN1', 'P2 Run')
