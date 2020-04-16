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

"""This package contains a scaffold of a model."""

from aea.skills.base import Model

DEFAULT_ACCEPTABLE_STANOX = [47214, 47221]


class Parameters(Model):
    """This class scaffolds a model."""
    def __init__(self, **kwargs):
        self._event_type = None
        self._variation_status = None
        self._status = None
        self._planned_datetime = None
        self._actual_datetime = None
        self._planned_timetable_datetime = None
        self._location = None
        self._location_stanox = None
        self._is_correction = None
        self._train_terminated = None
        self._operating_company = None
        self._division_code = None
        self._train_service_code = None
        self._train_id = None
        self._is_off_route = None
        self._current_train_id = None
        self._original_location = None
        self._original_location_planned_departure_datetime = None
        self._minutes_late = None
        self._early_late_description = None

        super().__init__(**kwargs)

    @property
    def event_type(self):
        return self._event_type

    @property
    def variation_status(self):
        return self._variation_status

    @property
    def status(self):
        return self._status

    @property
    def planned_datetime(self):
        return self._planned_datetime

    @property
    def actual_datetime(self):
        return self._actual_datetime

    @property
    def planned_timetable_datetime(self):
        return self._planned_timetable_datetime


    @property
    def location(self):
        return self._location

    @property
    def location_stanox(self):
        return self._location_stanox

    @property
    def is_correction(self):
        return self._is_correction

    @property
    def train_terminated(self):
        return self.train_terminated

    @property
    def operating_company(self):
        return self._operating_company

    @property
    def division_code(self):
        return self._division_code

    @property
    def train_service_code(self):
        return self._train_service_code

    @property
    def train_id(self):
        return self._train_id

    @property
    def is_off_route(self):
        return self.is_off_route

    @property
    def current_train_id(self):
        return self._current_train_id

    @property
    def original_location(self):
        return self._original_location

    @property
    def original_location_lanned_departure_datetime(self):
        return self._original_location_planned_departure_datetime

    @property
    def minutes_late(self):
        return self._minutes_late

    @property
    def early_late_description(self):
        return self._early_late_description

    def setup_data(self, data_dict):
        """Setup and update the data of an agent."""
        self._event_type = data_dict.get('event_type')
        self._variation_status = data_dict.get('variation_status')
        self._status = data_dict.get('status')
        self._planned_datetime = data_dict.get("planned_datetime")
        self._actual_datetime = data_dict.get("actual_datetime")
        self._planned_timetable_datetime = data_dict.get('planned_timetable_datetime')
        self._location = data_dict.get('location')
        self._location_stanox = data_dict.get('location_stanox')
        self._is_correction = data_dict.get('is_correction')
        self._train_terminated = data_dict.get('train_terminated')
        self._operating_company = data_dict.get('operating_company')
        self._division_code = data_dict.get('division_code')
        self._train_service_code = data_dict.get('train_service_code')
        self._train_id = data_dict.get('train_id')
        self._is_off_route = data_dict.get('is_off_route')
        self._current_train_id = data_dict.get('current_train_id')
        self._original_location = data_dict.get("original_location")
        self._original_location_planned_departure_datetime = data_dict.get('original_location_planned_departure_datetime')
        self._minutes_late = int(
                    (self._actual_datetime - self._planned_datetime).total_seconds() / 60
                )
        self._early_late_description = data_dict.get('early_late_description')
