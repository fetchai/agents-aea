# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2019 Fetch.AI Limited
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

"""This package contains a class representing the search state."""

from typing import Set

from aea.skills.base import SharedClass


class Search(SharedClass):
    """This class deals with the search state."""

    def __init__(self, *args, **kwargs):
        """Instantiate the search class."""
        super().__init__(*args, **kwargs)
        self._id = 0
        self.ids_for_tac = set()  # type: Set[int]

    @property
    def id(self) -> int:
        """Get the search id."""
        return self._id

    def get_next_id(self) -> int:
        """
        Generate the next search id and stores it.

        :return: a search id
        """
        self._id += 1
        self.ids_for_tac.add(self._id)
        return self._id
        # TODO: we need to make sure dialogue and search ids are unique across skills;
