# AEA Quick Start

If you want to create Autonomous Economic Agents (AEAs) that can act independently of constant user input and autonomously execute actions to achieve their objective, you can use the AEA framework.

<iframe width="560" height="315" src="https://www.youtube.com/embed/mwkAUh-_uxA" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

This example will take you through a simple AEA to familiarise you with the basics of the framework.

## Echo Skill Demo

This is a simple demo that introduces you to the main components of an AEA.

The fastest way to have your first AEA is to fetch one that already exists!

``` bash
aea fetch fetchai/my_first_aea:0.28.5
cd my_first_aea
```

To learn more about the folder structure of an AEA project read on <a href="../package-imports/">here</a>.

??? note "Alternatively: step by step install:"
    **Create a new AEA**

    First, create a new AEA project and enter it.

    ``` bash
    aea create my_first_aea
    cd my_first_aea
    ```

    **Add the stub connection**

    Second, add the stub connection to the project.

    ``` bash
    aea add connection fetchai/stub:0.21.3
    ```

    **Add the echo skill**

    Third, add the echo skill to the project.

    ``` bash
    aea add skill fetchai/echo:0.20.6
    ```

    This copies the <code>fetchai/echo:0.20.6</code> skill code containing the "behaviours", and "handlers" into the project, ready to run. The identifier of the skill <code>fetchai/echo:0.20.6</code> consists of the name of the author of the skill, followed by the skill name and its version.

### Echo Skill

Just like humans, AEAs can have _skills_ to achieve their tasks. As an agent developer, you can create skills to add to your own AEAs. You can also choose to publish your skills so others add them to their AEAs. More details on skills can be found on <a href="../skill/"> this page </a>.

The above agent has an <a href="https://aea-registry.fetch.ai/details/skill/fetchai/echo/latest" target="_blank">echo skill</a>, fetched from <a href="https://aea-registry.fetch.ai" target="_blank">the registry</a>, which simply echoes any messages it receives back to its sender.

### Communication via Envelopes and Messages

AEAs use envelopes containing messages for communication. To learn more, check out the <a href="../core-components-1/">next section</a>.

### Stub Connection

Besides skills, AEAs may have one or more _connections_ enabling them to interface with entities in the outside world. For example, an HTTP client connection allows an AEA to communicate with HTTP servers. To read more about connections see <a href="../connection/">this page</a>.

In this demo, we use the stub connection (`fetchai/stub0.15.0`) to send envelopes to and receive envelopes from the AEA.

A stub connection provides an I/O reader and writer. It uses two files for communication: one for incoming envelopes and the other for outgoing envelopes.

The AEA waits for a new envelope posted to the file `my_first_aea/input_file`, and adds a response to the file `my_first_aea/output_file`.

The format of each envelope is the following:

``` bash
TO,SENDER,PROTOCOL_ID,ENCODED_MESSAGE,
```

For example:

``` bash
recipient_aea,sender_aea,fetchai/default:1.0.0,\x08\x01\x12\x011*\x07\n\x05hello,
```

### Install AEA Dependencies

``` bash
aea install
```

### Add and Create a Private Key

All AEAs need a private key to run. Add one now:

``` bash
aea generate-key fetchai
aea add-key fetchai
```

### Run the AEA

Run the AEA.

``` bash
aea run
```

You will see the echo skill running in the terminal window (an output similar to the one below).

``` bash
    _     _____     _
   / \   | ____|   / \
  / _ \  |  _|    / _ \
 / ___ \ | |___  / ___ \
/_/   \_\|_____|/_/   \_\

v1.1.1

Starting AEA 'my_first_aea' in 'async' mode ...
info: Echo Handler: setup method called.
info: Echo Behaviour: setup method called.
info: [my_first_aea]: Start processing messages...
info: Echo Behaviour: act method called.
info: Echo Behaviour: act method called.
info: Echo Behaviour: act method called.
...
```

The framework first calls the `setup` methods in the skill's `Handler` and `Behaviour` classes in that order; after which it repeatedly calls the `act` method of `Behaviour` class. This is the main agent loop in action.

#### Add a Message to the Input File

You can send the AEA a message wrapped in an envelope using the CLI's `interact` command.

From a different terminal and same directory (ensure you are in the same virtual environment: `pipenv shell`):

``` bash
cd my_first_aea
aea interact
```

You can now send messages to this AEA via an interactive tool by typing anything into the prompt and hitting enter twice (once to send the message and once more to check for a response).

Let us send `hello` to this AEA (type `hello` and press enter twice). In the original terminal, you will see the `Echo Handler` dealing with this envelope and its contained message. You should see an output similar to the one below but with a different `dialogue_reference`.

``` bash
info: Echo Behaviour: act method called.
info: Echo Handler: message=Message(dialogue_reference=('1', '') message_id=1 target=0 performative=bytes content=b'hello'), sender=my_first_aea_interact
info: Echo Behaviour: act method called.
info: Echo Behaviour: act method called.
```

??? note "Manual approach:"
    Optionally, from a different terminal and same directory (i.e. the `my_first_aea` project), you can send the AEA a message wrapped in an envelope via the input file.

    ``` bash
    echo 'my_first_aea,sender_aea,fetchai/default:1.0.0,\x12\x10\x08\x01\x12\x011*\t*\x07\n\x05hello,' >> input_file
    ```

    You will see the <code>Echo Handler</code> dealing with the envelope and responding with the same message to the <code>output_file</code>, and also decoding the Base64 encrypted message in this case.

    ``` bash
    info: Echo Behaviour: act method called.
    Echo Handler: message=Message(sender=sender_aea,to=my_first_aea,content=b'hello',dialogue_reference=('1', ''),message_id=1,performative=bytes,target=0), sender=sender_aea
    info: Echo Behaviour: act method called.
    info: Echo Behaviour: act method called.
    ```
    
    Note, due to the dialogue reference having to be incremented, you can only send the above envelope once! This approach does not work in conjunction with the <code>aea interact</code> command.

### Stop the AEA

You can stop an AEA by pressing `CTRL C`.

Once you do, you should see the AEA being interrupted and then calling the `teardown()` methods:

``` bash
info: Echo Behaviour: act method called.
info: Echo Behaviour: act method called.
^C my_first_aea interrupted!
my_first_aea stopping ...
info: Echo Handler: teardown method called.
info: Echo Behaviour: teardown method called.
```

### Write a Test for the AEA

We can write an end-to-end test for the AEA utilising helper classes provided by the framework.

??? note "Writing tests:"
    The following test class replicates the preceding demo and tests its correct behaviour. The `AEATestCase` classes are a tool for AEA developers to write useful end-to-end tests of their AEAs.

    First, get the `packages` directory from the AEA repository (execute from the working directory which contains the <code>my_first_aea</code> folder):

    ``` bash
    svn export https://github.com/fetchai/agents-aea.git/trunk/packages
    ```

    Then write the test:
    
    ``` python
    import signal
    import time
    
    from aea.common import Address
    from aea.mail.base import Envelope
    from aea.protocols.base import Message
    from aea.protocols.dialogue.base import Dialogue
    
    from packages.fetchai.protocols.default.dialogues import DefaultDialogue, DefaultDialogues
    from packages.fetchai.protocols.default.message import DefaultMessage
    from packages.fetchai.protocols.default.serialization import DefaultSerializer
    from aea.test_tools.test_cases import AEATestCase
    
    
    class TestEchoSkill(AEATestCase):
        """Test that echo skill works."""
    
        def test_echo(self):
            """Run the echo skill sequence."""
            process = self.run_agent()
            is_running = self.is_running(process)
            assert is_running, "AEA not running within timeout!"
    
            # add sending and receiving envelope from input/output files
            sender_aea = "sender_aea"
            def role_from_first_message(
                message: Message, receiver_address: Address
            ) -> Dialogue.Role:
                return DefaultDialogue.Role.AGENT
            dialogues = DefaultDialogues(sender_aea, role_from_first_message)
            message_content = b"hello"
            message = DefaultMessage(
                performative=DefaultMessage.Performative.BYTES,
                dialogue_reference=dialogues.new_self_initiated_dialogue_reference(),
                content=message_content,
            )
            sent_envelope = Envelope(
                to=self.agent_name,
                sender=sender_aea,
                protocol_id=message.protocol_id,
                message=DefaultSerializer().encode(message),
            )
    
            self.send_envelope_to_agent(sent_envelope, self.agent_name)
    
            time.sleep(2.0)
            received_envelope = self.read_envelope_from_agent(self.agent_name)
    
            assert sent_envelope.to == received_envelope.sender
            assert sent_envelope.sender == received_envelope.to
            assert sent_envelope.protocol_id == received_envelope.protocol_id
            received_message = DefaultMessage.serializer.decode(received_envelope.message)
            assert message.content == received_message.content
    
            check_strings = (
                "Echo Handler: setup method called.",
                "Echo Behaviour: setup method called.",
                "Echo Behaviour: act method called.",
                "content={}".format(message_content),
            )
            missing_strings = self.missing_from_output(process, check_strings)
            assert (
                missing_strings == []
            ), "Strings {} didn't appear in agent output.".format(missing_strings)
    
            assert (
                self.is_successfully_terminated()
            ), "Echo agent wasn't successfully terminated."
    
    ```
    
    Place the above code into a file <code>test.py</code> in your AEA project directory (the same level as the <code>aea-config.yaml</code> file).
    
    To run, execute the following:

    ``` bash
    pytest test.py
    ```

### Delete the AEA

Delete the AEA from the parent directory (`cd ..` to go to the parent directory).

``` bash
aea delete my_first_aea
```

## Next Steps

To gain an understanding of the core components of the framework, please continue to the next page:

- <a href="../core-components-1/">Core components - Part 1</a>

For more demos, use cases or step-by-step guides, please check the following:

- <a href="../generic-skills">Generic skill use case</a>
- <a href='../weather-skills/'>Weather skill demo</a>
- <a href='../generic-skills-step-by-step/'> Generic step by step guide </a>
