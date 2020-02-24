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

Once installed, create a new environment and open it.

``` bash
touch Pipfile && pipenv --python 3.7 && pipenv shell
```

### Installing docker

At some point, you will need [Docker](https://www.docker.com/) installed on your machine 
(e.g. to run an OEF Node).
 
### Download the scripts and packages directories

Download folders containing examples, scripts and packages:
``` bash
svn export https://github.com/fetchai/agents-aea.git/trunk/examples
svn export https://github.com/fetchai/agents-aea.git/trunk/scripts
svn export https://github.com/fetchai/agents-aea.git/trunk/packages
```
You can install the `svn` command with (`brew install subversion` or `sudo apt-get install subversion`).

## Installation

The following installs the entire AEA package which also includes a command-line interface (CLI).

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


## Echo skill demo

The echo skill is a simple demo that introduces you to the main business logic components of an AEA. 
The fastest way to create your first AEA is to fetch it! 

If you want to follow a step by step guide we show you how to do it at the end of the file.

``` bash
aea fetch fetchai/my_first_aea:0.1.0
cd my_first_aea
```

## Usage of the stub connection	

AEAs use messages for communication. We use a stub connection to send messages to and receive messages from the AEA.		
		
The stub connection is already added to the AEA by default.		
		
A stub connection provides an I/O reader and writer. It uses two files for communication: one for incoming messages and the other for outgoing messages. Each line contains an encoded envelope.		
		
The AEA waits for new messages posted to the file `my_first_aea/input_file`, and adds a response to the file `my_first_aea/output_file`.		
		
The format of each line is the following:		
		
``` bash		
TO,SENDER,PROTOCOL_ID,ENCODED_MESSAGE		
```
         		
For example:		
		
``` bash		
recipient_aea,sender_aea,fetchai/default:0.1.0,{"type": "bytes", "content": "aGVsbG8="}
```

## Run the AEA

Run the AEA with the default `stub` connection.

``` bash
aea run
```

or 

``` bash
aea run --connections fetchai/stub:0.1.0
```

You will see the echo skill running in the terminal window.

``` bash
info: Echo Behaviour: act method called.
info: Echo Behaviour: act method called.
info: Echo Behaviour: act method called.
```

The framework first calls the `setup` method on the `Handler`, and `Behaviour` code in that order; after which it repeatedly calls the Behaviour method act. This is the main agent loop in action.

Let's look at the `Handler` in more depth.

### Add a message to the input file

From a different terminal and same directory, we send the AEA a message wrapped in an envelope via the input file.

``` bash
echo 'my_first_aea,sender_aea,fetchai/default:0.1.0,{"type": "bytes", "content": "aGVsbG8="}' >> input_file
```

You will see the `Echo Handler` dealing with the envelope and responding with the same message to the `output_file`, and also decoding the Base64 encrypted message in this case.

``` bash
info: Echo Behaviour: act method called.
info: Echo Handler: message=Message(type=bytes content=b'hello'), sender=sender_aea
info: Echo Behaviour: act method called.
info: Echo Behaviour: act method called.
```

## Stop the AEA

Stop the AEA by pressing `CTRL C`

## Delete the AEA

Delete the AEA from the parent directory (`cd ..` to go to the parent directory).

``` bash
aea delete my_first_aea
```

For more detailed analysis of the core components of the framework, please check the following:

- <a href="/aea/core-components/">Core components</a>

For more demos, use cases or step by step guides, please check the following:

- <a href="/aea/generic-skills">Generic skill use case</a>
- <a href='/aea/weather-skills/'>Weather skill demo</a> 
- <a href='/aea/thermometer-skills-step-by-step/'> Thermometer step by step guide </a>

<br />

<details><summary>Step by step install</summary>

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
```bash
aea add skill fetchai/echo:0.1.0		
```		
This copies the `echo` skill code containing the "behaviours", and "handlers" into the skill, ready to run. The identifier of the skill `fetchai/echo:0.1.0` consists of the name of the author of the skill, followed by the skill name and its version.		
</details>
