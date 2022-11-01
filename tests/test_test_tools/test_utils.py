# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""Test utilities."""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Type
from unittest import mock

import pytest

from aea.test_tools import utils
from aea.test_tools.utils import copy_class, remove_test_directory, wait_for_condition


def test_wait_for_condition():
    """Test test_wait_for_condition"""

    wait_for_condition(lambda: True)
    with pytest.raises(TimeoutError, match="test error msg"):
        wait_for_condition(lambda: False, error_msg="test error msg")


class TestCopyClass:
    """Test copy_class"""

    cls: Type
    copy_of_cls: Type

    def setup(self):
        """Setup"""

        # redefine for each test
        class Parent:
            """Parent"""

            def __init__(self):
                self.x = self._y = None
                self.attr = "attr"
                self.mutable_attr = []

        class Child(Parent):
            """Child"""

            cls_attr = "cls_attr"
            cls_mutable_attr = []

            def __init__(self):
                super().__init__()

            @classmethod
            def cls_method(cls, x):
                cls.x = x

            def method(self, y):
                """F"""
                self._y = y

            @property
            def y(self):
                return self._y

        self.cls = Child
        self.copy_of_cls = copy_class(Child)

    @pytest.mark.parametrize("mutate_original", [False, True])
    def test_cls(self, mutate_original: bool):
        """Test cls"""

        original, replica = self.cls, self.copy_of_cls
        a, b = (original, replica) if mutate_original else (replica, original)

        assert a is not b
        assert a != b
        assert a.cls_attr == b.cls_attr
        assert a.cls_mutable_attr == b.cls_mutable_attr

        # mutate state
        assert not hasattr(a, "x")
        a.cls_method(3)
        assert hasattr(a, "x")
        a.cls_mutable_attr.append(1)
        assert a.cls_mutable_attr
        assert not b.cls_mutable_attr

        # if we set the attribute on the original (parent class),
        # the replicate (child) will also have it.
        a.new_attr = "new_attr"
        a.g = lambda: None
        if not mutate_original:
            assert not hasattr(b, "x")
            assert not hasattr(b, "new_attr")
            assert not hasattr(b, "g")

    @pytest.mark.parametrize("mutate_original", [False, True])
    def test_instance(self, mutate_original: bool):
        """Test instance"""

        original, replica = self.cls(), self.copy_of_cls()
        a, b = (original, replica) if mutate_original else (replica, original)

        assert a is not b
        assert a != b
        assert a.cls_attr == b.cls_attr
        assert a.cls_mutable_attr == b.cls_mutable_attr

        # mutate state
        assert hasattr(a, "x") and hasattr(b, "x")  # set in __init__
        a.cls_method(3)
        assert a.x is b.x is None  # class method does not affect instance

        a.method(3)
        assert a.y == 3
        assert b.y is None

        a.cls_mutable_attr.append(1)
        assert a.cls_mutable_attr
        assert not b.cls_mutable_attr

        # mutating instance attributes in not heritable
        a.new_attr = "new_attr"
        a.g = lambda: None
        assert not hasattr(b, "new_attr")
        assert not hasattr(b, "g")


@pytest.mark.parametrize("path_type", [str, Path])
def test_remove_non_empty_test_directory(path_type):
    """Test remove_test_directory"""

    tmp_dir = path_type(tempfile.TemporaryDirectory().name)
    assert not os.path.exists(tmp_dir)
    shutil.copytree(str(Path(utils.__file__).parent), tmp_dir)
    assert os.path.isdir(tmp_dir)
    assert list(Path(tmp_dir).glob("*"))

    permission = os.stat(tmp_dir).st_mode
    with mock.patch("os.lstat", side_effect=Exception):
        assert not remove_test_directory(tmp_dir)
    assert os.path.exists(tmp_dir)
    assert os.stat(tmp_dir).st_mode == permission

    assert remove_test_directory(tmp_dir)
    assert not os.path.exists(tmp_dir)
