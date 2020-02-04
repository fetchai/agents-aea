"""This module contains two_party_negotiation's message definition."""

from enum import Enum
from typing import Dict, FrozenSet, Optional, Set, Tuple, cast

from aea.configurations.base import ProtocolId
from aea.protocols.base import Message

DEFAULT_BODY_SIZE = 4


class Unit:
    """This class represents an instance of Unit."""

    def __init__(self):
        """Initialise an instance of Unit."""
        raise NotImplementedError


class IOTApp7:
    """This class represents an instance of IOTApp7."""

    def __init__(self):
        """Initialise an instance of IOTApp7."""
        raise NotImplementedError


class DataModel:
    """This class represents an instance of DataModel."""

    def __init__(self):
        """Initialise an instance of DataModel."""
        raise NotImplementedError


class TwoPartyNegotiationMessage(Message):
    """A protocol for negotiation over a fixed set of resources involving two parties."""

    protocol_id = ProtocolId("fetchai", "two_party_negotiation", "0.1.0")

    _speech_acts = {
        "cfp": {"query": DataModel},
        "propose": {"number": int, "price": float, "description": str, "flag": bool, "query": DataModel, "proposal": Optional[Dict[IOTApp7, bytes]], "rounds": FrozenSet[int], "items": Tuple[Unit]},
        "accept": {},
        "decline": {},
        "match_accept": {},
    }

    class Performative(Enum):
        """Performatives for the two_party_negotiation protocol."""

        DECLINE = "decline"
        CFP = "cfp"
        MATCH_ACCEPT = "match_accept"
        PROPOSE = "propose"
        ACCEPT = "accept"

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
        """Initialise."""
        super().__init__(
            dialogue_reference=dialogue_reference,
            message_id=message_id,
            target=target,
            performative=performative,
            **kwargs,
        )
        assert (
            self._check_consistency()
        ), "This message is invalid according to the 'two_party_negotiation' protocol"

    @property
    def valid_performatives(self) -> Set[str]:
        """Get valid performatives."""
        return set(self._speech_acts.keys())

    @property
    def dialogue_reference(self) -> Tuple[str, str]:
        """Get the dialogue_reference of the message."""
        assert self.is_set("dialogue_reference"), "dialogue_reference is not set"
        return cast(Tuple[str, str], self.get("dialogue_reference"))

    @property
    def message_id(self) -> int:
        """Get the message_id of the message."""
        assert self.is_set("message_id"), "message_id is not set"
        return cast(int, self.get("message_id"))

    @property
    def target(self) -> int:
        """Get the target of the message."""
        assert self.is_set("target"), "target is not set."
        return cast(int, self.get("target"))

    @property
    def performative(self) -> Performative:  # noqa: F821
        """Get the performative of the message."""
        assert self.is_set("performative"), "performative is not set"
        return cast(TwoPartyNegotiationMessage.Performative, self.get("performative"))

    @property
    def query(self) -> DataModel:
        """Get the query from the message."""
        assert self.is_set("query"), "query is not set"
        return cast(DataModel, self.get("query"))

    @property
    def number(self) -> int:
        """Get the number from the message."""
        assert self.is_set("number"), "number is not set"
        return cast(int, self.get("number"))

    @property
    def price(self) -> float:
        """Get the price from the message."""
        assert self.is_set("price"), "price is not set"
        return cast(float, self.get("price"))

    @property
    def description(self) -> str:
        """Get the description from the message."""
        assert self.is_set("description"), "description is not set"
        return cast(str, self.get("description"))

    @property
    def flag(self) -> bool:
        """Get the flag from the message."""
        assert self.is_set("flag"), "flag is not set"
        return cast(bool, self.get("flag"))

    @property
    def proposal(self) -> Optional[Dict[IOTApp7, bytes]]:
        """Get the proposal from the message."""
        assert self.is_set("proposal"), "proposal is not set"
        return cast(Optional[Dict[IOTApp7, bytes]], self.get("proposal"))

    @property
    def rounds(self) -> FrozenSet[int]:
        """Get the rounds from the message."""
        assert self.is_set("rounds"), "rounds is not set"
        return cast(FrozenSet[int], self.get("rounds"))

    @property
    def items(self) -> Tuple[Unit]:
        """Get the items from the message."""
        assert self.is_set("items"), "items is not set"
        return cast(Tuple[Unit], self.get("items"))

    def _check_consistency(self) -> bool:
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
                assert type(self.query) == DataModel, "query is not 'DataModel'."
            elif self.performative == TwoPartyNegotiationMessage.Performative.PROPOSE:
                expected_nb_of_contents = 8
                assert type(self.number) == int, "number is not 'int'."
                assert type(self.price) == float, "price is not 'float'."
                assert type(self.description) == str, "description is not 'str'."
                assert type(self.flag) == bool, "flag is not 'bool'."
                assert type(self.query) == DataModel, "query is not 'DataModel'."
                if self.is_set("proposal"):
                    assert type(self.proposal) == dict, "proposal is not 'dict'."
                    for key, value in self.proposal.items():
                        assert type(key) == IOTApp7, "Keys of proposal dictionary are not 'IOTApp7'."
                        assert type(value) == bytes, "Values of proposal dictionary are not 'bytes'."
                assert type(self.rounds) == frozenset, "rounds is not 'frozenset'."
                assert all(type(element) == int for element in self.rounds), "Elements of rounds are not 'int'."
                assert type(self.items) == tuple, "items is not 'tuple'."
                assert all(type(element) == Unit for element in self.items), "Elements of items are not 'Unit'."
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
