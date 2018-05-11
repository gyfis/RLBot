import asyncio
import json

import websockets

from RLBotFramework.agents.base_flatbuffer_agent import BaseFlatbufferAgent
from RLBotFramework.agents.base_flatbuffer_agent import SimpleControllerState
from RLBotMessages.flat import GameTickPacket

PORT = 42008
central_packet = None
controller_states = {}


async def data_exchange(websocket, path):
    async for message in websocket:
        global controller_states
        controller_states = json.loads(message)

        if central_packet is not None:
            await websocket.send(json.dumps(central_packet))

start_server = websockets.serve(data_exchange, 'localhost', PORT)


class FlatBot(BaseFlatbufferAgent):

    def __init__(self, name, team, index):
        BaseFlatbufferAgent.__init__(self, name, team, index)
        self.persistent_controller = SimpleControllerState()

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:

        asyncio.get_event_loop().run_until_complete(start_server)

        index_str = str(self.index)

        if index_str in controller_states:
            scratch_state = controller_states[index_str]
            self.persistent_controller.steer = scratch_state['steer']
            self.persistent_controller.throttle = scratch_state['throttle']
            self.persistent_controller.pitch = scratch_state['pitch']
            self.persistent_controller.yaw = scratch_state['yaw']
            self.persistent_controller.roll = scratch_state['roll']
            self.persistent_controller.jump = scratch_state['jump']
            self.persistent_controller.boost = scratch_state['boost']
            self.persistent_controller.handbrake = scratch_state['handbrake']

        if packet.Ball() is None:  # This happens during replays
            return self.persistent_controller

        ball_phys = packet.Ball().Physics()

        players = []
        for i in range(packet.PlayersLength()):
            players.append(player_to_dict(packet.Players(i)))

        global central_packet

        central_packet = {
            'ball': {
                'location': v3_to_dict(ball_phys.Location()),
                'velocity': v3_to_dict(ball_phys.Velocity())
            },
            'players': players
        }

        return self.persistent_controller


def player_to_dict(car):
    return {
        'location': v3_to_dict(car.Physics().Location()),
        'velocity': v3_to_dict(car.Physics().Velocity()),
        'rotation': rot_to_dict(car.Physics().Rotation())
    }


def v3_to_dict(v3):
    return {
        'x': v3.X(),
        'y': v3.Y(),
        'z': v3.Z()
    }


def rot_to_dict(rot):
    return {
        'pitch': rot.Pitch(),
        'yaw': rot.Yaw(),
        'roll': rot.Roll()
    }
