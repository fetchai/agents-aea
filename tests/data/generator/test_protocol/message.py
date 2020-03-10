# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2020 fetchai
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""This module contains test_protocol's message definition."""

from enum import Enum
from typing import Dict, FrozenSet, Optional, Set, Tuple, Union, cast

from aea.configurations.base import ProtocolId
from aea.protocols.base import Message

from tests.data.generator.test_protocol.custom_types import DataModel

DEFAULT_BODY_SIZE = 4


class TestProtocolMessage(Message):
    """A protocol for testing purposes."""

    protocol_id = ProtocolId("fetchai", "test_protocol", "0.1.0")

    DataModel = DataModel

    class Performative(Enum):
        """Performatives for the test_protocol protocol."""

        PERFORMATIVE_CT = "performative_ct"
        PERFORMATIVE_EMPTY_CONTENTS = "performative_empty_contents"
        PERFORMATIVE_MT = "performative_mt"
        PERFORMATIVE_O = "performative_o"
        PERFORMATIVE_PCT = "performative_pct"
        PERFORMATIVE_PMT = "performative_pmt"
        PERFORMATIVE_PT = "performative_pt"

        def __str__(self):
            """Get the string representation."""
            return self.value

    def __init__(
        self,
        dialogue_reference: Tuple[str, str],
        message_id: int,
        target: int,
        performative: Performative,
        **kwargs,
    ):
        """
        Initialise an instance of TestProtocolMessage.

        :param message_id: the message id.
        :param dialogue_reference: the dialogue reference.
        :param target: the message target.
        :param performative: the message performative.
        """
        super().__init__(
            dialogue_reference=dialogue_reference,
            message_id=message_id,
            target=target,
            performative=TestProtocolMessage.Performative(performative),
            **kwargs,
        )
        self._performatives = {
            "performative_ct",
            "performative_empty_contents",
            "performative_mt",
            "performative_o",
            "performative_pct",
            "performative_pmt",
            "performative_pt",
        }
        assert (
            self._is_consistent()
        ), "This message is invalid according to the 'test_protocol' protocol."

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
        return cast(TestProtocolMessage.Performative, self.get("performative"))

    @property
    def target(self) -> int:
        """Get the target of the message."""
        assert self.is_set("target"), "target is not set."
        return cast(int, self.get("target"))

    @property
    def content_bool(self) -> bool:
        """Get the 'content_bool' content from the message."""
        assert self.is_set("content_bool"), "'content_bool' content is not set."
        return cast(bool, self.get("content_bool"))

    @property
    def content_bytes(self) -> bytes:
        """Get the 'content_bytes' content from the message."""
        assert self.is_set("content_bytes"), "'content_bytes' content is not set."
        return cast(bytes, self.get("content_bytes"))

    @property
    def content_ct(self) -> DataModel:
        """Get the 'content_ct' content from the message."""
        assert self.is_set("content_ct"), "'content_ct' content is not set."
        return cast(DataModel, self.get("content_ct"))

    @property
    def content_dict_bool_int(self) -> Dict[bool, bytes]:
        """Get the 'content_dict_bool_int' content from the message."""
        assert self.is_set(
            "content_dict_bool_int"
        ), "'content_dict_bool_int' content is not set."
        return cast(Dict[bool, bytes], self.get("content_dict_bool_int"))

    @property
    def content_dict_int_ct(self) -> Dict[int, DataModel]:
        """Get the 'content_dict_int_ct' content from the message."""
        assert self.is_set(
            "content_dict_int_ct"
        ), "'content_dict_int_ct' content is not set."
        return cast(Dict[int, DataModel], self.get("content_dict_int_ct"))

    @property
    def content_dict_str_float(self) -> Dict[str, float]:
        """Get the 'content_dict_str_float' content from the message."""
        assert self.is_set(
            "content_dict_str_float"
        ), "'content_dict_str_float' content is not set."
        return cast(Dict[str, float], self.get("content_dict_str_float"))

    @property
    def content_float(self) -> float:
        """Get the 'content_float' content from the message."""
        assert self.is_set("content_float"), "'content_float' content is not set."
        return cast(float, self.get("content_float"))

    @property
    def content_int(self) -> int:
        """Get the 'content_int' content from the message."""
        assert self.is_set("content_int"), "'content_int' content is not set."
        return cast(int, self.get("content_int"))

    @property
    def content_list_bool(self) -> Tuple[bool, ...]:
        """Get the 'content_list_bool' content from the message."""
        assert self.is_set(
            "content_list_bool"
        ), "'content_list_bool' content is not set."
        return cast(Tuple[bool, ...], self.get("content_list_bool"))

    @property
    def content_list_bytes(self) -> Tuple[bytes, ...]:
        """Get the 'content_list_bytes' content from the message."""
        assert self.is_set(
            "content_list_bytes"
        ), "'content_list_bytes' content is not set."
        return cast(Tuple[bytes, ...], self.get("content_list_bytes"))

    @property
    def content_list_ct(self) -> Tuple[DataModel, ...]:
        """Get the 'content_list_ct' content from the message."""
        assert self.is_set("content_list_ct"), "'content_list_ct' content is not set."
        return cast(Tuple[DataModel, ...], self.get("content_list_ct"))

    @property
    def content_list_float(self) -> Tuple[float, ...]:
        """Get the 'content_list_float' content from the message."""
        assert self.is_set(
            "content_list_float"
        ), "'content_list_float' content is not set."
        return cast(Tuple[float, ...], self.get("content_list_float"))

    @property
    def content_list_int(self) -> Tuple[int, ...]:
        """Get the 'content_list_int' content from the message."""
        assert self.is_set("content_list_int"), "'content_list_int' content is not set."
        return cast(Tuple[int, ...], self.get("content_list_int"))

    @property
    def content_list_str(self) -> Tuple[str, ...]:
        """Get the 'content_list_str' content from the message."""
        assert self.is_set("content_list_str"), "'content_list_str' content is not set."
        return cast(Tuple[str, ...], self.get("content_list_str"))

    @property
    def content_o_bool(self) -> Optional[bool]:
        """Get the 'content_o_bool' content from the message."""
        assert self.is_set("content_o_bool"), "'content_o_bool' content is not set."
        return cast(Optional[bool], self.get("content_o_bool"))

    @property
    def content_o_ct(self) -> Optional[DataModel]:
        """Get the 'content_o_ct' content from the message."""
        assert self.is_set("content_o_ct"), "'content_o_ct' content is not set."
        return cast(Optional[DataModel], self.get("content_o_ct"))

    @property
    def content_o_dict_str_int(self) -> Optional[Dict[str, int]]:
        """Get the 'content_o_dict_str_int' content from the message."""
        assert self.is_set(
            "content_o_dict_str_int"
        ), "'content_o_dict_str_int' content is not set."
        return cast(Optional[Dict[str, int]], self.get("content_o_dict_str_int"))

    @property
    def content_o_list_bytes(self) -> Optional[Tuple[bytes, ...]]:
        """Get the 'content_o_list_bytes' content from the message."""
        assert self.is_set(
            "content_o_list_bytes"
        ), "'content_o_list_bytes' content is not set."
        return cast(Optional[Tuple[bytes, ...]], self.get("content_o_list_bytes"))

    @property
    def content_o_set_float(self) -> Optional[FrozenSet[float]]:
        """Get the 'content_o_set_float' content from the message."""
        assert self.is_set(
            "content_o_set_float"
        ), "'content_o_set_float' content is not set."
        return cast(Optional[FrozenSet[float]], self.get("content_o_set_float"))

    @property
    def content_o_union(
        self,
    ) -> Optional[Union[str, Dict[str, int], FrozenSet[DataModel], Dict[str, float]]]:
        """Get the 'content_o_union' content from the message."""
        assert self.is_set("content_o_union"), "'content_o_union' content is not set."
        return cast(
            Optional[
                Union[str, Dict[str, int], FrozenSet[DataModel], Dict[str, float]]
            ],
            self.get("content_o_union"),
        )

    @property
    def content_set_bool(self) -> FrozenSet[bool]:
        """Get the 'content_set_bool' content from the message."""
        assert self.is_set("content_set_bool"), "'content_set_bool' content is not set."
        return cast(FrozenSet[bool], self.get("content_set_bool"))

    @property
    def content_set_bytes(self) -> FrozenSet[bytes]:
        """Get the 'content_set_bytes' content from the message."""
        assert self.is_set(
            "content_set_bytes"
        ), "'content_set_bytes' content is not set."
        return cast(FrozenSet[bytes], self.get("content_set_bytes"))

    @property
    def content_set_ct(self) -> FrozenSet[DataModel]:
        """Get the 'content_set_ct' content from the message."""
        assert self.is_set("content_set_ct"), "'content_set_ct' content is not set."
        return cast(FrozenSet[DataModel], self.get("content_set_ct"))

    @property
    def content_set_float(self) -> FrozenSet[float]:
        """Get the 'content_set_float' content from the message."""
        assert self.is_set(
            "content_set_float"
        ), "'content_set_float' content is not set."
        return cast(FrozenSet[float], self.get("content_set_float"))

    @property
    def content_set_int(self) -> FrozenSet[int]:
        """Get the 'content_set_int' content from the message."""
        assert self.is_set("content_set_int"), "'content_set_int' content is not set."
        return cast(FrozenSet[int], self.get("content_set_int"))

    @property
    def content_set_str(self) -> FrozenSet[str]:
        """Get the 'content_set_str' content from the message."""
        assert self.is_set("content_set_str"), "'content_set_str' content is not set."
        return cast(FrozenSet[str], self.get("content_set_str"))

    @property
    def content_str(self) -> str:
        """Get the 'content_str' content from the message."""
        assert self.is_set("content_str"), "'content_str' content is not set."
        return cast(str, self.get("content_str"))

    @property
    def content_union(
        self,
    ) -> Union[
        DataModel,
        bytes,
        int,
        float,
        bool,
        str,
        FrozenSet[int],
        Tuple[DataModel, ...],
        Dict[str, DataModel],
    ]:
        """Get the 'content_union' content from the message."""
        assert self.is_set("content_union"), "'content_union' content is not set."
        return cast(
            Union[
                DataModel,
                bytes,
                int,
                float,
                bool,
                str,
                FrozenSet[int],
                Tuple[DataModel, ...],
                Dict[str, DataModel],
            ],
            self.get("content_union"),
        )

    def _is_consistent(self) -> bool:
        """Check that the message follows the test_protocol protocol."""
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

            # Light Protocol Rule 2
            # Check correct performative
            assert (
                type(self.performative) == TestProtocolMessage.Performative
            ), "'{}' is not in the list of valid performatives: {}".format(
                self.performative, self.valid_performatives
            )

            # Check correct contents
            actual_nb_of_contents = len(self.body) - DEFAULT_BODY_SIZE
            expected_nb_of_contents = 0
            if self.performative == TestProtocolMessage.Performative.PERFORMATIVE_CT:
                expected_nb_of_contents = 1
                assert (
                    type(self.content_ct) == DataModel
                ), "Content 'content_ct' is not of type 'DataModel'."
            elif self.performative == TestProtocolMessage.Performative.PERFORMATIVE_PT:
                expected_nb_of_contents = 5
                assert (
                    type(self.content_bytes) == bytes
                ), "Content 'content_bytes' is not of type 'bytes'."
                assert (
                    type(self.content_int) == int
                ), "Content 'content_int' is not of type 'int'."
                assert (
                    type(self.content_float) == float
                ), "Content 'content_float' is not of type 'float'."
                assert (
                    type(self.content_bool) == bool
                ), "Content 'content_bool' is not of type 'bool'."
                assert (
                    type(self.content_str) == str
                ), "Content 'content_str' is not of type 'str'."
            elif self.performative == TestProtocolMessage.Performative.PERFORMATIVE_PCT:
                expected_nb_of_contents = 12
                assert (
                    type(self.content_set_ct) == frozenset
                ), "Content 'content_set_ct' is not of type 'frozenset'."
                assert all(
                    type(element) == DataModel for element in self.content_set_ct
                ), "Elements of the content 'content_set_ct' are not of type 'DataModel'."
                assert (
                    type(self.content_set_bytes) == frozenset
                ), "Content 'content_set_bytes' is not of type 'frozenset'."
                assert all(
                    type(element) == bytes for element in self.content_set_bytes
                ), "Elements of the content 'content_set_bytes' are not of type 'bytes'."
                assert (
                    type(self.content_set_int) == frozenset
                ), "Content 'content_set_int' is not of type 'frozenset'."
                assert all(
                    type(element) == int for element in self.content_set_int
                ), "Elements of the content 'content_set_int' are not of type 'int'."
                assert (
                    type(self.content_set_float) == frozenset
                ), "Content 'content_set_float' is not of type 'frozenset'."
                assert all(
                    type(element) == float for element in self.content_set_float
                ), "Elements of the content 'content_set_float' are not of type 'float'."
                assert (
                    type(self.content_set_bool) == frozenset
                ), "Content 'content_set_bool' is not of type 'frozenset'."
                assert all(
                    type(element) == bool for element in self.content_set_bool
                ), "Elements of the content 'content_set_bool' are not of type 'bool'."
                assert (
                    type(self.content_set_str) == frozenset
                ), "Content 'content_set_str' is not of type 'frozenset'."
                assert all(
                    type(element) == str for element in self.content_set_str
                ), "Elements of the content 'content_set_str' are not of type 'str'."
                assert (
                    type(self.content_list_ct) == tuple
                ), "Content 'content_list_ct' is not of type 'tuple'."
                assert all(
                    type(element) == DataModel for element in self.content_list_ct
                ), "Elements of the content 'content_list_ct' are not of type 'DataModel'."
                assert (
                    type(self.content_list_bytes) == tuple
                ), "Content 'content_list_bytes' is not of type 'tuple'."
                assert all(
                    type(element) == bytes for element in self.content_list_bytes
                ), "Elements of the content 'content_list_bytes' are not of type 'bytes'."
                assert (
                    type(self.content_list_int) == tuple
                ), "Content 'content_list_int' is not of type 'tuple'."
                assert all(
                    type(element) == int for element in self.content_list_int
                ), "Elements of the content 'content_list_int' are not of type 'int'."
                assert (
                    type(self.content_list_float) == tuple
                ), "Content 'content_list_float' is not of type 'tuple'."
                assert all(
                    type(element) == float for element in self.content_list_float
                ), "Elements of the content 'content_list_float' are not of type 'float'."
                assert (
                    type(self.content_list_bool) == tuple
                ), "Content 'content_list_bool' is not of type 'tuple'."
                assert all(
                    type(element) == bool for element in self.content_list_bool
                ), "Elements of the content 'content_list_bool' are not of type 'bool'."
                assert (
                    type(self.content_list_str) == tuple
                ), "Content 'content_list_str' is not of type 'tuple'."
                assert all(
                    type(element) == str for element in self.content_list_str
                ), "Elements of the content 'content_list_str' are not of type 'str'."
            elif self.performative == TestProtocolMessage.Performative.PERFORMATIVE_PMT:
                expected_nb_of_contents = 3
                assert (
                    type(self.content_dict_int_ct) == dict
                ), "Content 'content_dict_int_ct' is not of type 'dict'."
                for key, value in self.content_dict_int_ct.items():
                    assert (
                        type(key) == int
                    ), "Keys of 'content_dict_int_ct' dictionary are not of type 'int'."
                    assert (
                        type(value) == DataModel
                    ), "Values of 'content_dict_int_ct' dictionary are not of type 'DataModel'."
                assert (
                    type(self.content_dict_bool_int) == dict
                ), "Content 'content_dict_bool_int' is not of type 'dict'."
                for key, value in self.content_dict_bool_int.items():
                    assert (
                        type(key) == bool
                    ), "Keys of 'content_dict_bool_int' dictionary are not of type 'bool'."
                    assert (
                        type(value) == bytes
                    ), "Values of 'content_dict_bool_int' dictionary are not of type 'bytes'."
                assert (
                    type(self.content_dict_str_float) == dict
                ), "Content 'content_dict_str_float' is not of type 'dict'."
                for key, value in self.content_dict_str_float.items():
                    assert (
                        type(key) == str
                    ), "Keys of 'content_dict_str_float' dictionary are not of type 'str'."
                    assert (
                        type(value) == float
                    ), "Values of 'content_dict_str_float' dictionary are not of type 'float'."
            elif self.performative == TestProtocolMessage.Performative.PERFORMATIVE_MT:
                expected_nb_of_contents = 1
                assert (
                    type(self.content_union) == DataModel
                    or type(self.content_union) == bool
                    or type(self.content_union) == bytes
                    or type(self.content_union) == dict
                    or type(self.content_union) == float
                    or type(self.content_union) == frozenset
                    or type(self.content_union) == int
                    or type(self.content_union) == str
                    or type(self.content_union) == tuple
                ), "Content 'content_union' should be either of the following types: ['DataModel', 'bool', 'bytes', 'dict', 'float', 'frozenset', 'int', 'str', 'tuple']."
                if type(self.content_union) == frozenset:
                    assert all(
                        type(element) == int for element in self.content_union
                    ), "Elements of the content 'content_union' should be of type 'int'."
                if type(self.content_union) == tuple:
                    assert all(
                        type(element) == DataModel for element in self.content_union
                    ), "Elements of the content 'content_union' should be of type 'CustomDataModel'."
                if type(self.content_union) == dict:
                    for key, value in self.content_union.items():
                        assert (
                            type(key) == str and type(value) == DataModel
                        ), "The type of keys and values of 'content_union' dictionary must be 'str' and 'DataModel' respectively."
            elif self.performative == TestProtocolMessage.Performative.PERFORMATIVE_O:
                expected_nb_of_contents = 0
                if self.is_set("content_o_ct"):
                    expected_nb_of_contents += 1
                    assert (
                        type(self.content_o_ct) == DataModel
                    ), "Content 'content_o_ct' is not of type 'DataModel'."
                if self.is_set("content_o_bool"):
                    expected_nb_of_contents += 1
                    assert (
                        type(self.content_o_bool) == bool
                    ), "Content 'content_o_bool' is not of type 'bool'."
                if self.is_set("content_o_set_float"):
                    expected_nb_of_contents += 1
                    assert (
                        type(self.content_o_set_float) == frozenset
                    ), "Content 'content_o_set_float' is not of type 'frozenset'."
                    assert all(
                        type(element) == float for element in self.content_o_set_float
                    ), "Elements of the content 'content_o_set_float' are not of type 'float'."
                if self.is_set("content_o_list_bytes"):
                    expected_nb_of_contents += 1
                    assert (
                        type(self.content_o_list_bytes) == tuple
                    ), "Content 'content_o_list_bytes' is not of type 'tuple'."
                    assert all(
                        type(element) == bytes for element in self.content_o_list_bytes
                    ), "Elements of the content 'content_o_list_bytes' are not of type 'bytes'."
                if self.is_set("content_o_dict_str_int"):
                    expected_nb_of_contents += 1
                    assert (
                        type(self.content_o_dict_str_int) == dict
                    ), "Content 'content_o_dict_str_int' is not of type 'dict'."
                    for key, value in self.content_o_dict_str_int.items():
                        assert (
                            type(key) == str
                        ), "Keys of 'content_o_dict_str_int' dictionary are not of type 'str'."
                        assert (
                            type(value) == int
                        ), "Values of 'content_o_dict_str_int' dictionary are not of type 'int'."
                if self.is_set("content_o_union"):
                    expected_nb_of_contents += 1
                    assert (
                        type(self.content_o_union) == dict
                        or type(self.content_o_union) == frozenset
                        or type(self.content_o_union) == str
                    ), "Content 'content_o_union' should be either of the following types: ['dict', 'frozenset', 'str']."
                    if type(self.content_o_union) == frozenset:
                        assert all(
                            type(element) == DataModel
                            for element in self.content_o_union
                        ), "Elements of the content 'content_o_union' should be of type 'CustomDataModel'."
                    if type(self.content_o_union) == dict:
                        for key, value in self.content_o_union.items():
                            assert (
                                type(key) == str and type(value) == float
                            ), "The type of keys and values of 'content_o_union' dictionary must be 'str' and 'float' respectively."
            elif (
                self.performative
                == TestProtocolMessage.Performative.PERFORMATIVE_EMPTY_CONTENTS
            ):
                expected_nb_of_contents = 0

            # Check correct content count
            assert (
                expected_nb_of_contents == actual_nb_of_contents
            ), "Incorrect number of contents. Expected {} contents. Found {}".format(
                expected_nb_of_contents, actual_nb_of_contents
            )

            # Light Protocol Rule 3
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
