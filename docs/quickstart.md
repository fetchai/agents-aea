If you want to create Autonomous Economic Agents (AEAs) that can act independently of constant user input and autonomously execute actions to achieve their objective,
you can use the Fetch.ai AEA framework.

<iframe width="560" height="315" src="https://www.youtube.com/embed/mwkAUh-_uxA" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

This example will take you through the simplest AEA in order to make you familiar with the framework.

## Preliminaries

Create and enter into a new working directory.

``` bash
mkdir my_aea_projects/
cd my_aea_projects/
```

We highly recommend using a virtual environment to ensure consistency across dependencies.

Check that you have [`pipenv`](https://github.com/pypa/pipenv).

``` bash
which pipenv
```

If you don't have it, install it. Instructions are <a href="https://pypi.org/project/pipenv/" target=_blank>here</a>.

Once installed, create a new environment and open it (here we use Python 3.7 but the AEA framework supports any Python >= 3.6).

``` bash
touch Pipfile && pipenv --python 3.7 && pipenv shell
```

### Installing docker

<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>For the purpose of the quickstart only, you can skip installation of docker.</p>
</div>

At some point, you will need [Docker](https://www.docker.com/) installed on your machine
(e.g. to run an [OEF search and communication node](../oef-ledger)).

### Download the scripts and examples directories

<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>For the purpose of the quickstart only, you can skip downloading the scripts and examples directories.</p>
</div>

Download folders containing examples and scripts:
``` bash
svn export https://github.com/fetchai/agents-aea.git/trunk/examples
svn export https://github.com/fetchai/agents-aea.git/trunk/scripts
```
You can install the `svn` command with (`brew install subversion` or `sudo apt-get install subversion`).

## Installation

The following installs the entire AEA package which also includes a [command-line interface (CLI)](../cli-commands).

``` bash
pip install aea[all]
```

If you are using `zsh` rather than `bash` type
``` zsh
pip install 'aea[all]'
```

### Known issues

If the installation steps fail, it might be a dependency issue.

The following hints can help:

- Ubuntu/Debian systems only: install Python 3.7 headers.
``` bash
sudo apt-get install python3.7-dev
```

- Windows users: install <a href="https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2019" target=_blank>tools for Visual Studio</a>.

## Setup Author name

You can now setup your author name:
``` bash
aea init
```

This is your unique author name in the Fetch.ai ecosystem.

You should see a similar output (with your input replacing the sample input):
``` bash
Do you have a Registry account? [y/N]: n
Create a new account on the Registry now:
Username: fetchai
Email: hello@fetch.ai
Password:
Please make sure that passwords are equal.
Confirm password:
    _     _____     _
   / \   | ____|   / \
  / _ \  |  _|    / _ \
 / ___ \ | |___  / ___ \
/_/   \_\|_____|/_/   \_\

v0.5.0

AEA configurations successfully initialized: {'author': 'fetchai'}
```

<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>If you would rather not create an account on the registry at this point, then run `aea init --local` instead.</p>
</div>

## Echo skill demo

The echo skill is a simple demo that introduces you to the main business logic components of an AEA. The fastest way to create your first AEA is to fetch it!

If you want to follow a step by step guide we show you how to do it at the end of the file.

``` bash
aea fetch fetchai/my_first_aea:0.6.0
cd my_first_aea
```

To learn more about the folder structure of an AEA project read on [here](../package-imports).

<details><summary>Alternatively: step by step install</summary>

<b> Create a new AEA </b>
<br>
First, create a new AEA project and enter it.
``` bash
aea create my_first_aea
cd my_first_aea
```
<br>
<b>Add the echo skill</b>
<br>
Second, add the echo skill to the project.
``` bash
aea add skill fetchai/echo:0.3.0
```
This copies the `fetchai/echo:0.3.0` skill code containing the "behaviours", and "handlers" into the project, ready to run. The identifier of the skill `fetchai/echo:0.3.0` consists of the name of the author of the skill, followed by the skill name and its version.
</details>

## Usage of the stub connection

AEAs use envelopes containing messages for communication. We use a stub connection to send envelopes to and receive envelopes from the AEA.

The stub connection is already added to the AEA by default.

A stub connection provides an I/O reader and writer. It uses two files for communication: one for incoming envelopes and the other for outgoing envelopes.

The AEA waits for a new envelope posted to the file `my_first_aea/input_file`, and adds a response to the file `my_first_aea/output_file`.

The format of each envelope is the following:

``` bash
TO,SENDER,PROTOCOL_ID,ENCODED_MESSAGE,
```

For example:

``` bash
recipient_aea,sender_aea,fetchai/default:0.3.0,\x08\x01*\x07\n\x05hello,
```

## Run the AEA

Run the AEA with the default `fetchai/stub:0.6.0` connection.

``` bash
aea run
```

or

``` bash
aea run --connections fetchai/stub:0.6.0
```

You will see the echo skill running in the terminal window.

``` bash
    _     _____     _
   / \   | ____|   / \
  / _ \  |  _|    / _ \
 / ___ \ | |___  / ___ \
/_/   \_\|_____|/_/   \_\

v0.5.0

Starting AEA 'my_first_aea' in 'async' mode ...
info: Echo Handler: setup method called.
info: Echo Behaviour: setup method called.
info: [my_first_aea]: Start processing messages...
info: Echo Behaviour: act method called.
info: Echo Behaviour: act method called.
info: Echo Behaviour: act method called.
...
```

The framework first calls the `setup` method on the `Handler`, and `Behaviour` code in that order; after which it repeatedly calls the Behaviour method act. This is the main agent loop in action.

Let's look at the `Handler` in more depth.

### Add a message to the input file

From a different terminal and same directory, we send the AEA a message wrapped in an envelope via the input file.

``` bash
echo 'my_first_aea,sender_aea,fetchai/default:0.3.0,\x08\x01*\x07\n\x05hello,' >> input_file
```

You will see the `Echo Handler` dealing with the envelope and responding with the same message to the `output_file`, and also decoding the Base64 encrypted message in this case.

``` bash
info: Echo Behaviour: act method called.
info: Echo Handler: message=Message(dialogue_reference=('', '') message_id=1 target=0 performative=bytes content=b'hello'), sender=sender_aea
info: Echo Behaviour: act method called.
info: Echo Behaviour: act method called.
```

<details><summary>CLI interact command</summary>

Optionally, use the CLI interact command from a different terminal:

``` bash
aea interact
```

You can then send the AEA messages via an interactive tool by typing `hello` into the prompt and hitting enter twice (once to send, once more to check for a response).

</details>

## Stop the AEA

Stop the AEA by pressing `CTRL C`

You should see the AEA being interrupted and then calling the `teardown()` methods:

``` bash
info: Echo Behaviour: act method called.
info: Echo Behaviour: act method called.
^C my_first_aea interrupted!
my_first_aea stopping ...
info: Echo Handler: teardown method called.
info: Echo Behaviour: teardown method called.
```

## Write a test for the AEA

We can write an end-to-end test for the AEA utilising helper classes provided by the framework.

<details><summary>Writing tests</summary>

The following test class replicates the preceding demo and tests it's correct behaviour. The `AEATestCase` classes are a tool for AEA developers to write useful end-to-end tests of their AEAs.

``` python
import signal
import time

from aea.mail.base import Envelope
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer
from aea.test_tools.test_cases import AEATestCase


class TestEchoSkill(AEATestCase):
    """Test that echo skill works."""

    def test_echo(self):
        """Run the echo skill sequence."""
        process = self.run_agent()
        is_running = self.is_running(process)
        assert is_running, "AEA not running within timeout!"

        # add sending and receiving envelope from input/output files
        message_content = b"hello"
        message = DefaultMessage(
            performative=DefaultMessage.Performative.BYTES, content=message_content,
        )
        sent_envelope = Envelope(
            to=self.agent_name,
            sender="sender_aea",
            protocol_id=message.protocol_id,
            message=DefaultSerializer().encode(message),
        )

        self.send_envelope_to_agent(sent_envelope, self.agent_name)

        time.sleep(2.0)
        received_envelope = self.read_envelope_from_agent(self.agent_name)

        assert sent_envelope.to == received_envelope.sender
        assert sent_envelope.sender == received_envelope.to
        assert sent_envelope.protocol_id == received_envelope.protocol_id
        assert sent_envelope.message == received_envelope.message

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

Place the above code into a file `test.py` in your AEA project directory (the same level as the `aea-config.yaml` file).

To run, execute the following:

``` python
pytest test.py
```

</details>

## Delete the AEA

Delete the AEA from the parent directory (`cd ..` to go to the parent directory).

``` bash
aea delete my_first_aea
```

## Next steps

To gain an understanding of the core components of the framework, please continue to the next step of 'Getting Started':

- <a href="../core-components/">Core components</a>

For more demos, use cases or step by step guides, please check the following:

- <a href="../generic-skills">Generic skill use case</a>
- <a href='../weather-skills/'>Weather skill demo</a>
- <a href='../generic-skills-step-by-step/'> Generic step by step guide </a>

<br />
