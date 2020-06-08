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

"""This module contains t_protocol's message definition."""

import logging
from enum import Enum
from typing import Dict, FrozenSet, Optional, Set, Tuple, Union, cast

from aea.configurations.base import ProtocolId
from aea.protocols.base import Message

from tests.data.generator.t_protocol.custom_types import DataModel as CustomDataModel

logger = logging.getLogger("packages.fetchai.protocols.t_protocol.message")

DEFAULT_BODY_SIZE = 4


class TProtocolMessage(Message):
    """A protocol for testing purposes."""

    protocol_id = ProtocolId("fetchai", "t_protocol", "0.1.0")

    DataModel = CustomDataModel

    class Performative(Enum):
        """Performatives for the t_protocol protocol."""

        PERFORMATIVE_CT = "performative_ct"
        PERFORMATIVE_EMPTY_CONTENTS = "performative_empty_contents"
        PERFORMATIVE_MT = "performative_mt"
        PERFORMATIVE_O = "performative_o"
        PERFORMATIVE_PCT = "performative_pct"
        PERFORMATIVE_PMT = "performative_pmt"
        PERFORMATIVE_PT = "performative_pt"

        def __str__(self):
            """Get the string representation."""
            return str(self.value)

    def __init__(
        self,
        performative: Performative,
        dialogue_reference: Tuple[str, str] = ("", ""),
        message_id: int = 1,
        target: int = 0,
        **kwargs,
    ):
        """
        Initialise an instance of TProtocolMessage.

        :param message_id: the message id.
        :param dialogue_reference: the dialogue reference.
        :param target: the message target.
        :param performative: the message performative.
        """
        super().__init__(
            dialogue_reference=dialogue_reference,
            message_id=message_id,
            target=target,
            performative=TProtocolMessage.Performative(performative),
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
        return cast(TProtocolMessage.Performative, self.get("performative"))

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
    def content_ct(self) -> CustomDataModel:
        """Get the 'content_ct' content from the message."""
        assert self.is_set("content_ct"), "'content_ct' content is not set."
        return cast(CustomDataModel, self.get("content_ct"))

    @property
    def content_dict_bool_bytes(self) -> Dict[bool, bytes]:
        """Get the 'content_dict_bool_bytes' content from the message."""
        assert self.is_set(
            "content_dict_bool_bytes"
        ), "'content_dict_bool_bytes' content is not set."
        return cast(Dict[bool, bytes], self.get("content_dict_bool_bytes"))

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
        return cast(Optional[bool], self.get("content_o_bool"))

    @property
    def content_o_ct(self) -> Optional[CustomDataModel]:
        """Get the 'content_o_ct' content from the message."""
        return cast(Optional[CustomDataModel], self.get("content_o_ct"))

    @property
    def content_o_dict_str_int(self) -> Optional[Dict[str, int]]:
        """Get the 'content_o_dict_str_int' content from the message."""
        return cast(Optional[Dict[str, int]], self.get("content_o_dict_str_int"))

    @property
    def content_o_list_bytes(self) -> Optional[Tuple[bytes, ...]]:
        """Get the 'content_o_list_bytes' content from the message."""
        return cast(Optional[Tuple[bytes, ...]], self.get("content_o_list_bytes"))

    @property
    def content_o_set_float(self) -> Optional[FrozenSet[float]]:
        """Get the 'content_o_set_float' content from the message."""
        return cast(Optional[FrozenSet[float]], self.get("content_o_set_float"))

    @property
    def content_o_union(
        self,
    ) -> Optional[
        Union[
            str,
            Dict[str, int],
            FrozenSet[int],
            FrozenSet[bytes],
            Tuple[bool, ...],
            Dict[str, float],
        ]
    ]:
        """Get the 'content_o_union' content from the message."""
        return cast(
            Optional[
                Union[
                    str,
                    Dict[str, int],
                    FrozenSet[int],
                    FrozenSet[bytes],
                    Tuple[bool, ...],
                    Dict[str, float],
                ]
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
    def content_union_1(
        self,
    ) -> Union[
        CustomDataModel,
        bytes,
        int,
        float,
        bool,
        str,
        FrozenSet[int],
        Tuple[bool, ...],
        Dict[str, int],
    ]:
        """Get the 'content_union_1' content from the message."""
        assert self.is_set("content_union_1"), "'content_union_1' content is not set."
        return cast(
            Union[
                CustomDataModel,
                bytes,
                int,
                float,
                bool,
                str,
                FrozenSet[int],
                Tuple[bool, ...],
                Dict[str, int],
            ],
            self.get("content_union_1"),
        )

    @property
    def content_union_2(
        self,
    ) -> Union[
        FrozenSet[bytes],
        FrozenSet[int],
        FrozenSet[str],
        Tuple[float, ...],
        Tuple[bool, ...],
        Tuple[bytes, ...],
        Dict[str, int],
        Dict[int, float],
        Dict[bool, bytes],
    ]:
        """Get the 'content_union_2' content from the message."""
        assert self.is_set("content_union_2"), "'content_union_2' content is not set."
        return cast(
            Union[
                FrozenSet[bytes],
                FrozenSet[int],
                FrozenSet[str],
                Tuple[float, ...],
                Tuple[bool, ...],
                Tuple[bytes, ...],
                Dict[str, int],
                Dict[int, float],
                Dict[bool, bytes],
            ],
            self.get("content_union_2"),
        )

    def _is_consistent(self) -> bool:
        """Check that the message follows the t_protocol protocol."""
        try:
            assert (
                type(self.dialogue_reference) == tuple
            ), "Invalid type for 'dialogue_reference'. Expected 'tuple'. Found '{}'.".format(
                type(self.dialogue_reference)
            )
            assert (
                type(self.dialogue_reference[0]) == str
            ), "Invalid type for 'dialogue_reference[0]'. Expected 'str'. Found '{}'.".format(
                type(self.dialogue_reference[0])
            )
            assert (
                type(self.dialogue_reference[1]) == str
            ), "Invalid type for 'dialogue_reference[1]'. Expected 'str'. Found '{}'.".format(
                type(self.dialogue_reference[1])
            )
            assert (
                type(self.message_id) == int
            ), "Invalid type for 'message_id'. Expected 'int'. Found '{}'.".format(
                type(self.message_id)
            )
            assert (
                type(self.target) == int
            ), "Invalid type for 'target'. Expected 'int'. Found '{}'.".format(
                type(self.target)
            )

            # Light Protocol Rule 2
            # Check correct performative
            assert (
                type(self.performative) == TProtocolMessage.Performative
            ), "Invalid 'performative'. Expected either of '{}'. Found '{}'.".format(
                self.valid_performatives, self.performative
            )

            # Check correct contents
            actual_nb_of_contents = len(self.body) - DEFAULT_BODY_SIZE
            expected_nb_of_contents = 0
            if self.performative == TProtocolMessage.Performative.PERFORMATIVE_CT:
                expected_nb_of_contents = 1
                assert (
                    type(self.content_ct) == CustomDataModel
                ), "Invalid type for content 'content_ct'. Expected 'DataModel'. Found '{}'.".format(
                    type(self.content_ct)
                )
            elif self.performative == TProtocolMessage.Performative.PERFORMATIVE_PT:
                expected_nb_of_contents = 5
                assert (
                    type(self.content_bytes) == bytes
                ), "Invalid type for content 'content_bytes'. Expected 'bytes'. Found '{}'.".format(
                    type(self.content_bytes)
                )
                assert (
                    type(self.content_int) == int
                ), "Invalid type for content 'content_int'. Expected 'int'. Found '{}'.".format(
                    type(self.content_int)
                )
                assert (
                    type(self.content_float) == float
                ), "Invalid type for content 'content_float'. Expected 'float'. Found '{}'.".format(
                    type(self.content_float)
                )
                assert (
                    type(self.content_bool) == bool
                ), "Invalid type for content 'content_bool'. Expected 'bool'. Found '{}'.".format(
                    type(self.content_bool)
                )
                assert (
                    type(self.content_str) == str
                ), "Invalid type for content 'content_str'. Expected 'str'. Found '{}'.".format(
                    type(self.content_str)
                )
            elif self.performative == TProtocolMessage.Performative.PERFORMATIVE_PCT:
                expected_nb_of_contents = 10
                assert (
                    type(self.content_set_bytes) == frozenset
                ), "Invalid type for content 'content_set_bytes'. Expected 'frozenset'. Found '{}'.".format(
                    type(self.content_set_bytes)
                )
                assert all(
                    type(element) == bytes for element in self.content_set_bytes
                ), "Invalid type for frozenset elements in content 'content_set_bytes'. Expected 'bytes'."
                assert (
                    type(self.content_set_int) == frozenset
                ), "Invalid type for content 'content_set_int'. Expected 'frozenset'. Found '{}'.".format(
                    type(self.content_set_int)
                )
                assert all(
                    type(element) == int for element in self.content_set_int
                ), "Invalid type for frozenset elements in content 'content_set_int'. Expected 'int'."
                assert (
                    type(self.content_set_float) == frozenset
                ), "Invalid type for content 'content_set_float'. Expected 'frozenset'. Found '{}'.".format(
                    type(self.content_set_float)
                )
                assert all(
                    type(element) == float for element in self.content_set_float
                ), "Invalid type for frozenset elements in content 'content_set_float'. Expected 'float'."
                assert (
                    type(self.content_set_bool) == frozenset
                ), "Invalid type for content 'content_set_bool'. Expected 'frozenset'. Found '{}'.".format(
                    type(self.content_set_bool)
                )
                assert all(
                    type(element) == bool for element in self.content_set_bool
                ), "Invalid type for frozenset elements in content 'content_set_bool'. Expected 'bool'."
                assert (
                    type(self.content_set_str) == frozenset
                ), "Invalid type for content 'content_set_str'. Expected 'frozenset'. Found '{}'.".format(
                    type(self.content_set_str)
                )
                assert all(
                    type(element) == str for element in self.content_set_str
                ), "Invalid type for frozenset elements in content 'content_set_str'. Expected 'str'."
                assert (
                    type(self.content_list_bytes) == tuple
                ), "Invalid type for content 'content_list_bytes'. Expected 'tuple'. Found '{}'.".format(
                    type(self.content_list_bytes)
                )
                assert all(
                    type(element) == bytes for element in self.content_list_bytes
                ), "Invalid type for tuple elements in content 'content_list_bytes'. Expected 'bytes'."
                assert (
                    type(self.content_list_int) == tuple
                ), "Invalid type for content 'content_list_int'. Expected 'tuple'. Found '{}'.".format(
                    type(self.content_list_int)
                )
                assert all(
                    type(element) == int for element in self.content_list_int
                ), "Invalid type for tuple elements in content 'content_list_int'. Expected 'int'."
                assert (
                    type(self.content_list_float) == tuple
                ), "Invalid type for content 'content_list_float'. Expected 'tuple'. Found '{}'.".format(
                    type(self.content_list_float)
                )
                assert all(
                    type(element) == float for element in self.content_list_float
                ), "Invalid type for tuple elements in content 'content_list_float'. Expected 'float'."
                assert (
                    type(self.content_list_bool) == tuple
                ), "Invalid type for content 'content_list_bool'. Expected 'tuple'. Found '{}'.".format(
                    type(self.content_list_bool)
                )
                assert all(
                    type(element) == bool for element in self.content_list_bool
                ), "Invalid type for tuple elements in content 'content_list_bool'. Expected 'bool'."
                assert (
                    type(self.content_list_str) == tuple
                ), "Invalid type for content 'content_list_str'. Expected 'tuple'. Found '{}'.".format(
                    type(self.content_list_str)
                )
                assert all(
                    type(element) == str for element in self.content_list_str
                ), "Invalid type for tuple elements in content 'content_list_str'. Expected 'str'."
            elif self.performative == TProtocolMessage.Performative.PERFORMATIVE_PMT:
                expected_nb_of_contents = 2
                assert (
                    type(self.content_dict_bool_bytes) == dict
                ), "Invalid type for content 'content_dict_bool_bytes'. Expected 'dict'. Found '{}'.".format(
                    type(self.content_dict_bool_bytes)
                )
                for (
                    key_of_content_dict_bool_bytes,
                    value_of_content_dict_bool_bytes,
                ) in self.content_dict_bool_bytes.items():
                    assert (
                        type(key_of_content_dict_bool_bytes) == bool
                    ), "Invalid type for dictionary keys in content 'content_dict_bool_bytes'. Expected 'bool'. Found '{}'.".format(
                        type(key_of_content_dict_bool_bytes)
                    )
                    assert (
                        type(value_of_content_dict_bool_bytes) == bytes
                    ), "Invalid type for dictionary values in content 'content_dict_bool_bytes'. Expected 'bytes'. Found '{}'.".format(
                        type(value_of_content_dict_bool_bytes)
                    )
                assert (
                    type(self.content_dict_str_float) == dict
                ), "Invalid type for content 'content_dict_str_float'. Expected 'dict'. Found '{}'.".format(
                    type(self.content_dict_str_float)
                )
                for (
                    key_of_content_dict_str_float,
                    value_of_content_dict_str_float,
                ) in self.content_dict_str_float.items():
                    assert (
                        type(key_of_content_dict_str_float) == str
                    ), "Invalid type for dictionary keys in content 'content_dict_str_float'. Expected 'str'. Found '{}'.".format(
                        type(key_of_content_dict_str_float)
                    )
                    assert (
                        type(value_of_content_dict_str_float) == float
                    ), "Invalid type for dictionary values in content 'content_dict_str_float'. Expected 'float'. Found '{}'.".format(
                        type(value_of_content_dict_str_float)
                    )
            elif self.performative == TProtocolMessage.Performative.PERFORMATIVE_MT:
                expected_nb_of_contents = 2
                assert (
                    type(self.content_union_1) == CustomDataModel
                    or type(self.content_union_1) == bool
                    or type(self.content_union_1) == bytes
                    or type(self.content_union_1) == dict
                    or type(self.content_union_1) == float
                    or type(self.content_union_1) == frozenset
                    or type(self.content_union_1) == int
                    or type(self.content_union_1) == str
                    or type(self.content_union_1) == tuple
                ), "Invalid type for content 'content_union_1'. Expected either of '['DataModel', 'bool', 'bytes', 'dict', 'float', 'frozenset', 'int', 'str', 'tuple']'. Found '{}'.".format(
                    type(self.content_union_1)
                )
                if type(self.content_union_1) == frozenset:
                    assert all(
                        type(element) == int for element in self.content_union_1
                    ), "Invalid type for elements of content 'content_union_1'. Expected 'int'."
                if type(self.content_union_1) == tuple:
                    assert all(
                        type(element) == bool for element in self.content_union_1
                    ), "Invalid type for tuple elements in content 'content_union_1'. Expected 'bool'."
                if type(self.content_union_1) == dict:
                    for (
                        key_of_content_union_1,
                        value_of_content_union_1,
                    ) in self.content_union_1.items():
                        assert (
                            type(key_of_content_union_1) == str
                            and type(value_of_content_union_1) == int
                        ), "Invalid type for dictionary key, value in content 'content_union_1'. Expected 'str', 'int'."
                assert (
                    type(self.content_union_2) == dict
                    or type(self.content_union_2) == frozenset
                    or type(self.content_union_2) == tuple
                ), "Invalid type for content 'content_union_2'. Expected either of '['dict', 'frozenset', 'tuple']'. Found '{}'.".format(
                    type(self.content_union_2)
                )
                if type(self.content_union_2) == frozenset:
                    assert (
                        all(type(element) == bytes for element in self.content_union_2)
                        or all(type(element) == int for element in self.content_union_2)
                        or all(type(element) == str for element in self.content_union_2)
                    ), "Invalid type for frozenset elements in content 'content_union_2'. Expected either 'bytes' or 'int' or 'str'."
                if type(self.content_union_2) == tuple:
                    assert (
                        all(type(element) == bool for element in self.content_union_2)
                        or all(
                            type(element) == bytes for element in self.content_union_2
                        )
                        or all(
                            type(element) == float for element in self.content_union_2
                        )
                    ), "Invalid type for tuple elements in content 'content_union_2'. Expected either 'bool' or 'bytes' or 'float'."
                if type(self.content_union_2) == dict:
                    for (
                        key_of_content_union_2,
                        value_of_content_union_2,
                    ) in self.content_union_2.items():
                        assert (
                            (
                                type(key_of_content_union_2) == bool
                                and type(value_of_content_union_2) == bytes
                            )
                            or (
                                type(key_of_content_union_2) == int
                                and type(value_of_content_union_2) == float
                            )
                            or (
                                type(key_of_content_union_2) == str
                                and type(value_of_content_union_2) == int
                            )
                        ), "Invalid type for dictionary key, value in content 'content_union_2'. Expected 'bool','bytes' or 'int','float' or 'str','int'."
            elif self.performative == TProtocolMessage.Performative.PERFORMATIVE_O:
                expected_nb_of_contents = 0
                if self.is_set("content_o_ct"):
                    expected_nb_of_contents += 1
                    content_o_ct = cast(CustomDataModel, self.content_o_ct)
                    assert (
                        type(content_o_ct) == CustomDataModel
                    ), "Invalid type for content 'content_o_ct'. Expected 'DataModel'. Found '{}'.".format(
                        type(content_o_ct)
                    )
                if self.is_set("content_o_bool"):
                    expected_nb_of_contents += 1
                    content_o_bool = cast(bool, self.content_o_bool)
                    assert (
                        type(content_o_bool) == bool
                    ), "Invalid type for content 'content_o_bool'. Expected 'bool'. Found '{}'.".format(
                        type(content_o_bool)
                    )
                if self.is_set("content_o_set_float"):
                    expected_nb_of_contents += 1
                    content_o_set_float = cast(
                        FrozenSet[float], self.content_o_set_float
                    )
                    assert (
                        type(content_o_set_float) == frozenset
                    ), "Invalid type for content 'content_o_set_float'. Expected 'frozenset'. Found '{}'.".format(
                        type(content_o_set_float)
                    )
                    assert all(
                        type(element) == float for element in content_o_set_float
                    ), "Invalid type for frozenset elements in content 'content_o_set_float'. Expected 'float'."
                if self.is_set("content_o_list_bytes"):
                    expected_nb_of_contents += 1
                    content_o_list_bytes = cast(
                        Tuple[bytes, ...], self.content_o_list_bytes
                    )
                    assert (
                        type(content_o_list_bytes) == tuple
                    ), "Invalid type for content 'content_o_list_bytes'. Expected 'tuple'. Found '{}'.".format(
                        type(content_o_list_bytes)
                    )
                    assert all(
                        type(element) == bytes for element in content_o_list_bytes
                    ), "Invalid type for tuple elements in content 'content_o_list_bytes'. Expected 'bytes'."
                if self.is_set("content_o_dict_str_int"):
                    expected_nb_of_contents += 1
                    content_o_dict_str_int = cast(
                        Dict[str, int], self.content_o_dict_str_int
                    )
                    assert (
                        type(content_o_dict_str_int) == dict
                    ), "Invalid type for content 'content_o_dict_str_int'. Expected 'dict'. Found '{}'.".format(
                        type(content_o_dict_str_int)
                    )
                    for (
                        key_of_content_o_dict_str_int,
                        value_of_content_o_dict_str_int,
                    ) in content_o_dict_str_int.items():
                        assert (
                            type(key_of_content_o_dict_str_int) == str
                        ), "Invalid type for dictionary keys in content 'content_o_dict_str_int'. Expected 'str'. Found '{}'.".format(
                            type(key_of_content_o_dict_str_int)
                        )
                        assert (
                            type(value_of_content_o_dict_str_int) == int
                        ), "Invalid type for dictionary values in content 'content_o_dict_str_int'. Expected 'int'. Found '{}'.".format(
                            type(value_of_content_o_dict_str_int)
                        )
                if self.is_set("content_o_union"):
                    expected_nb_of_contents += 1
                    content_o_union = cast(
                        Union[
                            str,
                            Dict[str, int],
                            FrozenSet[int],
                            FrozenSet[bytes],
                            Tuple[bool, ...],
                            Dict[str, float],
                        ],
                        self.content_o_union,
                    )
                    assert (
                        type(content_o_union) == dict
                        or type(content_o_union) == frozenset
                        or type(content_o_union) == str
                        or type(content_o_union) == tuple
                    ), "Invalid type for content 'content_o_union'. Expected either of '['dict', 'frozenset', 'str', 'tuple']'. Found '{}'.".format(
                        type(content_o_union)
                    )
                    if type(content_o_union) == frozenset:
                        assert all(
                            type(element) == bytes for element in content_o_union
                        ) or all(
                            type(element) == int for element in content_o_union
                        ), "Invalid type for frozenset elements in content 'content_o_union'. Expected either 'bytes' or 'int'."
                    if type(content_o_union) == tuple:
                        assert all(
                            type(element) == bool for element in content_o_union
                        ), "Invalid type for tuple elements in content 'content_o_union'. Expected 'bool'."
                    if type(content_o_union) == dict:
                        for (
                            key_of_content_o_union,
                            value_of_content_o_union,
                        ) in content_o_union.items():
                            assert (
                                type(key_of_content_o_union) == str
                                and type(value_of_content_o_union) == float
                            ), "Invalid type for dictionary key, value in content 'content_o_union'. Expected 'str', 'float'."
            elif (
                self.performative
                == TProtocolMessage.Performative.PERFORMATIVE_EMPTY_CONTENTS
            ):
                expected_nb_of_contents = 0

            # Check correct content count
            assert (
                expected_nb_of_contents == actual_nb_of_contents
            ), "Incorrect number of contents. Expected {}. Found {}".format(
                expected_nb_of_contents, actual_nb_of_contents
            )

            # Light Protocol Rule 3
            if self.message_id == 1:
                assert (
                    self.target == 0
                ), "Invalid 'target'. Expected 0 (because 'message_id' is 1). Found {}.".format(
                    self.target
                )
            else:
                assert (
                    0 < self.target < self.message_id
                ), "Invalid 'target'. Expected an integer between 1 and {} inclusive. Found {}.".format(
                    self.message_id - 1, self.target,
                )
        except (AssertionError, ValueError, KeyError) as e:
            logger.error(str(e))
            return False

        return True
