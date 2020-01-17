"""This module contains two_party_negotiation's message definition."""

from typing import Dict, cast

from aea.protocols.base import Message


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

    def __init__(
        self, message_id: int, target: int, performative: str, contents: Dict, **kwargs
    ):
        """Initialise."""
        super().__init__(
            message_id=message_id,
            target=target,
            performative=performative,
            contents=contents,
            **kwargs
        )

        self.speech_acts = {
            "cfp": {"query", DataModel},
            "propose": {"query", DataModel, "price", float},
            "accept": {},
            "decline": {},
            "match_accept": {},
        }

        assert self.check_consistency()

    @property
    def performatives(self) -> set:
        """Get allowed performatives."""
        return set(self.speech_acts.keys())

    def check_consistency(self) -> bool:
        """Check that the message follows the two_party_negotiation protocol."""
        try:
            assert self.is_set("message_id"), "message_id is not set"
            message_id = self.get("message_id")
            assert type(message_id) == int, "message_id is not int"

            assert self.is_set("target"), "target is not set"
            target = self.get("target")
            assert type(target) == int, "target is not int"

            assert self.is_set("performative"), "performative is not set"
            performative = self.get("performative")
            assert type(performative) == str, "performative is not str"

            assert self.is_set("contents"), "contents is not set"
            contents = self.get("contents")
            assert type(contents) == dict, "contents is not a dictionary"
            contents = cast(Dict, contents)

            # Light Protocol 2
            # Check correct performative
            assert (
                performative in self.performatives
            ), "performative is not in the list of allowed performative"

            # Check correct contents
            contents_definition = self.speech_acts[performative]  # type is Dict
            # Check number of contents
            assert len(contents) == len(
                contents_definition
            ), "incorrect number of contents"
            # Check the content is of the correct type
            for content, content_type in contents_definition:
                assert isinstance(
                    contents[content], content_type
                ), "incorrect content type"

            # Light Protocol 3
            if message_id == 1:
                assert target == 0, "target should be 0"
            else:
                assert (
                    0 < target < message_id
                ), "target should be strictly between 0 and message_id"
        except (AssertionError, ValueError, KeyError) as e:
            print(str(e))
            return False

        return True
