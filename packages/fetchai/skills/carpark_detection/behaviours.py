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

"""This package contains a scaffold of a behaviour."""

import logging
import os
import subprocess
from typing import Optional, cast

from aea.helpers.search.models import Description
from aea.skills.base import Behaviour
from aea.skills.behaviours import TickerBehaviour
from packages.fetchai.protocols.oef.message import OEFMessage
from packages.fetchai.protocols.oef.serialization import OEFSerializer, DEFAULT_OEF
from packages.fetchai.skills.carpark_detection.strategy import Strategy

logger = logging.getLogger("aea.carpark_detection_skill")

REGISTER_ID = 1
UNREGISTER_ID = 2
SERVICE_ID = ''


DEFAULT_LAT = 1
DEFAULT_LON = 1
DEFAULT_IMAGE_CAPTURE_INTERVAL = 300


class CarParkDetectionAndGUIBehaviour(Behaviour):
    """This class implements a behaviour."""

    def __init__(self, **kwargs):
        """Initialise the behaviour."""
        self.image_capture_interval = kwargs.pop('image_capture_interval') if 'image_capture_interval' in kwargs.keys() else DEFAULT_IMAGE_CAPTURE_INTERVAL
        self.default_latitude = kwargs.pop('default_latitude') if 'default_latitude' in kwargs.keys() else DEFAULT_LAT
        self.default_longitude = kwargs.pop('default_longitude') if 'default_longitude' in kwargs.keys() else DEFAULT_LON
        self.process_id = None
        super().__init__(**kwargs)

    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """
        logger.info("[{}]: Attempt to launch car park detection and GUI in seperate processes.".format(self.context.agent_name))
        old_cwp = os.getcwd()
        os.chdir('../')
        strategy = cast(Strategy, self.context.strategy)
        if os.path.isfile('run_scripts/run_carparkagent.py'):
            param_list = [
                'python', 'run_scripts/run_carparkagent.py',
                '-ps', str(self.image_capture_interval),
                '-lat', str(self.default_latitude),
                '-lon', str(self.default_longitude)]
            logger.info("[{}]:Launchng process {}".format(self.context.agent_name, param_list))
            self.process_id = subprocess.Popen(param_list)
            os.chdir(old_cwp)
            logger.info("[{}]: detection and gui process launched, process_id {}".format(self.context.agent_name, self.process_id))
            strategy.other_carpark_processes_running = True
        else:
            logger.info("[{}]: Failed to find run_carpakragent.py - either you are running this without the rest of the carpark agent code (which can be got from here: https://github.com/fetchai/carpark_agent or you are running the aea from the wrong directory.".format(self.context.agent_name))

    def act(self) -> None:
        """
        Implement the act.

        :return: None
        """
        """Return the state of the execution."""

        # We never started the other processes
        if self.process_id is None:
            return

        return_code = self.process_id.poll()

        # Other procssess running fine
        if return_code is None:
            return
        # Other processes have finished so we should finish too
        # this is a bit hacky!
        else:
            exit()

    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        if self.process_id is None:
            return

        self.process_id.terminate()
        self.process_id.wait()


class ServiceRegistrationBehaviour(TickerBehaviour):
    """This class implements a behaviour."""

    def __init__(self, **kwargs):
        """Initialise the behaviour."""
        super().__init__(**kwargs)
        self._last_connection_status = self.context.connection_status.is_connected
        self._registered_service_description = None  # type: Optional[Description]
        self._oef_msf_id = 0

    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        self._record_oef_status()
        balance = self.context.ledger_apis.token_balance('fetchai', cast(str, self.context.agent_addresses.get('fetchai')))
        strategy.db.set_system_status("ledger-status", self.context.ledger_apis.last_tx_statuses['fetchai'])
        logger.info("[{}]: starting balance on fetchai ledger={}.".format(self.context.agent_name, balance))
        self._register_service()

    def act(self) -> None:
        """
        Implement the act.

        :return: None
        """
        self._update_connection_status()
        self._unregister_service()
        self._register_service()

    def _register_service(self) -> None:
        """
        Register to the OEF Service Directory.

        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        if strategy.has_service_description():
            desc = strategy.get_service_description()
            self._registered_service_description = desc
            self._oef_msf_id += 1
            msg = OEFMessage(type=OEFMessage.Type.REGISTER_SERVICE,
                             id=self._oef_msf_id,
                             service_description=desc,
                             service_id=SERVICE_ID)
            self.context.outbox.put_message(to=DEFAULT_OEF,
                                            sender=self.context.agent_address,
                                            protocol_id=OEFMessage.protocol_id,
                                            message=OEFSerializer().encode(msg))
            logger.info("[{}]: updating car park detection services on OEF.".format(self.context.agent_name))

    def _unregister_service(self) -> None:
        """
        Unregister service from OEF Service Directory.

        :return: None
        """
        if self._registered_service_description is not None:
            self._oef_msf_id += 1
            msg = OEFMessage(type=OEFMessage.Type.UNREGISTER_SERVICE,
                             id=self._oef_msf_id,
                             service_description=self._registered_service_description,
                             service_id=SERVICE_ID)
            self.context.outbox.put_message(to=DEFAULT_OEF,
                                            sender=self.context.agent_address,
                                            protocol_id=OEFMessage.protocol_id,
                                            message=OEFSerializer().encode(msg))
            logger.info("[{}]: unregistering car park detection services from OEF.".format(self.context.agent_name))
            self._registered_service_description = None

    def _update_connection_status(self) -> None:
        """
        Update the connection status in the db.

        :return: None
        """
        if self.context.connection_status.is_connected != self._last_connection_status:
            self._last_connection_status = self.context.connection_status.is_connected
            self._record_oef_status()

    def _record_oef_status(self):
        strategy = cast(Strategy, self.context.strategy)
        if self._last_connection_status:
            strategy.db.set_system_status("oef-status", "Connected")
        else:
            strategy.db.set_system_status("oef-status", "Disconnected")

    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        self._unregister_service()
        balance = self.context.ledger_apis.token_balance('fetchai', cast(str, self.context.agent_addresses.get('fetchai')))
        logger.info("[{}]: ending balance on fetchai ledger={}.".format(self.context.agent_name, balance))
