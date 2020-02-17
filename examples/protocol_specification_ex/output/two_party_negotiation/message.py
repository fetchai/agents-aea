"""This module contains two_party_negotiation's message definition."""

from enum import Enum
from typing import Dict, FrozenSet, Optional, Set, Tuple, Union, cast

from aea.configurations.base import ProtocolId
from aea.protocols.base import Message

DEFAULT_BODY_SIZE = 4


class TwoPartyNegotiationMessage(Message):
    """A protocol for negotiation over a fixed set of resources involving two parties."""

    protocol_id = ProtocolId("fetchai", "two_party_negotiation", "0.1.0")

    class Performative(Enum):
        """Performatives for the two_party_negotiation protocol."""

        ACCEPT = "accept"
        CFP = "cfp"
        DECLINE = "decline"
        MATCH_ACCEPT = "match_accept"
        PROPOSE = "propose"

        def __str__(self):
            """Get string representation."""
            return self.value

    def __init__(
        self,
        dialogue_reference: Tuple[str, str],
        message_id: int,
        target: int,
        performative: str,
        **kwargs,
    ):
        """Initialise an instance of TwoPartyNegotiationMessage."""
        super().__init__(
            dialogue_reference=dialogue_reference,
            message_id=message_id,
            target=target,
            performative=performative,
            **kwargs,
        )
        self._performatives = {"accept", "cfp", "decline", "match_accept", "propose"}
        assert (
            self._is_consistent()
        ), "This message is invalid according to the 'two_party_negotiation' protocol."

    @property
    def valid_performatives(self) -> Set[str]:
        """Get valid performatives."""
        return self._performatives

    @property
    def dialogue_reference(self) -> Tuple[str, str]:
        """Get the dialogue_reference of the message."""
        assert self.is_set("dialogue_reference"), "dialogue_reference is not set."
        return cast(Tuple[str, str], self.get("dialogue_reference"))

    @property
    def message_id(self) -> int:
        """Get the message_id of the message."""
        assert self.is_set("message_id"), "message_id is not set."
        return cast(int, self.get("message_id"))

    @property
    def performative(self) -> Performative:  # noqa: F821
        """Get the performative of the message."""
        assert self.is_set("performative"), "performative is not set."
        return cast(TwoPartyNegotiationMessage.Performative, self.get("performative"))

    @property
    def target(self) -> int:
        """Get the target of the message."""
        assert self.is_set("target"), "target is not set."
        return cast(int, self.get("target"))

    @property
    def conditions(self) -> Optional[Union[str, Dict[str, int], FrozenSet[str], Dict[str, float]]]:
        """Get the 'conditions' content from the message."""
        assert self.is_set("conditions"), "'conditions' content is not set."
        return cast(Optional[Union[str, Dict[str, int], FrozenSet[str], Dict[str, float]]], self.get("conditions"))

    @property
    def description(self) -> str:
        """Get the 'description' content from the message."""
        assert self.is_set("description"), "'description' content is not set."
        return cast(str, self.get("description"))

    @property
    def flag(self) -> bool:
        """Get the 'flag' content from the message."""
        assert self.is_set("flag"), "'flag' content is not set."
        return cast(bool, self.get("flag"))

    @property
    def items(self) -> Tuple[int]:
        """Get the 'items' content from the message."""
        assert self.is_set("items"), "'items' content is not set."
        return cast(Tuple[int], self.get("items"))

    @property
    def number(self) -> int:
        """Get the 'number' content from the message."""
        assert self.is_set("number"), "'number' content is not set."
        return cast(int, self.get("number"))

    @property
    def price(self) -> float:
        """Get the 'price' content from the message."""
        assert self.is_set("price"), "'price' content is not set."
        return cast(float, self.get("price"))

    @property
    def proposal(self) -> Optional[Dict[str, bytes]]:
        """Get the 'proposal' content from the message."""
        assert self.is_set("proposal"), "'proposal' content is not set."
        return cast(Optional[Dict[str, bytes]], self.get("proposal"))

    @property
    def query(self) -> str:
        """Get the 'query' content from the message."""
        assert self.is_set("query"), "'query' content is not set."
        return cast(str, self.get("query"))

    @property
    def rounds(self) -> FrozenSet[int]:
        """Get the 'rounds' content from the message."""
        assert self.is_set("rounds"), "'rounds' content is not set."
        return cast(FrozenSet[int], self.get("rounds"))

    def _is_consistent(self) -> bool:
        """Check that the message follows the two_party_negotiation protocol."""
        try:
            assert (
                type(self.dialogue_reference) == tuple
            ), "dialogue_reference must be 'tuple' but it is not."
            assert (
                type(self.dialogue_reference[0]) == str
            ), "The first element of dialogue_reference must be 'str' but it is not."
            assert (
                type(self.dialogue_reference[1]) == str
            ), "The second element of dialogue_reference must be 'str' but it is not."
            assert type(self.message_id) == int, "message_id is not int"
            assert type(self.target) == int, "target is not int"

            # Light Protocol 2
            # # Check correct performative
            assert (
                type(self.performative) == TwoPartyNegotiationMessage.Performative
            ), "'{}' is not in the list of valid performatives: {}".format(
                self.performative, self.valid_performatives
            )

            # # Check correct contents
            actual_nb_of_contents = len(self.body) - DEFAULT_BODY_SIZE
            if self.performative == TwoPartyNegotiationMessage.Performative.CFP:
                expected_nb_of_contents = 1
                assert type(self.query) == str, "Content 'query' is not of type 'str'."
            elif self.performative == TwoPartyNegotiationMessage.Performative.PROPOSE:
                expected_nb_of_contents = 9
                assert type(self.number) == int, "Content 'number' is not of type 'int'."
                assert type(self.price) == float, "Content 'price' is not of type 'float'."
                assert type(self.description) == str, "Content 'description' is not of type 'str'."
                assert type(self.flag) == bool, "Content 'flag' is not of type 'bool'."
                assert type(self.query) == str, "Content 'query' is not of type 'str'."
                if self.is_set("proposal"):
                    assert type(self.proposal) == dict, "Content 'proposal' is not of type 'dict'."
                    for key, value in self.proposal.items():
                        assert (
                            type(key) == str
                        ), "Keys of 'proposal' dictionary are not of type 'str'."
                        assert (
                            type(value) == bytes
                        ), "Values of 'proposal' dictionary are not of type 'bytes'."
                assert type(self.rounds) == frozenset, "Content 'rounds' is not of type 'frozenset'."
                assert all(
                    type(element) == int for element in self.rounds
                ), "Elements of the content 'rounds' are not of type 'int'."
                assert type(self.items) == tuple, "Content 'items' is not of type 'tuple'."
                assert all(
                    type(element) == int for element in self.items
                ), "Elements of the content 'items' are not of type 'int'."
                if self.is_set("conditions"):
                    assert type(self.conditions) == dict or type(self.conditions) == frozenset or type(self.conditions) == str, "Content 'conditions' should be either of the following types: ['dict', 'frozenset', 'str']."
                    if type(self.conditions) == frozenset:
                        assert (
                            all(type(element) == str for element in self.conditions)
                        ), "Elements of the content 'conditions' should be of type 'str'."
                    if type(self.conditions) == dict:
                        for key, value in self.conditions.items():
                            assert (
                                    (type(key) == str and type(value) == float)
                        ), "The type of keys and values of 'conditions' dictionary must be 'str' and 'float' respectively."
            elif self.performative == TwoPartyNegotiationMessage.Performative.ACCEPT:
                expected_nb_of_contents = 0
            elif self.performative == TwoPartyNegotiationMessage.Performative.DECLINE:
                expected_nb_of_contents = 0
            elif self.performative == TwoPartyNegotiationMessage.Performative.MATCH_ACCEPT:
                expected_nb_of_contents = 0

            # # Check correct content count
            assert (
                expected_nb_of_contents == actual_nb_of_contents
            ), "Incorrect number of contents. Expected {} contents. Found {}".format(
                expected_nb_of_contents, actual_nb_of_contents
            )

            # Light Protocol 3
            if self.message_id == 1:
                assert (
                    self.target == 0
                ), "Expected target to be 0 when message_id is 1. Found {}.".format(
                    self.target
                )
            else:
                assert (
                    0 < self.target < self.message_id
                ), "Expected target to be between 1 to (message_id -1) inclusive. Found {}".format(
                    self.target
                )
        except (AssertionError, ValueError, KeyError) as e:
            print(str(e))
            return False

        return True
