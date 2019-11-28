The AEA TAC - trading agent competition - skills demonstrate an interaction between multiple AEAs in a game.

There are two types of agents:

* The tac controller which coordinates the game.
* The participant agents which compete in the game.

### Dependencies

Follow the <a href="../quickstart/#preliminaries">Preliminaries</a> and <a href="../quickstart/#installation">Installation</a> sections from the AEA quick start.


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
You can change the game parameters in `tac_controller/skills/tac_control/skill.yaml` under `Parameters`.

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
aea add skill tac_negotiation
```

### Add the tac participation skill to participant two
``` bash
cd tac_participant_two
aea add skill tac_participation
aea add skill tac_negotiation
```

### Run both the TAC participant AEAs
``` bash
aea run
```

!!!	Note
	Currently, the agents cannot settle their trades. Updates coming soon!
