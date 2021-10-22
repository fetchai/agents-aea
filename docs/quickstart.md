If you want to create Autonomous Economic Agents (AEAs) that can act independently of constant user input and autonomously execute actions to achieve their objective, you can use the AEA framework.

<iframe width="560" height="315" src="https://www.youtube.com/embed/mwkAUh-_uxA" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

This example will take you through a simple AEA to familiarise you with the basics of the framework.

## System Requirements

The AEA framework can be used on `Windows`, `Ubuntu/Debian` and `MacOS`.

You need <a href="https://www.python.org/downloads/" target="_blank">Python 3.6</a> or higher as well as <a href="https://golang.org/dl/" target="_blank">Go 1.14.2</a> or higher installed.

​GCC installation is required:
* Ubuntu: `apt-get install gcc`
* Windows (with <a href="https://chocolatey.org/" target="_blank">`choco`</a>
 installed): `choco install mingw`
* MacOS X (with home brew): `brew install gcc`

### Option 1: Manual system preparation

Install a compatible Python and Go version on your system (see <a href="https://realpython.com/installing-python/" target="_blank">this external resource</a> for a comprehensive guide).

<details><summary>Manual approach</summary>

The following hints can help:

<ul>
<li>To install Go, follow the official guide, depending on your platform <a href="https://golang.org/doc/install" target="_blank">here</a></li>

<li>Python is already included by default on 
many Linux distributions (e.g. Ubuntu), as well as MacOS.
To check you have the right version, open a terminal and run: 
``` bash
python3 --version
```
</li>

<li>To install Python on Windows machines, you can download a specific release <a href="https://www.python.org/downloads/" target="_blank">here</a>.</li>

<li>Ubuntu/Debian systems only: install Python headers,
  depending on the Python version you have installed on your machine.
  E.g. for Python 3.7: 
``` bash
sudo apt-get install python3.7-dev
```
</li>

<li>Windows users: install <a href="https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2019" target="_blank">tools for Visual Studio</a>.</li>
</ul>

</details>

### Option 2: Using an automated install script

We provide a script to automatically install all framework dependencies and the framework itself. This means that if you follow this option, you can skip the <a href="../quickstart#installation">installation step</a> that comes later on this page.

<details><summary>Automated install script approach</summary>

On MacOS or Ubuntu run the following commands to download and install:

``` bash
curl https://raw.githubusercontent.com/fetchai/agents-aea/main/scripts/install.sh --output install.sh
chmod +x install.sh
./install.sh
```

On Windows: download <a href="https://raw.githubusercontent.com/fetchai/agents-aea/main/scripts/install.ps1" target="_blank">https://raw.githubusercontent.com/fetchai/agents-aea/main/scripts/install.ps1</a>, then run <code>install.ps1</code> with the PowerShell terminal.

</details>

### Option 3: Using Docker
​
We also provide a Docker image with all the needed dependencies.

<details><summary>Docker approach</summary>

To use the image you will first have to pull it and than run it with your current local directory mounted as a docker volume. This allows you to keep your agents local while working on them from within the docker container.

To pull:

``` bash
docker pull fetchai/aea-user:latest
```

To run the image on Linux and MacOs:

``` bash
docker run -it -v $(pwd):/agents --workdir=/agents fetchai/aea-user:latest 
```

And on Windows:

``` bash
docker run -it -v %cd%:/agents --workdir=/agents fetchai/aea-user:latest 
```

Once successfully logged into the docker container, 
you can follow the rest of the guide the same way as if not using docker.
​
</details>

## Preliminaries

Ensure, you are in a clean working directory:

- either you create it manually `mkdir my_aea_projects/ && cd my_aea_projects/`, then add an empty directory called `packages` with the following command `mkdir packages/`,

- or you clone the template repo as described in `Approach 1` in the <a href="../development-setup#approach-1">development setup</a> guide.

At this point, when typing `ls` you should see a single folder called `packages` in your working environment. This will act as your local registry for AEA components.

Unless you are using the docker image, we highly recommend using a virtual environment to ensure consistency across dependencies.

Check that you have <a href="https://github.com/pypa/pipenv" target="_blank">`pipenv`</a>.

``` bash
which pipenv
```

If you don't have it, install it. Instructions are <a href="https://pypi.org/project/pipenv/" target="_blank">here</a>.

Once installed, create a new environment and open it (here we use Python 3.7 but the AEA framework supports any Python >= 3.6).

``` bash
touch Pipfile && pipenv --python 3.7 && pipenv shell
```


## Installation

The following installs the entire AEA package which also includes a <a href="../cli-commands">command-line interface (CLI)</a>. (You can skip this step if you used the install script above: <a href="../quickstart#option-2-using-an-automated-install-script">Option 2 </a>.)

``` bash
pip install aea[all]
```

If you are using `zsh` rather than `bash` type
``` zsh
pip install 'aea[all]'
```

If the installation steps fail, it might be a dependency issue. Make sure you have followed all the relevant system specific steps above under `System Requirements`.

## Setup author name

AEAs are composed from components. AEAs and AEA components can be developed by anyone and pushed to the <a href="https://aea-registry.fetch.ai" target="_blank">AEA registry</a> for others to use. To use the registry, we need to register an author name.

You can set up your author name using the `init` command:
``` bash
aea init
```

This is your unique author (or developer) name in the AEA ecosystem.

You should see a similar output (with your input instead of the sample username and email):
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

v1.1.0

AEA configurations successfully initialized: {'author': 'fetchai'}
```

<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>If you would rather not create an account on the registry at this point, then run <code>aea init --local</code> instead.</p>
</div>

## Echo skill demo

This is a simple demo that introduces you to the main components of an AEA. 

The fastest way to have your first AEA is to fetch one that already exists!

``` bash
aea fetch fetchai/my_first_aea:0.27.0
cd my_first_aea
```

To learn more about the folder structure of an AEA project read on <a href="../package-imports/">here</a>.

<details><summary>Alternatively: step by step install</summary>

<b> Create a new AEA </b>
<br>
First, create a new AEA project and enter it.
``` bash
aea create my_first_aea
cd my_first_aea
```
<br>
<b>Add the stub connection</b>
<br>
Second, add the stub connection to the project.
``` bash
aea add connection fetchai/stub:0.21.0
```
<br>
<b>Add the echo skill</b>
<br>
Third, add the echo skill to the project.
``` bash
aea add skill fetchai/echo:0.19.0
```
This copies the <code>fetchai/echo:0.19.0</code> skill code containing the "behaviours", and "handlers" into the project, ready to run. The identifier of the skill <code>fetchai/echo:0.19.0</code> consists of the name of the author of the skill, followed by the skill name and its version.
</details>

### Echo skill

Just like humans, AEAs can have _skills_ to achieve their tasks. As an agent developer, you can create skills to add to your own AEAs. You can also choose to publish your skills so others add them to their AEAs. More details on skills can be found on <a href="../skill/"> this page </a>.

The above agent has an <a href="https://aea-registry.fetch.ai/details/skill/fetchai/echo/latest" target="_blank">echo skill</a>, fetched from <a href="https://aea-registry.fetch.ai" target="_blank">the registry</a>, which simply echoes any messages it receives back to its sender.

### Communication via envelopes and messages

AEAs use envelopes containing messages for communication. To learn more, check out the <a href="../core-components-1/">next section</a>.

### Stub connection

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

### Install AEA dependencies

``` bash
aea install
```

### Add and create a private key

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

v1.1.0

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

#### Add a message to the input file

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

<details><summary>Manual approach</summary>

Optionally, from a different terminal and same directory (i.e. the <code>my_first_aea</code> project), you can send the AEA a message wrapped in an envelope via the input file.

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

</details>

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

### Write a test for the AEA

We can write an end-to-end test for the AEA utilising helper classes provided by the framework.

<details><summary>Writing tests</summary>

The following test class replicates the preceding demo and tests it's correct behaviour. The <code>AEATestCase</code> classes are a tool for AEA developers to write useful end-to-end tests of their AEAs.

First, get the packages directory from the AEA repository (execute from the working directory which contains the <code>my_first_aea</code> folder):

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

</details>

### Delete the AEA

Delete the AEA from the parent directory (`cd ..` to go to the parent directory).

``` bash
aea delete my_first_aea
```

## Next steps

To gain an understanding of the core components of the framework, please continue to the next page:

- <a href="../core-components-1/">Core components - Part 1</a>

For more demos, use cases or step by step guides, please check the following:

- <a href="../generic-skills">Generic skill use case</a>
- <a href='../weather-skills/'>Weather skill demo</a>
- <a href='../generic-skills-step-by-step/'> Generic step by step guide </a>

<br />
