/* -*- coding: utf-8 -*-
* ------------------------------------------------------------------------------
*
*   Copyright 2018-2019 Fetch.AI Limited
*
*   Licensed under the Apache License, Version 2.0 (the "License");
*   you may not use this file except in compliance with the License.
*   You may obtain a copy of the License at
*
*       http://www.apache.org/licenses/LICENSE-2.0
*
*   Unless required by applicable law or agreed to in writing, software
*   distributed under the License is distributed on an "AS IS" BASIS,
*   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
*   See the License for the specific language governing permissions and
*   limitations under the License.
*
* ------------------------------------------------------------------------------
 */

package main

import (
	"fmt"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/rs/zerolog"

	aea "libp2p_node/aea"
	"libp2p_node/dht/dhtclient"
	"libp2p_node/dht/dhtnode"
	"libp2p_node/dht/dhtpeer"
	"libp2p_node/utils"
)

const (
	libp2pNodePanicError      = "LIBP2P_NODE_PANIC_ERROR"
	libp2pMultiaddrsListStart = "MULTIADDRS_LIST_START"
	libp2pMultiaddrsListEnd   = "MULTIADDRS_LIST_END"
)

var logger zerolog.Logger = utils.NewDefaultLogger()

// panics if err is not nil
func check(err error) {
	if err != nil {
		fmt.Println(libp2pNodePanicError, ":", err.Error())
		panic(err)
	}
}

func main() {

	var err error

	// Initialize connection to aea
	agent := aea.AeaApi{}
	check(agent.Init())
	logger.Info().Msg("successfully initialized API to AEA!")

	// Get node configuration

	// aea agent address
	aeaAddr := agent.AeaAddress()

	// node address (ip and port)
	nodeHost, nodePort := agent.Address()

	// node public address, if set
	nodeHostPublic, nodePortPublic := agent.PublicAddress()

	// node delegate service address, if set
	_, nodePortDelegate := agent.DelegateAddress()

	// node monitoring service address, if set
	_, nodePortMonitoring := agent.MonitoringAddress()

	// node private key
	key := agent.PrivateKey()

	// entry peers
	entryPeers := agent.EntryPeers()

	// agent proof of representation
	record := agent.AgentRecord()

	// add artificial delay for agent registration
	registrationDelay := agent.RegistrationDelayInSeconds()

	// persist agent records to file
	storagePath := agent.RecordStoragePath()
	// libp2p node
	var node dhtnode.DHTNode

	// Run as a peer or just as a client
	if nodePortPublic == 0 {
		// if no external address is provided, run as a client
		opts := []dhtclient.Option{
			dhtclient.IdentityFromFetchAIKey(key),
			dhtclient.BootstrapFrom(entryPeers),
		}
		if record != nil {
			opts = append(opts, dhtclient.RegisterAgentAddress(record, agent.Connected))
		}
		node, err = dhtclient.New(opts...)
	} else {
		opts := []dhtpeer.Option{
			dhtpeer.LocalURI(nodeHost, nodePort),
			dhtpeer.PublicURI(nodeHostPublic, nodePortPublic),
			dhtpeer.IdentityFromFetchAIKey(key),
			dhtpeer.EnableRelayService(),
			dhtpeer.EnableDelegateService(nodePortDelegate),
			dhtpeer.BootstrapFrom(entryPeers),
		}
		if record != nil {
			opts = append(opts, dhtpeer.RegisterAgentAddress(record, agent.Connected))
		}
		if nodePortMonitoring != 0 {
			opts = append(opts, dhtpeer.EnablePrometheusMonitoring(nodePortMonitoring))
		}
		if registrationDelay != 0 {
			//lint:ignore ST1011 don't use unit-specific suffix "Seconds"
			durationSeconds := time.Duration(registrationDelay)
			opts = append(opts, dhtpeer.WithRegistrationDelay(durationSeconds*1000000*time.Microsecond))
		}
		if storagePath != "" {
			opts = append(opts, dhtpeer.StoreRecordsTo(storagePath))
		}

		if len(agent.MailboxUri()) > 0 {
			opts = append(opts, dhtpeer.EnableMailboxService(agent.MailboxUri()))
		}
		node, err = dhtpeer.New(opts...)
	}

	if err != nil {
		check(err)
	}
	defer node.Close()

	// Connect to the agent
	fmt.Println(libp2pMultiaddrsListStart) // keyword
	fmt.Println(node.MultiAddr())
	fmt.Println(libp2pMultiaddrsListEnd) // keyword

	check(agent.Connect())
	if aeaAddr != "" {
		logger.Info().Msg("successfully connected to AEA!")
	}

	// Receive envelopes from agent and forward to peer
	go func() {
		for envel := range agent.Queue() {
			envelope := envel
			logger.Info().Msgf("received envelope from agent: %s", envelope)
			err := node.RouteEnvelope(envelope)
			if err != nil {
				logger.Error().Msgf("Route envelope error: %s", err.Error())
			}
		}
	}()

	// Deliver envelopes received fro DHT to agent
	node.ProcessEnvelope(func(envel *aea.Envelope) error {
		return agent.Put(envel)
	})

	// Wait until Ctrl+C or a termination call is done.
	c := make(chan os.Signal, 1)
	signal.Notify(c, os.Interrupt)

	// SIGTERM for k8s graceful stop support
	signal.Notify(c, syscall.SIGTERM)

	//wait for termination
	<-c

	logger.Info().Msg("node stopped")
}
