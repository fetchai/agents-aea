The AEA TAC - trading agent competition - skills demonstrate an interaction between multiple AEAs in a game.

There are two types of agents:

* The tac controller which coordinates the game.
* The participant agents which compete in the game.

## Prerequisites

Make sure you have the latest `aea` version.

``` bash
aea --version
```

If not, update with the following.

``` bash
pip install aea[all] --force --no-cache-dir
```

## Demo preliminaries

Follow the Preliminaries and Installation instructions <a href="../quickstart" target=_blank>here</a>.


Download the packages and scripts directories.
``` bash
svn export https://github.com/fetchai/agents-aea.git/trunk/packages
svn export https://github.com/fetchai/agents-aea.git/trunk/scripts
```

## Launch an OEF node
In a separate terminal, launch a local OEF node (for search and discovery).
``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```

Keep it running for all the following demos.

## Demo 1: no ledger transactions


### Create the TAC controller AEA
In the root directory, create the tac controller AEA.
``` bash
aea create tac_controller
```

### Add the tac control skill
``` bash
cd tac_controller
aea add skill tac_control
```

### Update the game parameters
You can change the game parameters in `skill.yaml` under `Parameters`.

You must set the start time to a point in the future `start_time: Nov 10 2019  10:40AM`.

### Run the TAC controller AEA
``` bash
aea run
```

### Create the TAC participants AEA
In a separate terminal, in the root directory, create the tac participant AEA.
``` bash
aea create tac_participant_one
aea create tac_participant_two
```

### Add the tac participation skill to participant one
``` bash
cd tac_participant_one
aea add skill tac_participation
```

### Add the tac participation skill to participant two
``` bash
cd tac_participant_two
aea add skill tac_participation
```

### Run both the TAC participant AEAs
``` bash
aea run
```