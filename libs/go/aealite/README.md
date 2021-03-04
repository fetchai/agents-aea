# aealite

AEALite is a lightweight implementation of an AEA library in Golang.


## Usage example

``` golang
package main

import (
	"log"

	aea "aealite"
	connections "aealite/connections"
)

func main() {

	var err error

	logger.Info().Msg("Agent starting ...")

	// Create agent
	agent := aea.Agent{}

	// Set connection
	agent.connection = &connections.P2PClientApi{}

	// Initialise agent from environment file (first arg to process)
	err = agent.InitFromEnv()
	if err != nil {
		log.Fatal("Failed to initialise agent", err)
	}
	logger.Info().Msg("successfully initialized AEA!")

	err = agent.Start()
	if err != nil {
		log.Fatal("Failed to start agent", err)
	}
	logger.Info().Msg("successfully started AEA!")

	// // Send envelope to target
	// agent.Put(envel)

	// // Print out received envelopes
	// go func() {
	// 	for envel := range agent.Queue() {
	// 		envelope := envel
	// 		logger.Info().Msgf("received envelope: %s", envelope)
	// 	}
	// }()

	// Wait until Ctrl+C or a termination call is done.
	c := make(chan os.Signal, 1)
	signal.Notify(c, os.Interrupt)
	<-c

	err = agent.Stop()
	if err != nil {
		log.Info("Failed to stop agent", err)
	}
	logger.Info().Msg("Agent stopped")
}
```

## Development

To run all tests run:

``` bash
go test -p 1 -timeout 0 -count 1 -v ./...
```

To lint:

``` bash
golines . -w
golangci-lint run
```

To generate protoc files:

``` bash
cd ..
protoc -I="aealite/protocols/" --go_out="." aealite/protocols/acn.proto
protoc -I="aealite/protocols/" --go_out="." aealite/protocols/base.proto
cd aealite
```