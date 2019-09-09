import gym

from aea.protocols.base.message import Message
from aea.mail.base import Envelope, OutBox

from abc import ABC, abstractmethod

from typing import Tuple, Any

from queue import Queue

Action = Any
Observation = Any
Reward = float
Done = bool
Info = dict
Feedback = Tuple[Observation, Reward, Done, Info]

outbox: OutBox
public_key: str


class ProxyEnv(gym.Env, ABC):
    metadata = {'render.modes': ['human']}

    def __init__(self, ):
        super().__init__()
        self.queue = Queue()
        # protocol object
        # outbox of the agent
        # queue between the training thread and the main thread that receives messages

    def step(self, action: Action) -> Feedback:
        """"
        The standard step method of a gym environment.

        - The action is given to apply_action, which does the necessary conversion and then executes it.
        - Then through receive_percept_message, the method waits for a reply from the real environment.
        - Finally, the received reply is converted into the standard observation, reward, done and info
        via message_to_percept

        More information in the comments under the other methods.

        :param action: the action sent to the step method (e.g. the output of an RL algorithm)
        :return: a Tuple containing the Feedback of Observation, Reward, Done and Info
        """

        self.apply_action(action)

        msg = self.receive_percept_message()

        observation, reward, done, info = self.message_to_percept(msg)

        return observation, reward, done, info

    @abstractmethod
    def apply_action(self, action: Action) -> None:
        """"
        Execute the 'action' sent to the step function.

        This usually involves
        - Transforming the 'action' (e.g. price) that is an output of an RL algorithm into an action
        that is executable in the real environment (e.g. a proposal message containing the price).
        - Executing the action in the real environment (e.g. send the proposal to another agent).

        :param action: the action sent to the step method (e.g. the output of an RL algorithm)
        :return: a Tuple containing the Feedback of Observation, Reward, Done and Info
        """
        pass

    @abstractmethod
    def receive_percept_message(self) -> Message:
        """"
        Receive the reply to the action taken.

        The command to receive the message is blocking.
        This usually involves
        - Transforming the 'action' (e.g. price) that is an output of an RL algorithm into an action
        that is executable in the real environment (e.g. a proposal message containing the price).
        - Executing the action in the real environment (e.g. send the proposal to another agent).

        :return: a Tuple containing the Feedback of Observation, Reward, Done and Info
        """
        pass

    @abstractmethod
    def message_to_percept(self, message: Message) -> Feedback:
        """"
        Transform the message received from the real (typically Multi-Agent) environment into
        observation, reward, done, info.

        :param message: the message received from the real environment.
        :return: a Tuple containing the Feedback of Observation, Reward, Done and Info
        """
        pass
