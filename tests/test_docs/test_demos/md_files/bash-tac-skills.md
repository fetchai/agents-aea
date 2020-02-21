``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```

``` bash
aea create tac_controller
cd tac_controller
```

``` bash
aea add connection fetchai/oef:0.1.0
aea add skill fetchai/tac_control:0.1.0
aea install
```

``` bash
aea config set agent.default_ledger ethereum
```

``` bash
aea config get skills.tac_control.models.parameters.args.start_time
aea config set skills.tac_control.models.parameters.args.start_time '21 12 2019  07:14'
```

``` bash
aea run --connections fetchai/oef:0.1.0
```

``` bash
aea create tac_participant_one
aea create tac_participant_two
```

``` bash
cd tac_participant_one
aea add connection fetchai/oef:0.1.0
aea add skill fetchai/tac_participation:0.1.0
aea add skill fetchai/tac_negotiation:0.1.0
aea install
```

``` bash
aea config set agent.default_ledger ethereum
```

``` bash
cd tac_participant_two
aea add connection fetchai/oef:0.1.0
aea add skill fetchai/tac_participation:0.1.0
aea add skill fetchai/tac_negotiation:0.1.0
aea install
```

``` bash
aea config set agent.default_ledger ethereum
```

``` bash
aea run --connections fetchai/oef:0.1.0
```

