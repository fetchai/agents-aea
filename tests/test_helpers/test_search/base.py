# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2020 Fetch.AI Limited
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

"""This module contains the tests for the search helper module."""

from aea.helpers.search.models import Location


def test_location_init():
    """Test the initialization of the location model"""
    latitude = 51.507351
    longitude = -0.127758
    loc = Location(latitude, longitude)
    latitude_2 = 48.856613
    longitude_2 = 2.352222
    loc2 = Location(latitude_2, longitude_2)
    assert loc != loc2, "Locations should not be the same."
    assert loc.distance(loc2) > 0.0, "Locations should be positive."
