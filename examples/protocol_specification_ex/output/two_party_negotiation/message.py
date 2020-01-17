"""This module contains two_party_negotiation's message definition."""

from typing import cast, Dict, Tuple

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

    def __init__(self, message_id: int, target: int, performative: str, contents: Dict, **kwargs):
        """Initialise."""
        super().__init__(message_id=message_id, target=target, performative=performative, contents=contents, **kwargs)

        self.speech_acts_definition = {
            'cfp': {
                'query', DataModel
            },
            'propose': {
                'query', DataModel,
                'price', float
            },
            'accept': {},
            'decline': {},
            'match_accept': {}
        }

        assert self.check_consistency()

    @property
    def performatives_definition(self) -> set:
        """Get allowed performatives."""
        return set(self.speech_acts_definition.keys())

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
    def contents(self) -> Dict:
        """Get the contents of the message."""
        assert self.is_set("contents"), "contents is not set"
        return cast(Dict, self.get("contents"))

    @property
    def query(self) -> DataModel:
        """Get 'query' from the contents of the message."""
        assert self.is_set("query"), "\'query\' is not set"
        return cast(DataModel, self.get("query"))

    @property
    def price(self) -> float:
        """Get 'price' from the contents of the message."""
        assert self.is_set("price"), "\'price\' is not set"
        return cast(float, self.get("price"))

    def check_consistency(self) -> bool:
        """Check that the message follows the two_party_negotiation protocol."""
        try:
            assert isinstance(self.dialogue_reference, Tuple)
            assert isinstance(self.dialogue_reference[0], str) and isinstance(self.dialogue_reference[1], str)
            assert type(self.message_id) == int, "message_id must be 'int' but it is not."
            assert type(self.target) == int, "target must be 'int' but it is not."
            assert type(self.performative) == str, "performative must be 'str' but it is not."
            assert type(self.contents) == dict, "contents must be a 'Dict' but it is not"

            # Light Protocol 2
            # Check correct performative
            assert self.performative in self.performatives_definition, "'{}' is not in the list of allowed performative".format(self.performative)

            # Check correct contents
            contents_definition = self.speech_acts_definition[self.performative]
            # Number of contents
            assert len(self.contents) == len(contents_definition), "Incorrect number of contents. Expected {} contents. Found {}".format(len(self.contents), len(contents_definition))
            # Name and type of each content
            for content_name, content_value in self.contents:
                assert isinstance(content_name, str), "Incorrect type for content name '{}'. Expected 'str'.".format(str(content_name))
                assert content_name in contents_definition.keys(), "Incorrect content '{}'".format(content_name)
                assert isinstance(content_value, contents_definition[content_name]), "Incorrect content type for '{}'. Expected {}. Found {}.".format(content_name, contents_definition[content_name], type(content_value))

            # Light Protocol 3
            if self.message_id == 1:
                assert self.target == 0, "Expected target to be 0 when message_id is 1. Found {}.".format(self.target)
            else:
                assert 0 < self.target < self.message_id, "Expected target to be between 1 to (message_id -1) inclusive. Found {}".format(self.target)
        except (AssertionError, ValueError, KeyError) as e:
            print(str(e))
            return False

        return True
