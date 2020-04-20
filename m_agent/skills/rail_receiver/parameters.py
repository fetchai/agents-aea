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
from aea.helpers.search.generic import GenericDataModel
from aea.skills.base import Model
from typing import Any, Dict, List, Optional, Tuple

from aea.helpers.search.models import Description, Query, Location

from packages.aris.skills.rail_receiver.rail_data_model import RAIL_DATAMODEL

DEFAULT_SERVICE_DATA = {"country": "UK", "city": "Cambridge", "latlon": Location(0.0, 0.0)}


class Parameters(Model):
    """This class scaffolds a model."""
    def __init__(self, **kwargs):
        self._event_type = None
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
        self._is_off_route = None
        self._current_train_id = None
        self._original_location = None
        self._original_location_planned_departure_datetime = None
        self._minutes_late = None
        self._early_late_description = None
        #  Creation message details.
        self._train_id = None
        self._schedule_source = None
        self._train_file_address = None
        self._schedule_end_date = None
        self._tp_origin_timestamp = None
        self._creation_timestamp = None
        self._tp_origin_stanox = None
        self._origin_dep_timestamp = None
        self._toc_id = None
        self._d1266_record_number = None
        self._train_call_type = None
        self._train_uid = None
        self._train_call_mode = None
        self._schedule_type = None
        self._sched_origin_stanox = None
        self._schedule_wtt_id = None
        self._schedule_start_date = None
        self._latitude = 0.0
        self._longitude = 0.0

        super().__init__(**kwargs)
        self._oef_msg_id = 0

        self._service_data = kwargs.pop("service_data", DEFAULT_SERVICE_DATA)

    @property
    def schedule_source(self):
        return self._schedule_source

    @property
    def latitude(self):
        return self._latitude

    @property
    def longitude(self):
        return self._longitude

    @property
    def train_file_address(self):
        return self._train_file_address

    @property
    def schedule_end_date(self):
        return self._schedule_end_date

    @property
    def tp_origin_stanox(self):
        return self._tp_origin_stanox

    @property
    def origin_dep_timestamp(self):
        return self._origin_dep_timestamp

    @property
    def toc_id(self):
        return self._toc_id

    @property
    def d1266_record_number(self):
        return self._d1266_record_number

    @property
    def train_call_type(self):
        return self._train_call_type

    @property
    def train_uid(self):
        return self._train_uid

    @property
    def train_call_mode(self):
        return self._train_call_mode

    @property
    def schedule_type(self):
        return self._schedule_type

    @property
    def sched_origin_stanox(self):
        return self._sched_origin_stanox

    @property
    def schedule_wtt_id(self):
        return self._schedule_wtt_id

    @property
    def schedule_start_date(self):
        return self._schedule_start_date

    @property
    def event_type(self):
        return self._event_type

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
        return self._is_off_route

    @property
    def current_train_id(self):
        return self._current_train_id

    @property
    def original_location(self):
        return self._original_location

    @property
    def original_location_planned_departure_datetime(self):
        return self._original_location_planned_departure_datetime

    @property
    def minutes_late(self):
        return self._minutes_late

    @property
    def early_late_description(self):
        return self._early_late_description

    def update_data(self, data_dict):
        """Update the train agent."""
        self.context.logger.info(data_dict)
        self._event_type = data_dict.get('event_type')
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
        self._minutes_late = data_dict.get('minutes_late')
        self._early_late_description = data_dict.get('early_late_description')

    def setup_data(self, data_dict):
        """Setup the train agent."""
        self._schedule_source = data_dict.get("schedule_source")
        self._train_file_address = data_dict.get("train_file_address")
        self._schedule_end_date = data_dict.get("schedule_end_date")
        self._train_id = data_dict.get("train_id")
        self._tp_origin_timestamp = data_dict.get('tp_origin_timestamp')
        self._creation_timestamp = data_dict.get('creation_timestamp')
        self._tp_origin_stanox = data_dict.get('tp_origin_stanox')
        self._origin_dep_timestamp = data_dict.get('origin_dep_timestamp')
        self._train_service_code = data_dict.get('train_service_code')
        self._toc_id = data_dict.get('toc_id')
        self._d1266_record_number = data_dict.get('d1266_record_number')
        self._train_call_type = data_dict.get('train_call_type')
        self._train_uid = data_dict.get('train_uid')
        self._train_call_mode = data_dict.get('train_call_mode')
        self._schedule_type = data_dict.get('schedule_type')
        self._sched_origin_stanox = data_dict.get('sched_origin_stanox')
        self._schedule_wtt_id = data_dict.get('schedule_wtt_id')
        self._schedule_start_date = data_dict.get('schedule_start_date')
        self._longitude = float(data_dict.get('longitude'))
        self._latitude = float(data_dict.get('latitude'))

    def get_next_oef_msg_id(self) -> int:
        """
        Get the next oef msg id.

        :return: the next oef msg id
        """
        self._oef_msg_id += 1
        return self._oef_msg_id

    def generate_service_data(self) -> Dict[str, Any]:
        """Build the current service data based on the location."""
        self._service_data['latlon'] = Location(latitude=self._latitude, longitude=self._longitude)
        return self._service_data

    def get_service_description(self) -> Description:
        """
        Get the service description.

        :return: a description of the offered services
        """
        desc = Description(
            values=self.generate_service_data(),
            data_model=RAIL_DATAMODEL(),
            data_model_name="rail_data_model"
        )
        return desc

    def is_matching_supply(self, query: Query) -> bool:
        """
        Check if the query matches the supply.

        :param query: the query
        :return: bool indiciating whether matches or not
        """
        # TODO, this is a stub
        return True
