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

import os
import subprocess  # nosec
from typing import Optional, cast

from aea.crypto.ethereum import ETHEREUM
from aea.crypto.fetchai import FETCHAI
from aea.helpers.search.models import Description
from aea.skills.base import Behaviour
from aea.skills.behaviours import TickerBehaviour

from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.protocols.oef_search.serialization import OefSearchSerializer
from packages.fetchai.skills.carpark_detection.strategy import Strategy

REGISTER_ID = 1
UNREGISTER_ID = 2

DEFAULT_LAT = 1
DEFAULT_LON = 1
DEFAULT_IMAGE_CAPTURE_INTERVAL = 300


class CarParkDetectionAndGUIBehaviour(Behaviour):
    """This class implements a behaviour."""

    def __init__(self, **kwargs):
        """Initialise the behaviour."""
        self.image_capture_interval = kwargs.pop(
            "image_capture_interval", DEFAULT_IMAGE_CAPTURE_INTERVAL
        )
        self.default_latitude = kwargs.pop("default_latitude", DEFAULT_LAT)
        self.default_longitude = kwargs.pop("default_longitude", DEFAULT_LON)
        self.process_id = None
        super().__init__(**kwargs)

    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """
        self.context.logger.info(
            "[{}]: Attempt to launch car park detection and GUI in seperate processes.".format(
                self.context.agent_name
            )
        )
        strategy = cast(Strategy, self.context.strategy)
        if os.path.isfile("run_scripts/run_carparkagent.py"):
            param_list = [
                "python",
                os.path.join("..", "run_scripts", "run_carparkagent.py"),
                "-ps",
                str(self.image_capture_interval),
                "-lat",
                str(self.default_latitude),
                "-lon",
                str(self.default_longitude),
            ]
            self.context.logger.info(
                "[{}]:Launchng process {}".format(self.context.agent_name, param_list)
            )
            self.process_id = subprocess.Popen(param_list)  # nosec
            self.context.logger.info(
                "[{}]: detection and gui process launched, process_id {}".format(
                    self.context.agent_name, self.process_id
                )
            )
            strategy.other_carpark_processes_running = True
        else:
            self.context.logger.info(
                "[{}]: Failed to find run_carparkagent.py - either you are running this without the rest of the carpark agent code (which can be got from here: https://github.com/fetchai/carpark_agent or you are running the aea from the wrong directory.".format(
                    self.context.agent_name
                )
            )

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

        if self.context.ledger_apis.has_fetchai:
            fet_balance = self.context.ledger_apis.token_balance(
                FETCHAI, cast(str, self.context.agent_addresses.get(FETCHAI))
            )
            if fet_balance > 0:
                self.context.logger.info(
                    "[{}]: starting balance on fetchai ledger={}.".format(
                        self.context.agent_name, fet_balance
                    )
                )
            else:
                self.context.logger.warning(
                    "[{}]: you have no starting balance on fetchai ledger!".format(
                        self.context.agent_name
                    )
                )

        if self.context.ledger_apis.has_ethereum:
            eth_balance = self.context.ledger_apis.token_balance(
                ETHEREUM, cast(str, self.context.agent_addresses.get(ETHEREUM))
            )
            if eth_balance > 0:
                self.context.logger.info(
                    "[{}]: starting balance on ethereum ledger={}.".format(
                        self.context.agent_name, eth_balance
                    )
                )
            else:
                self.context.logger.warning(
                    "[{}]: you have no starting balance on ethereum ledger!".format(
                        self.context.agent_name
                    )
                )
        if strategy.is_ledger_tx:
            strategy.db.set_system_status(
                "ledger-status",
                self.context.ledger_apis.last_tx_statuses[strategy.ledger_id],
            )

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
            msg = OefSearchMessage(
                performative=OefSearchMessage.Performative.REGISTER_SERVICE,
                dialogue_reference=(str(self._oef_msf_id), ""),
                service_description=desc,
            )
            self.context.outbox.put_message(
                to=self.context.search_service_address,
                sender=self.context.agent_address,
                protocol_id=OefSearchMessage.protocol_id,
                message=OefSearchSerializer().encode(msg),
            )
            self.context.logger.info(
                "[{}]: updating car park detection services on OEF.".format(
                    self.context.agent_name
                )
            )

    def _unregister_service(self) -> None:
        """
        Unregister service from OEF Service Directory.

        :return: None
        """
        if self._registered_service_description is not None:
            self._oef_msf_id += 1
            msg = OefSearchMessage(
                performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
                dialogue_reference=(str(self._oef_msf_id), ""),
                service_description=self._registered_service_description,
            )
            self.context.outbox.put_message(
                to=self.context.search_service_address,
                sender=self.context.agent_address,
                protocol_id=OefSearchMessage.protocol_id,
                message=OefSearchSerializer().encode(msg),
            )
            self.context.logger.info(
                "[{}]: unregistering car park detection services from OEF.".format(
                    self.context.agent_name
                )
            )
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
        if self.context.ledger_apis.has_fetchai:
            balance = self.context.ledger_apis.token_balance(
                FETCHAI, cast(str, self.context.agent_addresses.get(FETCHAI))
            )
            self.context.logger.info(
                "[{}]: ending balance on fetchai ledger={}.".format(
                    self.context.agent_name, balance
                )
            )

        if self.context.ledger_apis.has_ethereum:
            balance = self.context.ledger_apis.token_balance(
                ETHEREUM, cast(str, self.context.agent_addresses.get(ETHEREUM))
            )
            self.context.logger.info(
                "[{}]: ending balance on ethereum ledger={}.".format(
                    self.context.agent_name, balance
                )
            )

        self._unregister_service()
