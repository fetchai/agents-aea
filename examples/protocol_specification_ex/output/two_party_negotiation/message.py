"""This module contains two_party_negotiation's message definition."""

from typing import Dict, Set, Tuple, cast

from aea.protocols.base import Message

DEFAULT_BODY_SIZE = 4


class DataModel:
    """This class represents a DataModel."""

    def __init__(self):
        """Initialise a DataModel."""
        raise NotImplementedError

    def __eq__(self, other):
        """Compare two instances of this class."""
        if type(other) is type(self):
            raise NotImplementedError
        else:
            return False


class TwoPartyNegotiationMessage(Message):
    """A protocol for negotiation over a fixed set of resources involving two parties."""

    _speech_acts = {
        "cfp": {"query": DataModel},
        "propose": {"query": DataModel, "price": float},
        "accept": {},
        "decline": {},
        "match_accept": {},
    }

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
        assert self._check_consistency()

    @property
    def speech_acts(self) -> Dict[str, Dict[str, str]]:
        """Get all speech acts."""
        return self._speech_acts

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
    def performative(self) -> str:
        """Get the performative of the message."""
        assert self.is_set("performative"), "performative is not set"
        return cast(str, self.get("performative"))

    @property
    def query(self) -> DataModel:
        """Get query for performative cfp."""
        assert self.is_set("query"), "query is not set"
        return cast(DataModel, self.get("query"))

    @property
    def price(self) -> float:
        """Get price for performative propose."""
        assert self.is_set("price"), "price is not set"
        return cast(float, self.get("price"))

    def _check_consistency(self) -> bool:
        """Check that the message follows the two_party_negotiation protocol."""
        try:
            assert isinstance(
                self.dialogue_reference, Tuple
            ), "dialogue_reference must be 'Tuple' but it is not."
            assert isinstance(
                self.dialogue_reference[0], str
            ), "The first element of dialogue_reference must be 'str' but it is not."
            assert isinstance(
                self.dialogue_reference[1], str
            ), "The second element of dialogue_reference must be 'str' but it is not."
            assert type(self.message_id) == int, "message_id is not int"
            assert type(self.target) == int, "target is not int"
            assert type(self.performative) == str, "performative is not str"

            # Light Protocol 2
            # Check correct performative
            assert (
                self.performative in self.valid_performatives
            ), "'{}' is not in the list of valid performativs: {}".format(
                self.performative, self.valid_performatives
            )

            # Check correct contents
            actual_nb_of_contents = len(self.body) - DEFAULT_BODY_SIZE
            if self.performative == "cfp":
                expexted_nb_of_contents = 1
                assert type(self.query) == DataModel, "query is not DataModel"
            if self.performative == "propose":
                expexted_nb_of_contents = 2
                assert type(self.query) == DataModel, "query is not DataModel"
                assert type(self.price) == float, "price is not float"
            if self.performative == "accept":
                expexted_nb_of_contents = 0
            if self.performative == "decline":
                expexted_nb_of_contents = 0
            if self.performative == "match_accept":
                expexted_nb_of_contents = 0

            # Check body size
            assert (
                expexted_nb_of_contents == actual_nb_of_contents
            ), "Incorrect number of contents. Expected {} contents. Found {}".format(
                expexted_nb_of_contents, actual_nb_of_contents
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
