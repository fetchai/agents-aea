import gym

from aea.protocols.base.message import Message
from aea.channel.gym import DEFAULT_GYM
from aea.mail.base import Envelope
from aea.protocols.gym.message import GymMessage
from aea.protocols.gym.serialization import GymSerializer

from examples.gym.proxy_agent import ProxyAgent
from examples.gym.proxy_env import ProxyEnv

from typing import Tuple, Any, Optional

import logging

logger = logging.getLogger(__name__)

Action = Any
Observation = Any
Reward = float
Done = bool
Info = dict
Feedback = Tuple[Observation, Reward, Done, Info]


class BanditProxyEnv(ProxyEnv):
    metadata = {'render.modes': ['human']}

    def __init__(self, gym_env: gym.Env):
        super().__init__()
        self.action_counter = 0
        self.proxy_agent = ProxyAgent(name="proxy", env=gym_env, proxy_env_queue=self.queue)

        # self.env = env

        # protocol object
        # outbox of the agent
        # queue between the training thread and the main thread that receives messages

    # def connect(self, outbox: OutBox, public_key: str):
    #     self.outbox = outbox
    #     self.public_key = public_key

    def apply_action(self, action: Action) -> None:
        self.action_counter += 1
        step_id = self.action_counter

        # action = [good_id, price]

        gym_msg = GymMessage(performative=GymMessage.Performative.ACT, action=action, step_id=step_id)
        gym_bytes = GymSerializer().encode(gym_msg)
        self.proxy_agent.outbox.put_message(to=DEFAULT_GYM, sender=self.proxy_agent.public_key,
                                            protocol_id=GymMessage.protocol_id, message=gym_bytes)

    def receive_percept_message(self) -> Message:
        # Keep getting messages from the queue
        # if the message in the queue is the right message (protocol==gym, Percept, correct step_id), then process
        # otherwise put it back in the queue

        envelope = self.queue.get(block=True, timeout=None)  # type: Optional[Envelope]

        expected_step_id = self.action_counter
        # assert to ensure envelope is an instance of Envelope
        if envelope is not None:
            if envelope.protocol_id == 'gym':
                gym_msg = GymSerializer().decode(envelope.message)
                gym_msg_performative = GymMessage.Performative(gym_msg.get("performative"))
                gym_msg_step_id = gym_msg.get("step_id")
                if gym_msg_performative == GymMessage.Performative.PERCEPT and gym_msg_step_id == expected_step_id:
                    return gym_msg
                else:
                    raise ValueError("Unexpected performative or no step_id: {}".format(gym_msg_performative))
            else:
                raise ValueError("Unknown protocol_id: {}".format(envelope.protocol_id))

    def message_to_percept(self, message: Message) -> Feedback:
        observation = message.get("observation")
        done = message.get("done")
        info = message.get("info")
        reward = message.get("reward")

        # step_id = gym_msg.get("step_id")

        return observation, done, reward, info

    def render(self, mode='human'):
        pass

    def reset(self):
        pass
