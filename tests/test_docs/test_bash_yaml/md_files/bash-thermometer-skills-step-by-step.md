``` bash 
sudo nano 99-hidraw-permissions.rules
``` 
``` bash 
KERNEL=="hidraw*", SUBSYSTEM=="hidraw", MODE="0664", GROUP="plugdev"
``` 
``` bash 
aea create my_aea
cd my_aea
``` 
``` bash 
aea scaffold skill thermometer
``` 
``` bash 
aea create my_client
cd my_client
``` 
``` bash 
aea scaffold skill thermometer_client
``` 
``` bash 
addr: ${OEF_ADDR: 127.0.0.1}
``` 
``` bash 
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
``` 
``` bash 
aea generate-key fetchai
aea add-key fetchai fet_private_key.txt
``` 
``` bash 
aea generate-wealth fetchai
``` 
``` bash 
aea add connection fetchai/oef:0.1.0
aea install
aea run --connections fetchai/oef:0.1.0
``` 
``` bash 
aea generate-key ethereum
aea add-key ethereum eth_private_key.txt
``` 
``` bash 
aea add connection fetchai/oef:0.1.0
aea install
aea run --connections fetchai/oef:0.1.0
``` 
``` bash 
cd ..
aea delete my_weather_station
aea delete my_weather_client
``` 
``` yaml 
name: thermometer
author: fetchai
version: 0.1.0
license: Apache-2.0
fingerprint: ""
description: "The thermometer skill implements the functionality to sell data."
behaviours:
 service_registration:
   class_name: ServiceRegistrationBehaviour
   args:
     services_interval: 60
handlers:
 fipa:
   class_name: FIPAHandler
   args: {}
models:
 strategy:
   class_name: Strategy
   args:
     price: 1
     seller_tx_fee: 0
     currency_id: 'FET'
     ledger_id: 'fetchai'
     has_sensor: True
     is_ledger_tx: True
 dialogues:
   class_name: Dialogues
   args: {}
protocols: ['fetchai/fipa:0.1.0', 'fetchai/oef:0.1.0', 'fetchai/default:0.1.0']
ledgers: ['fetchai']
dependencies:
 pyserial: {}
 temper-py: {}
``` 
``` yaml 
aea_version: 0.2.0
agent_name: my_aea
author: author
connections:
- fetchai/oef:0.1.0
- fetchai/stub:0.1.0
default_connection: fetchai/stub:0.1.0
default_ledger: fetchai
description: ''
fingerprint: ''
ledger_apis: {}
license: Apache-2.0
logging_config:
 disable_existing_loggers: false
 version: 1
private_key_paths: {}
protocols:
- fetchai/default:0.1.0
registry_path: ../packages
skills:
- author/thermometer:0.1.0
- fetchai/error:0.1.0
version: 0.1.0
``` 
``` yaml 

name: thermometer_client
author: fetchai
version: 0.1.0
license: Apache-2.0
fingerprint: ""
description: "The thermometer client skill implements the skill to purchase temperature data."
behaviours:
 search:
   class_name: MySearchBehaviour
   args:
     search_interval: 5
handlers:
 fipa:
   class_name: FIPAHandler
   args: {}
 oef:
   class_name: OEFHandler
   args: {}
 transaction:
   class_name: MyTransactionHandler
   args: {}
models:
 strategy:
   class_name: Strategy
   args:
     country: UK
     max_row_price: 4
     max_tx_fee: 2000000
     currency_id: 'FET'
     ledger_id: 'fetchai'
     is_ledger_tx: True
 dialogues:
   class_name: Dialogues
   args: {}
protocols: ['fetchai/fipa:0.1.0','fetchai/default:0.1.0','fetchai/oef:0.1.0']
ledgers: ['fetchai']
``` 
``` yaml 

aea_version: 0.2.0
agent_name: m_client
author: author
connections:
- fetchai/stub:0.1.0
default_connection: fetchai/stub:0.1.0
default_ledger: fetchai
description: ''
fingerprint: ''
ledger_apis: {}
license: Apache-2.0
logging_config:
 disable_existing_loggers: false
 version: 1
private_key_paths: {}
protocols:
- fetchai/default:0.1.0
registry_path: ../packages
skills:
- author/thermometer_client:0.1.0
- fetchai/error:0.1.0
version: 0.1.0
``` 
``` yaml 
skills:
- my_authos/thermometer:0.1.0
- fetchai/error:0.1.0
``` 
``` yaml 
ledger_apis:
  fetchai:
    network: testnet
``` 
``` yaml 
ledger_apis:
  ethereum:
    address: https://ropsten.infura.io/v3/f00f7b3ba0e848ddbdc8941c527447fe
    chain_id: 3
    gas_price: 50
``` 
``` yaml 
currency_id: 'ETH'
ledger_id: 'ethereum'
is_ledger_tx: True
``` 
``` yaml 
max_buyer_tx_fee: 20000
currency_id: 'ETH'
ledger_id: 'ethereum'
is_ledger_tx: True
``` 
``` python 
from typing import Optional, cast

from aea.crypto.ethereum import ETHEREUM
from aea.crypto.fetchai import FETCHAI
from aea.helpers.search.models import Description
from aea.skills.behaviours import TickerBehaviour

from packages.fetchai.protocols.oef.message import OEFMessage
from packages.fetchai.protocols.oef.serialization import DEFAULT_OEF, OEFSerializer
from packages.fetchai.skills.thermometer.strategy import Strategy


SERVICE_ID = ""
DEFAULT_SERVICES_INTERVAL = 30.0


class ServiceRegistrationBehaviour(TickerBehaviour):
   """This class implements a behaviour."""

    def __init__(self, **kwargs):
        """Initialise the behaviour."""
        services_interval = kwargs.pop(
            "services_interval", DEFAULT_SERVICES_INTERVAL
        )  # type: int
        super().__init__(tick_interval=services_interval, **kwargs)
        self._registered_service_description = None  # type: Optional[Description]
 
    def setup(self) -> None:
        """
        Implement the setup.
 
        :return: None
        """
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
 
        self._register_service()
 
    def act(self) -> None:
        """
        Implement the act.
 
        :return: None
        """
        self._unregister_service()
        self._register_service()
 
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
 
    def _register_service(self) -> None:
        """
        Register to the OEF Service Directory.
 
        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        desc = strategy.get_service_description()
        self._registered_service_description = desc
        oef_msg_id = strategy.get_next_oef_msg_id()
        msg = OEFMessage(
            type=OEFMessage.Type.REGISTER_SERVICE,
            id=oef_msg_id,
            service_description=desc,
            service_id=SERVICE_ID,
        )
        self.context.outbox.put_message(
            to=DEFAULT_OEF,
            sender=self.context.agent_address,
            protocol_id=OEFMessage.protocol_id,
            message=OEFSerializer().encode(msg),
        )
        self.context.logger.info(
            "[{}]: updating thermometer services on OEF.".format(
                self.context.agent_name
            )
        )
 
    def _unregister_service(self) -> None:
        """
        Unregister service from OEF Service Directory.
 
        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        oef_msg_id = strategy.get_next_oef_msg_id()
        msg = OEFMessage(
            type=OEFMessage.Type.UNREGISTER_SERVICE,
            id=oef_msg_id,
            service_description=self._registered_service_description,
            service_id=SERVICE_ID,
        )
        self.context.outbox.put_message(
            to=DEFAULT_OEF,
            sender=self.context.agent_address,
            protocol_id=OEFMessage.protocol_id,
            message=OEFSerializer().encode(msg),
        )
        self.context.logger.info(
            "[{}]: unregistering thermometer station services from OEF.".format(
                self.context.agent_name
            )
        )
        self._registered_service_description = None
``` 
``` python 
from typing import Optional, cast

from aea.configurations.base import ProtocolId
from aea.helpers.search.models import Description, Query
from aea.protocols.base import Message
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer
from aea.skills.base import Handler

from packages.fetchai.protocols.fipa.message import FIPAMessage
from packages.fetchai.protocols.fipa.serialization import FIPASerializer
from packages.fetchai.skills.thermometer.dialogues import Dialogue, Dialogues
from packages.fetchai.skills.thermometer.strategy import Strategy


class FIPAHandler(Handler):
    """This class scaffolds a handler."""
 
    SUPPORTED_PROTOCOL = FIPAMessage.protocol_id  # type: Optional[ProtocolId]
 
    def setup(self) -> None:
        """Implement the setup for the handler."""
        pass
 
    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.
 
        :param message: the message
        :return: None
        """
        # convenience representations
        fipa_msg = cast(FIPAMessage, message)
        dialogue_reference = fipa_msg.dialogue_reference
 
        # recover dialogue
        dialogues = cast(Dialogues, self.context.dialogues)
        if dialogues.is_belonging_to_registered_dialogue(
            fipa_msg, self.context.agent_address
        ):
            dialogue = cast(
                Dialogue, dialogues.get_dialogue(fipa_msg, self.context.agent_address)
            )
            dialogue.incoming_extend(fipa_msg)
        elif dialogues.is_permitted_for_new_dialogue(fipa_msg):
            dialogue = cast(
                Dialogue,
                dialogues.create_opponent_initiated(
                    message.counterparty,
                    dialogue_reference=dialogue_reference,
                    is_seller=True,
                ),
            )
            dialogue.incoming_extend(fipa_msg)
        else:
            self._handle_unidentified_dialogue(fipa_msg)
            return
 
        # handle message
        if fipa_msg.performative == FIPAMessage.Performative.CFP:
            self._handle_cfp(fipa_msg, dialogue)
        elif fipa_msg.performative == FIPAMessage.Performative.DECLINE:
            self._handle_decline(fipa_msg, dialogue)
        elif fipa_msg.performative == FIPAMessage.Performative.ACCEPT:
            self._handle_accept(fipa_msg, dialogue)
        elif fipa_msg.performative == FIPAMessage.Performative.INFORM:
            self._handle_inform(fipa_msg, dialogue)
 
    def teardown(self) -> None:
        """
        Implement the handler teardown.
 
        :return: None
        """
        pass
``` 
``` python 
def _handle_unidentified_dialogue(self, msg: FIPAMessage) -> None:
   """
   Handle an unidentified dialogue.

   Respond to the sender with a default message containing the appropriate error information.

   :param msg: the message

   :return: None
   """
   self.context.logger.info("[{}]: unidentified dialogue.".format(self.context.agent_name))
   default_msg = DefaultMessage(
       type=DefaultMessage.Type.ERROR,
       error_code=DefaultMessage.ErrorCode.INVALID_DIALOGUE.value,
       error_msg="Invalid dialogue.",
       error_data="fipa_message",
   ) 
   self.context.outbox.put_message(
       to=msg.counterparty,
       sender=self.context.agent_address,
       protocol_id=DefaultMessage.protocol_id,
       message=DefaultSerializer().encode(default_msg),
   )
``` 
``` python 
def _handle_cfp(self, msg: FIPAMessage, dialogue: Dialogue) -> None:
    """
    Handle the CFP.
 
    If the CFP matches the supplied services then send a PROPOSE, otherwise send a DECLINE.
 
    :param msg: the message
    :param dialogue: the dialogue object
    :return: None
    """
    new_message_id = msg.message_id + 1
    new_target = msg.message_id
    self.context.logger.info(
        "[{}]: received CFP from sender={}".format(
            self.context.agent_name, msg.counterparty[-5:]
        )
    )
    query = cast(Query, msg.query)
    strategy = cast(Strategy, self.context.strategy)
 
    if strategy.is_matching_supply(query):
        proposal, temp_data = strategy.generate_proposal_and_data(
            query, msg.counterparty
        )
        dialogue.temp_data = temp_data
        dialogue.proposal = proposal
        self.context.logger.info(
            "[{}]: sending sender={} a PROPOSE with proposal={}".format(
                self.context.agent_name, msg.counterparty[-5:], proposal.values
            )
        )
        proposal_msg = FIPAMessage(
            message_id=new_message_id,
            dialogue_reference=dialogue.dialogue_label.dialogue_reference,
            target=new_target,
            performative=FIPAMessage.Performative.PROPOSE,
            proposal=[proposal],
        )
        dialogue.outgoing_extend(proposal_msg)
        self.context.outbox.put_message(
            to=msg.counterparty,
            sender=self.context.agent_address,
            protocol_id=FIPAMessage.protocol_id,
            message=FIPASerializer().encode(proposal_msg),
        )
    else:
        self.context.logger.info(
            "[{}]: declined the CFP from sender={}".format(
                self.context.agent_name, msg.counterparty[-5:]
            )
        )
        decline_msg = FIPAMessage(
            message_id=new_message_id,
            dialogue_reference=dialogue.dialogue_label.dialogue_reference,
            target=new_target,
            performative=FIPAMessage.Performative.DECLINE,
        )
        dialogue.outgoing_extend(decline_msg)
        self.context.outbox.put_message(
            to=msg.counterparty,
            sender=self.context.agent_address,
            protocol_id=FIPAMessage.protocol_id,
            message=FIPASerializer().encode(decline_msg),
        )
``` 
``` python 
def _handle_decline(self, msg: FIPAMessage, dialogue: Dialogue) -> None:
    """
    Handle the DECLINE.
 
    Close the dialogue.
 
    :param msg: the message
    :param dialogue: the dialogue object
    :return: None
    """
    self.context.logger.info(
        "[{}]: received DECLINE from sender={}".format(
            self.context.agent_name, msg.counterparty[-5:]
        )
    )
    dialogues = cast(Dialogues, self.context.dialogues)
    dialogues.dialogue_stats.add_dialogue_endstate(
        Dialogue.EndState.DECLINED_PROPOSE, dialogue.is_self_initiated
    )

``` 
``` python 
def _handle_accept(self, msg: FIPAMessage, dialogue: Dialogue) -> None:
    """
    Handle the ACCEPT.
 
    Respond with a MATCH_ACCEPT_W_INFORM which contains the address to send the funds to.
 
    :param msg: the message
    :param dialogue: the dialogue object
    :return: None
    """
    new_message_id = msg.message_id + 1
    new_target = msg.message_id
    self.context.logger.info(
        "[{}]: received ACCEPT from sender={}".format(
            self.context.agent_name, msg.counterparty[-5:]
        )
    )
    self.context.logger.info(
        "[{}]: sending MATCH_ACCEPT_W_INFORM to sender={}".format(
            self.context.agent_name, msg.counterparty[-5:]
        )
    )
    proposal = cast(Description, dialogue.proposal)
    identifier = cast(str, proposal.values.get("ledger_id"))
    match_accept_msg = FIPAMessage(
        message_id=new_message_id,
        dialogue_reference=dialogue.dialogue_label.dialogue_reference,
        target=new_target,
        performative=FIPAMessage.Performative.MATCH_ACCEPT_W_INFORM,
        info={"address": self.context.agent_addresses[identifier]},
    )
    dialogue.outgoing_extend(match_accept_msg)
    self.context.outbox.put_message(
        to=msg.counterparty,
        sender=self.context.agent_address,
        protocol_id=FIPAMessage.protocol_id,
        message=FIPASerializer().encode(match_accept_msg),
    )
``` 
``` python 
def _handle_inform(self, msg: FIPAMessage, dialogue: Dialogue) -> None:
    """
    Handle the INFORM.
 
    If the INFORM message contains the transaction_digest then verify that it is settled, otherwise do nothing.
    If the transaction is settled send the temperature data, otherwise do nothing.
 
    :param msg: the message
    :param dialogue: the dialogue object
    :return: None
    """
    new_message_id = msg.message_id + 1
    new_target = msg.message_id
    logger.info(
        "[{}]: received INFORM from sender={}".format(
            self.context.agent_name, msg.counterparty[-5:]
        )
    )
 
    strategy = cast(Strategy, self.context.strategy)
    if strategy.is_ledger_tx and ("transaction_digest" in msg.info.keys()):
        tx_digest = msg.info["transaction_digest"]
        self.context.logger.info(
            "[{}]: checking whether transaction={} has been received ...".format(
                self.context.agent_name, tx_digest
            )
        )
        proposal = cast(Description, dialogue.proposal)
        ledger_id = cast(str, proposal.values.get("ledger_id"))
        is_valid = self.context.ledger_apis.is_tx_valid(
            ledger_id,
            tx_digest,
            self.context.agent_addresses[ledger_id],
            msg.counterparty,
            cast(str, proposal.values.get("tx_nonce")),
            cast(int, proposal.values.get("price")),
        )
        if is_valid:
            token_balance = self.context.ledger_apis.token_balance(
                ledger_id, cast(str, self.context.agent_addresses.get(ledger_id))
            )
            self.context.logger.info(
                "[{}]: transaction={} settled, new balance={}. Sending data to sender={}".format(
                    self.context.agent_name,
                    tx_digest,
                    token_balance,
                    msg.counterparty[-5:],
                )
            )
            inform_msg = FIPAMessage(
                message_id=new_message_id,
                dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                target=new_target,
                performative=FIPAMessage.Performative.INFORM,
                info=dialogue.temp_data,
            )
            dialogue.outgoing_extend(inform_msg)
            self.context.outbox.put_message(
                to=msg.counterparty,
                sender=self.context.agent_address,
                protocol_id=FIPAMessage.protocol_id,
                message=FIPASerializer().encode(inform_msg),
            )
            dialogues = cast(Dialogues, self.context.dialogues)
            dialogues.dialogue_stats.add_dialogue_endstate(
                Dialogue.EndState.SUCCESSFUL, dialogue.is_self_initiated
            )
        else:
            self.context.logger.info(
                "[{}]: transaction={} not settled, aborting".format(
                    self.context.agent_name, tx_digest
                )
            )
    elif "Done" in msg.info.keys():
        inform_msg = FIPAMessage(
            message_id=new_message_id,
            dialogue_reference=dialogue.dialogue_label.dialogue_reference,
            target=new_target,
            performative=FIPAMessage.Performative.INFORM,
            info=dialogue.temp_data,
        )
        dialogue.outgoing_extend(inform_msg)
        self.context.outbox.put_message(
            to=msg.counterparty,
            sender=self.context.agent_address,
            protocol_id=FIPAMessage.protocol_id,
            message=FIPASerializer().encode(inform_msg),
        )
        dialogues = cast(Dialogues, self.context.dialogues)
        dialogues.dialogue_stats.add_dialogue_endstate(
            Dialogue.EndState.SUCCESSFUL, dialogue.is_self_initiated
        )
    else:
        self.context.logger.warning(
            "[{}]: did not receive transaction digest from sender={}.".format(
                self.context.agent_name, msg.counterparty[-5:]
            )
        )
``` 
``` python 
from random import randrange
from typing import Any, Dict, Tuple

from temper import Temper

from aea.helpers.search.models import Description, Query
from aea.mail.base import Address
from aea.skills.base import Model

from packages.fetchai.skills.thermometer.thermometer_data_model import (
   SCHEME,
   THERMOMETER_DATAMODEL,
)

DEFAULT_PRICE_PER_ROW = 1
DEFAULT_SELLER_TX_FEE = 0
DEFAULT_CURRENCY_PBK = "FET"
DEFAULT_LEDGER_ID = "fetchai"
DEFAULT_IS_LEDGER_TX = True
DEFAULT_HAS_SENSOR = True


class Strategy(Model):
   """This class defines a strategy for the agent."""

   def __init__(self, **kwargs) -> None:
       """
       Initialize the strategy of the agent.

       :param register_as: determines whether the agent registers as seller, buyer or both
       :param search_for: determines whether the agent searches for sellers, buyers or both

       :return: None
       """
       self._price_per_row = kwargs.pop("price_per_row", DEFAULT_PRICE_PER_ROW)
       self._seller_tx_fee = kwargs.pop("seller_tx_fee", DEFAULT_SELLER_TX_FEE)
       self._currency_id = kwargs.pop("currency_id", DEFAULT_CURRENCY_PBK)
       self._ledger_id = kwargs.pop("ledger_id", DEFAULT_LEDGER_ID)
       self.is_ledger_tx = kwargs.pop("is_ledger_tx", DEFAULT_IS_LEDGER_TX)
       self._has_sensor = kwargs.pop("has_sensor", DEFAULT_HAS_SENSOR)
       super().__init__(**kwargs)
       self._oef_msg_id = 0
``` 
``` python 
def get_next_oef_msg_id(self) -> int:
   """
   Get the next oef msg id.

   :return: the next oef msg id
   """
   self._oef_msg_id += 1
   return self._oef_msg_id
``` 
``` python 
def get_service_description(self) -> Description:
   """
   Get the service description.

   :return: a description of the offered services
   """
   desc = Description(SCHEME, data_model=THERMOMETER_DATAMODEL())
   return desc
``` 
``` python 
def is_matching_supply(self, query: Query) -> bool:
   """
   Check if the query matches the supply.

   :param query: the query
   :return: bool indicating whether matches or not
   """
   # TODO, this is a stub
   return True
``` 
``` python 
def generate_proposal_and_data(
   self, query: Query, counterparty: Address
) -> Tuple[Description, Dict[str, Any]]:
   """
   Generate a proposal matching the query.

   :param counterparty: the counterparty of the proposal.
   :param query: the query
   :return: a tuple of proposal and the temperature data
   """

   tx_nonce = self.context.ledger_apis.generate_tx_nonce(
       identifier=self._ledger_id,
       seller=self.context.agent_addresses[self._ledger_id],
       client=counterparty,
   )

   temp_data = self._build_data_payload()
   total_price = self._price_per_row
   assert (
       total_price - self._seller_tx_fee > 0
   ), "This sale would generate a loss, change the configs!"
   proposal = Description(
       {
           "price": total_price,
           "seller_tx_fee": self._seller_tx_fee,
           "currency_id": self._currency_id,
           "ledger_id": self._ledger_id,
           "tx_nonce": tx_nonce,
       }
   )
   return proposal, temp_data

def _build_data_payload(self) -> Dict[str, Any]:
   """
   Build the data payload.

   :return: a tuple of the data and the rows
   """
   if self._has_sensor:
       temper = Temper()
       while True:
           results = temper.read()
           if "internal temperature" in results.keys():
               degrees = {"thermometer_data": results}
           else:
               self.context.logger.debug("Couldn't read the sensor I am re-trying.")
   else:
       degrees = {"thermometer_data": randrange(10, 25)}
       self.context.logger.info(degrees)

   return degrees
``` 
``` python 
from typing import Any, Dict, Optional

from aea.helpers.dialogue.base import DialogueLabel
from aea.helpers.search.models import Description
from aea.skills.base import Model

from packages.fetchai.protocols.fipa.dialogues import FIPADialogue, FIPADialogues


class Dialogue(FIPADialogue):
   """The dialogue class maintains state of a dialogue and manages it."""

   def __init__(self, dialogue_label: DialogueLabel, is_seller: bool) -> None:
       """
       Initialize a dialogue label.

       :param dialogue_label: the identifier of the dialogue
       :param is_seller: indicates whether the agent associated with the dialogue is a seller or buyer

       :return: None
       """
       FIPADialogue.__init__(self, dialogue_label=dialogue_label, is_seller=is_seller)
       self.temp_data = None  # type: Optional[Dict[str, Any]]
       self.proposal = None  # type: Optional[Description]


class Dialogues(Model, FIPADialogues):
   """The dialogues class keeps track of all dialogues."""

   def __init__(self, **kwargs) -> None:
       """
       Initialize dialogues.

       :return: None
       """
       Model.__init__(self, **kwargs)
       FIPADialogues.__init__(self)

``` 
``` python 
from aea.helpers.search.models import Attribute, DataModel

SCHEME = {"country": "UK", "city": "Cambridge"}


class Thermometer_Datamodel(DataModel):
   """Data model for the thermo Agent."""

   def __init__(self):
       """Initialise the dataModel."""
       self.attribute_country = Attribute("country", str, True)
       self.attribute_city = Attribute("city", str, True)

       super().__init__(
           "thermometer_datamodel", [self.attribute_country, self.attribute_city]
       )

``` 
``` python 

from typing import cast

from aea.crypto.ethereum import ETHEREUM
from aea.crypto.fetchai import FETCHAI
from aea.skills.behaviours import TickerBehaviour

from packages.fetchai.protocols.oef.message import OEFMessage
from packages.fetchai.protocols.oef.serialization import DEFAULT_OEF, OEFSerializer
from packages.fetchai.skills.thermometer_client.strategy import Strategy

DEFAULT_SEARCH_INTERVAL = 5.0


class MySearchBehaviour(TickerBehaviour):
   """This class implements a search behaviour."""

   def __init__(self, **kwargs):
       """Initialize the search behaviour."""
       search_interval = cast(
           float, kwargs.pop("search_interval", DEFAULT_SEARCH_INTERVAL)
       )
       super().__init__(tick_interval=search_interval, **kwargs)

   def setup(self) -> None:
       """Implement the setup for the behaviour."""
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
          
   def act(self) -> None:
       """
       Implement the act.

       :return: None
       """
       strategy = cast(Strategy, self.context.strategy)
       if strategy.is_searching:
           query = strategy.get_service_query()
           search_id = strategy.get_next_search_id()
           oef_msg = OEFMessage(
               type=OEFMessage.Type.SEARCH_SERVICES, id=search_id, query=query
           )
           self.context.outbox.put_message(
               to=DEFAULT_OEF,
               sender=self.context.agent_address,
               protocol_id=OEFMessage.protocol_id,
               message=OEFSerializer().encode(oef_msg),
           )

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

``` 
``` python 
import pprint
from typing import Any, Dict, List, Optional, cast

from aea.configurations.base import ProtocolId, PublicId
from aea.decision_maker.messages.transaction import TransactionMessage
from aea.helpers.dialogue.base import DialogueLabel
from aea.helpers.search.models import Description
from aea.protocols.base import Message
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer
from aea.skills.base import Handler

from packages.fetchai.protocols.fipa.message import FIPAMessage
from packages.fetchai.protocols.fipa.serialization import FIPASerializer
from packages.fetchai.protocols.oef.message import OEFMessage
from packages.fetchai.skills.thermometer_client.dialogues import Dialogue, Dialogues
from packages.fetchai.skills.thermometer_client.strategy import Strategy


class FIPAHandler(Handler):
    """This class scaffolds a handler."""
 
    SUPPORTED_PROTOCOL = FIPAMessage.protocol_id  # type: Optional[ProtocolId]
 
    def setup(self) -> None:
        """
        Implement the setup.
 
        :return: None
        """
        pass
 
    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.
 
        :param message: the message
        :return: None
        """
        # convenience representations
        fipa_msg = cast(FIPAMessage, message)
 
        # recover dialogue
        dialogues = cast(Dialogues, self.context.dialogues)
        if dialogues.is_belonging_to_registered_dialogue(
            fipa_msg, self.context.agent_address
        ):
            dialogue = cast(
                Dialogue, dialogues.get_dialogue(fipa_msg, self.context.agent_address)
            )
            dialogue.incoming_extend(fipa_msg)
        else:
            self._handle_unidentified_dialogue(fipa_msg)
            return
 
        # handle message
        if fipa_msg.performative == FIPAMessage.Performative.PROPOSE:
            self._handle_propose(fipa_msg, dialogue)
        elif fipa_msg.performative == FIPAMessage.Performative.DECLINE:
            self._handle_decline(fipa_msg, dialogue)
        elif fipa_msg.performative == FIPAMessage.Performative.MATCH_ACCEPT_W_INFORM:
            self._handle_match_accept(fipa_msg, dialogue)
        elif fipa_msg.performative == FIPAMessage.Performative.INFORM:
            self._handle_inform(fipa_msg, dialogue)
 
    def teardown(self) -> None:
        """
        Implement the handler teardown.
 
        :return: None
        """
        pass
``` 
``` python 
def _handle_unidentified_dialogue(self, msg: FIPAMessage) -> None:
    """
    Handle an unidentified dialogue.
 
    :param msg: the message
    """
    self.context.logger.info("[{}]: unidentified dialogue.".format(self.context.agent_name))
    default_msg = DefaultMessage(
        type=DefaultMessage.Type.ERROR,
        error_code=DefaultMessage.ErrorCode.INVALID_DIALOGUE.value,
        error_msg="Invalid dialogue.",
        error_data="fipa_message",
    )
    self.context.outbox.put_message(
        to=msg.counterparty,
        sender=self.context.agent_address,
        protocol_id=DefaultMessage.protocol_id,
        message=DefaultSerializer().encode(default_msg),
    )
``` 
``` python 
def _handle_propose(self, msg: FIPAMessage, dialogue: Dialogue) -> None:
    """
    Handle the propose.
 
    :param msg: the message
    :param dialogue: the dialogue object
    :return: None
    """
    new_message_id = msg.message_id + 1
    new_target_id = msg.message_id
    proposals = msg.proposal
 
    if proposals is not []:
        # only take the first proposal
        proposal = proposals[0]
        self.context.logger.info(
            "[{}]: received proposal={} from sender={}".format(
                self.context.agent_name, proposal.values, msg.counterparty[-5:]
            )
        )
        strategy = cast(Strategy, self.context.strategy)
        acceptable = strategy.is_acceptable_proposal(proposal)
        affordable = strategy.is_affordable_proposal(proposal)
        if acceptable and affordable:
            strategy.is_searching = False
            self.context.logger.info(
                "[{}]: accepting the proposal from sender={}".format(
                    self.context.agent_name, msg.counterparty[-5:]
                )
            )
            dialogue.proposal = proposal
            accept_msg = FIPAMessage(
                message_id=new_message_id,
                dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                target=new_target_id,
                performative=FIPAMessage.Performative.ACCEPT,
            )
            dialogue.outgoing_extend(accept_msg)
            self.context.outbox.put_message(
                to=msg.counterparty,
                sender=self.context.agent_address,
                protocol_id=FIPAMessage.protocol_id,
                message=FIPASerializer().encode(accept_msg),
            )
        else:
            self.context.logger.info(
                "[{}]: declining the proposal from sender={}".format(
                    self.context.agent_name, msg.counterparty[-5:]
                )
            )
            decline_msg = FIPAMessage(
                message_id=new_message_id,
                dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                target=new_target_id,
                performative=FIPAMessage.Performative.DECLINE,
            )
            dialogue.outgoing_extend(decline_msg)
            self.context.outbox.put_message(
                to=msg.counterparty,
                sender=self.context.agent_address,
                protocol_id=FIPAMessage.protocol_id,
                message=FIPASerializer().encode(decline_msg),
            )
``` 
``` python 

def _handle_decline(self, msg: FIPAMessage, dialogue: Dialogue) -> None:
    """
    Handle the decline.
 
    :param msg: the message
    :param dialogue: the dialogue object
    :return: None
    """
    self.context.logger.info(
        "[{}]: received DECLINE from sender={}".format(
            self.context.agent_name, msg.counterparty[-5:]
        )
    )
    target = msg.get("target")
    dialogues = cast(Dialogues, self.context.dialogues)
    if target == 1:
        dialogues.dialogue_stats.add_dialogue_endstate(
            Dialogue.EndState.DECLINED_CFP, dialogue.is_self_initiated
        )
    elif target == 3:
        dialogues.dialogue_stats.add_dialogue_endstate(
            Dialogue.EndState.DECLINED_ACCEPT, dialogue.is_self_initiated
        )
``` 
``` python 

def _handle_match_accept(self, msg: FIPAMessage, dialogue: Dialogue) -> None:
    """
    Handle the match accept.
 
    :param msg: the message
    :param dialogue: the dialogue object
    :return: None
    """
    strategy = cast(Strategy, self.context.strategy)
    if strategy.is_ledger_tx:
        self.context.logger.info(
            "[{}]: received MATCH_ACCEPT_W_INFORM from sender={}".format(
                self.context.agent_name, msg.counterparty[-5:]
            )
        )
        info = msg.info
        address = cast(str, info.get("address"))
        proposal = cast(Description, dialogue.proposal)
        tx_msg = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
            skill_callback_ids=[PublicId("fetchai", "thermometer_client", "0.1.0")],
            tx_id="transaction0",
            tx_sender_addr=self.context.agent_addresses[
                proposal.values["ledger_id"]
            ],
            tx_counterparty_addr=address,
            tx_amount_by_currency_id={
                proposal.values["currency_id"]: -proposal.values["price"]
            },
            tx_sender_fee=strategy.max_buyer_tx_fee,
            tx_counterparty_fee=proposal.values["seller_tx_fee"],
            tx_quantities_by_good_id={},
            ledger_id=proposal.values["ledger_id"],
            info={"dialogue_label": dialogue.dialogue_label.json},
            tx_nonce=proposal.values.get("tx_nonce"),
        )
        self.context.decision_maker_message_queue.put_nowait(tx_msg)
        self.context.logger.info(
            "[{}]: proposing the transaction to the decision maker. Waiting for confirmation ...".format(
                self.context.agent_name
            )
        )
    else:
        new_message_id = msg.message_id + 1
        new_target = msg.message_id
        inform_msg = FIPAMessage(
            message_id=new_message_id,
            dialogue_reference=dialogue.dialogue_label.dialogue_reference,
            target=new_target,
            performative=FIPAMessage.Performative.INFORM,
            info={"Done": "Sending payment via bank transfer"},
        )
        dialogue.outgoing_extend(inform_msg)
        self.context.outbox.put_message(
            to=msg.counterparty,
            sender=self.context.agent_address,
            protocol_id=FIPAMessage.protocol_id,
            message=FIPASerializer().encode(inform_msg),
        )
        self.context.logger.info(
            "[{}]: informing counterparty={} of payment.".format(
                self.context.agent_name, msg.counterparty[-5:]
            )
        )

``` 
``` python 

def _handle_inform(self, msg: FIPAMessage, dialogue: Dialogue) -> None:
    """
    Handle the match inform.
 
    :param msg: the message
    :param dialogue: the dialogue object
    :return: None
    """
    self.context.logger.info(
        "[{}]: received INFORM from sender={}".format(
            self.context.agent_name, msg.counterparty[-5:]
        )
    )
    if "thermometer_data" in msg.info.keys():
        thermometer_data = msg.info["thermometer_data"]
        self.context.logger.info(
            "[{}]: received the following thermometer data={}".format(
                self.context.agent_name, pprint.pformat(thermometer_data)
            )
        )
        dialogues = cast(Dialogues, self.context.dialogues)
        dialogues.dialogue_stats.add_dialogue_endstate(
            Dialogue.EndState.SUCCESSFUL, dialogue.is_self_initiated
        )
    else:
        self.context.logger.info(
            "[{}]: received no data from sender={}".format(
                self.context.agent_name, msg.counterparty[-5:]
            )
        )
``` 
``` python 

class OEFHandler(Handler):
    """This class scaffolds a handler."""
 
    SUPPORTED_PROTOCOL = OEFMessage.protocol_id  # type: Optional[ProtocolId]
 
    def setup(self) -> None:
        """Call to setup the handler."""
        pass
 
    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.
 
        :param message: the message
        :return: None
        """
        # convenience representations
        oef_msg = cast(OEFMessage, message)
        if oef_msg.type is OEFMessage.Type.SEARCH_RESULT:
            agents = oef_msg.agents
            self._handle_search(agents)
 
    def teardown(self) -> None:
        """
        Implement the handler teardown.
 
        :return: None
        """
        pass
 
    def _handle_search(self, agents: List[str]) -> None:
        """
        Handle the search response.
 
        :param agents: the agents returned by the search
        :return: None
        """
        if len(agents) > 0:
            self.context.logger.info(
                "[{}]: found agents={}, stopping search.".format(
                    self.context.agent_name, list(map(lambda x: x[-5:], agents))
                )
            )
            strategy = cast(Strategy, self.context.strategy)
            # stopping search
            strategy.is_searching = False
            # pick first agent found
            opponent_addr = agents[0]
            dialogues = cast(Dialogues, self.context.dialogues)
            dialogue = dialogues.create_self_initiated(
                opponent_addr, self.context.agent_address, is_seller=False
            )
            query = strategy.get_service_query()
            self.context.logger.info(
                "[{}]: sending CFP to agent={}".format(
                    self.context.agent_name, opponent_addr[-5:]
                )
            )
            cfp_msg = FIPAMessage(
                message_id=FIPAMessage.STARTING_MESSAGE_ID,
                dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                performative=FIPAMessage.Performative.CFP,
                target=FIPAMessage.STARTING_TARGET,
                query=query,
            )
            dialogue.outgoing_extend(cfp_msg)
            self.context.outbox.put_message(
                to=opponent_addr,
                sender=self.context.agent_address,
                protocol_id=FIPAMessage.protocol_id,
                message=FIPASerializer().encode(cfp_msg),
            )
        else:
            self.context.logger.info(
                "[{}]: found no agents, continue searching.".format(
                    self.context.agent_name
                )
            )
 
``` 
``` python 

class MyTransactionHandler(Handler):
    """Implement the transaction handler."""
 
    SUPPORTED_PROTOCOL = TransactionMessage.protocol_id  # type: Optional[ProtocolId]
 
    def setup(self) -> None:
        """Implement the setup for the handler."""
        pass
 
    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.
 
        :param message: the message
        :return: None
        """
        tx_msg_response = cast(TransactionMessage, message)
        if (
            tx_msg_response is not None
            and tx_msg_response.performative
            == TransactionMessage.Performative.SUCCESSFUL_SETTLEMENT
        ):
            self.context.logger.info(
                "[{}]: transaction was successful.".format(self.context.agent_name)
            )
            json_data = {"transaction_digest": tx_msg_response.tx_digest}
            info = cast(Dict[str, Any], tx_msg_response.info)
            dialogue_label = DialogueLabel.from_json(
                cast(Dict[str, str], info.get("dialogue_label"))
            )
            dialogues = cast(Dialogues, self.context.dialogues)
            dialogue = dialogues.dialogues[dialogue_label]
            fipa_msg = cast(FIPAMessage, dialogue.last_incoming_message)
            new_message_id = fipa_msg.message_id + 1
            new_target_id = fipa_msg.message_id
            counterparty_addr = dialogue.dialogue_label.dialogue_opponent_addr
            inform_msg = FIPAMessage(
                message_id=new_message_id,
                dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                target=new_target_id,
                performative=FIPAMessage.Performative.INFORM,
                info=json_data,
            )
            dialogue.outgoing_extend(inform_msg)
            self.context.outbox.put_message(
                to=counterparty_addr,
                sender=self.context.agent_address,
                protocol_id=FIPAMessage.protocol_id,
                message=FIPASerializer().encode(inform_msg),
            )
            self.context.logger.info(
                "[{}]: informing counterparty={} of transaction digest.".format(
                    self.context.agent_name, counterparty_addr[-5:]
                )
            )
        else:
            self.context.logger.info(
                "[{}]: transaction was not successful.".format(self.context.agent_name)
            )
 
    def teardown(self) -> None:
        """
        Implement the handler teardown.
 
        :return: None
        """
        pass
``` 
``` python 

from typing import cast

from aea.helpers.search.models import Constraint, ConstraintType, Description, Query
from aea.skills.base import Model

DEFAULT_COUNTRY = "UK"
SEARCH_TERM = "country"
DEFAULT_MAX_ROW_PRICE = 5
DEFAULT_MAX_TX_FEE = 50
DEFAULT_CURRENCY_PBK = "FET"
DEFAULT_LEDGER_ID = "fetchai"
DEFAULT_IS_LEDGER_TX = True


class Strategy(Model):
    """This class defines a strategy for the agent."""
 
    def __init__(self, **kwargs) -> None:
        """
        Initialize the strategy of the agent.
 
        :return: None
        """
        self._country = kwargs.pop("country", DEFAULT_COUNTRY)
        self._max_row_price = kwargs.pop("max_row_price", DEFAULT_MAX_ROW_PRICE)
        self.max_buyer_tx_fee = kwargs.pop("max_tx_fee", DEFAULT_MAX_TX_FEE)
        self._currency_id = kwargs.pop("currency_id", DEFAULT_CURRENCY_PBK)
        self._ledger_id = kwargs.pop("ledger_id", DEFAULT_LEDGER_ID)
        self.is_ledger_tx = kwargs.pop("is_ledger_tx", DEFAULT_IS_LEDGER_TX)
        super().__init__(**kwargs)
        self._search_id = 0
        self.is_searching = True
``` 
``` python 

def get_next_search_id(self) -> int:
    """
    Get the next search id and set the search time.
 
    :return: the next search id
    """
    self._search_id += 1
    return self._search_id

def get_service_query(self) -> Query:
    """
    Get the service query of the agent.
 
    :return: the query
    """
    query = Query(
        [Constraint(SEARCH_TERM, ConstraintType("==", self._country))], model=None
    )
    return query
``` 
``` python 

def is_acceptable_proposal(self, proposal: Description) -> bool:
    """
    Check whether it is an acceptable proposal.
 
    :return: whether it is acceptable
    """
    result = (
        (proposal.values["price"] - proposal.values["seller_tx_fee"] > 0)
        and (proposal.values["price"] <= self._max_row_price)
        and (proposal.values["currency_id"] == self._currency_id)
        and (proposal.values["ledger_id"] == self._ledger_id)
    )
    return result
``` 
``` python 
def is_affordable_proposal(self, proposal: Description) -> bool:
    """
    Check whether it is an affordable proposal.
 
    :return: whether it is affordable
    """
    if self.is_ledger_tx:
        payable = proposal.values["price"] + self.max_buyer_tx_fee
        ledger_id = proposal.values["ledger_id"]
        address = cast(str, self.context.agent_addresses.get(ledger_id))
        balance = self.context.ledger_apis.token_balance(ledger_id, address)
        result = balance >= payable
    else:
        result = True
    return result
``` 
``` python 

from typing import Optional

from aea.helpers.dialogue.base import DialogueLabel
from aea.helpers.search.models import Description
from aea.skills.base import Model

from packages.fetchai.protocols.fipa.dialogues import FIPADialogue, FIPADialogues


class Dialogue(FIPADialogue):
    """The dialogue class maintains state of a dialogue and manages it."""
 
    def __init__(self, dialogue_label: DialogueLabel, is_seller: bool) -> None:
        """
        Initialize a dialogue label.
 
        :param dialogue_label: the identifier of the dialogue
        :param is_seller: indicates whether the agent associated with the dialogue is a seller or buyer
 
        :return: None
        """
        FIPADialogue.__init__(self, dialogue_label=dialogue_label, is_seller=is_seller)
        self.proposal = None  # type: Optional[Description]


class Dialogues(Model, FIPADialogues):
    """The dialogues class keeps track of all dialogues."""
 
    def __init__(self, **kwargs) -> None:
        """
        Initialize dialogues.
 
        :return: None
        """
        Model.__init__(self, **kwargs)
        FIPADialogues.__init__(self)
``` 
