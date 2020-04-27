Demonstrating interactions between AEAs and and an instance of Aries Cloud Agent (ACA).

### Discussion

This demo illustrates how an AEA may connect to an Aries Cloud Agent (ACA). 

Hyperledger Aries Cloud Agent is a foundation for building self-sovereign identity/decentralized identity services using verifiable credentials. You can read more about Hyperledger <a href="https://www.hyperledger.org" target=_blank>here</a> and the Aries project <a href="https://github.com/hyperledger/aries-cloudagent-python" target=_blank>here</a>.

In this demo, you will learn how an AEA could connect with an ACA, to send it administrative commands (e.g. issue verifiable credential to another AEA) and receive DID related notifications (e.g. receive a request for a credential proof from another AEA). 

## Preparation instructions

### Dependencies

Follow the <a href="../quickstart/#preliminaries">Preliminaries</a> and <a href="../quickstart/#installation">Installation</a> sections from the AEA quick start.

## ACA

### Install ACA

Install Aries cloud-agents (run `pip install aries-cloudagent` or see <a href="https://github.com/hyperledger/aries-cloudagent-python#install" target=_blank>here</a>) if you do not have it on your machine.

## Run the demo test

Run the following test file using PyTest:

``` bash
PyTest tests/test_examples/test_http_client_connection_to_aries_cloud_agent.py
```

You should see that the two tests pass.

## Demo code

Take a look at the test file you ran above `tests/test_examples/test_http_client_connection_to_aries_cloud_agent.py`. 

The main class is `TestAEAToACA`. The `setup_class` method initialises the scenario. 

``` python
@pytest.mark.asyncio
class TestAEAToACA:
    """End-to-end test for an AEA connecting to an ACA via the http client connection."""

    @classmethod
    def setup_class(cls):
        """Initialise the class."""
        cls.aca_admin_address = "127.0.0.1"
        cls.aca_admin_port = 8020
```

The address and port fields `cls.aca_admin_address` and `cls.aca_admin_port` specify where the ACA should listen to receive administrative commands from the AEA.

The following runs an ACA:

``` python
cls.process = subprocess.Popen(  # nosec
            [
                "aca-py",
                "start",
                "--admin",
                cls.aca_admin_address,
                str(cls.aca_admin_port),
                "--admin-insecure-mode",
                "--inbound-transport",
                "http",
                "0.0.0.0",
                "8000",
                "--outbound-transport",
                "http",
            ]
        )
```

Now take a look at the following method. This is where the demo resides. It first creates an AEA programmatically.

``` python
    @pytest.mark.asyncio
    async def test_end_to_end_aea_aca(self):
        # AEA components
        ledger_apis = LedgerApis({}, FETCHAI)
        wallet = Wallet({FETCHAI: FETCHAI_PRIVATE_KEY_FILE})
        identity = Identity(
            name="my_aea_1",
            address=wallet.addresses.get(FETCHAI),
            default_address_key=FETCHAI,
        )
        http_client_connection = HTTPClientConnection(
            address=self.aea_address,
            provider_address=self.aca_admin_address,
            provider_port=self.aca_admin_port,
        )
        resources = Resources()

        # create AEA
        aea = AEA(identity, [http_client_connection], wallet, ledger_apis, resources)
```

It then adds the HTTP protocol to the AEA. THe HTTP protocol defines the format of HTTP interactions (e.g. HTTP Request and Response). 

``` python
        # Add http protocol to AEA resources
        http_protocol_configuration = ProtocolConfig.from_json(
            yaml.safe_load(
                open(
                    os.path.join(
                        self.cwd,
                        "packages",
                        "fetchai",
                        "protocols",
                        "http",
                        "protocol.yaml",
                    )
                )
            )
        )
        http_protocol = Protocol(http_protocol_configuration, HttpSerializer())
        resources.add_protocol(http_protocol)
```

Then, the request message and envelope is created:

``` python
        # Request message & envelope
        request_http_message = HttpMessage(
            dialogue_reference=("", ""),
            target=0,
            message_id=1,
            performative=HttpMessage.Performative.REQUEST,
            method="GET",
            url="http://{}:{}/status".format(
                self.aca_admin_address, self.aca_admin_port
            ),
            headers="",
            version="",
            bodyy=b"",
        )
        request_envelope = Envelope(
            to="ACA",
            sender="AEA",
            protocol_id=HTTP_PROTOCOL_PUBLIC_ID,
            message=HttpSerializer().encode(request_http_message),
        )
```

Note that the `performative` is set to `HttpMessage.Performative.REQUEST`, the method `GET` corresponds with HTTP GET method, and `url` is where the request is sent. This is the location the ACA is listening for administrative commands. 

In the following part, the AEA is started in another thread `t_aea = Thread(target=aea.start)`, the HTTP request message created above is placed in the agent's outbox `aea.outbox.put(request_envelope)` to be sent to the ACA, and the received response is checked for success (e.g. `assert aea_handler.handled_message.status_text == "OK"`).

``` python
        # start AEA thread
        t_aea = Thread(target=aea.start)
        try:
            t_aea.start()
            time.sleep(1.0)
            aea.outbox.put(request_envelope)
            time.sleep(5.0)
            assert (
                aea_handler.handled_message.performative
                == HttpMessage.Performative.RESPONSE
            )
            assert aea_handler.handled_message.version == ""
            assert aea_handler.handled_message.status_code == 200
            assert aea_handler.handled_message.status_text == "OK"
            assert aea_handler.handled_message.headers is not None
            assert aea_handler.handled_message.version is not None
        finally:
            aea.stop()
            t_aea.join()
```

Note that the response from the ACA is caught by the `AEAHandler` class which just saves the handled message.

In the above interaction, and in general, the HTTP client connection the added to the AEA, takes care of the translation between messages and envelopes in the AEA world and the HTTP request/response format in the HTTP connection with the ACA.
