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

package aealite

import (
	"os"
	"testing"

	connections "aealite/connections"
	protocols "aealite/protocols"
)

const (
	EnvTestFile = "test_env_file.env"
)

var (
	ledgerId       = "fetchai"
	address        = "fetch1x9v67meyfq4pkgy2n2yf6797cfkul327kpclqr"
	publicKey      = "02ac514ba70de60ed5c30f90e3acdfc958ecb416d9676706bf013228abfb2c2816"
	privateKey     = "6d8d2b87d987641e2ca3f1991c1cccf08a118759e81fabdbf7e8484f27af015e"
	testProtocolId = "test_protocol_id"
	testMessage    = []byte{0x00}
)

// TestAgent apis
func TestAgent(t *testing.T) {
	os.Args = []string{"cmd", EnvTestFile}

	agent := Agent{}
	if agent.Connection != nil {
		t.Fatal("Agent connection not empty")
	}

	// set p2p client
	agent.Connection = &connections.P2PClientApi{}

	// initialise
	err := agent.InitFromEnv("test_env_file.env")

	if err != nil {
		t.Fatal("Failed to initialise agent", err)
	}

	if agent.Wallet == nil {
		t.Fatal("Wallet not set on Agent")
	}

	if agent.Wallet.LedgerId != ledgerId {
		t.Fatal("Wallet.LedgerId not set")
	}

	if agent.Wallet.Address != address {
		t.Fatal("Wallet.Address not set")
	}

	if agent.Wallet.PublicKey != publicKey {
		t.Fatal("Wallet.PublicKey not set")
	}

	if agent.Wallet.PrivateKey != privateKey {
		t.Fatal("Wallet.PrivateKey not set")
	}

	if !agent.Connection.Initialised() {
		t.Fatal("connection not initialised")
	}

	err = agent.Start()

	if err != nil {
		t.Fatal("Failed to start agent", err)
	}

	outEnvelope := &protocols.Envelope{
		To:         agent.Address(),
		Sender:     agent.Address(),
		ProtocolId: testProtocolId,
		Message:    testMessage,
	}

	err = agent.Put(outEnvelope)

	if err != nil {
		t.Fatal("Failed to send envelope", err)
	}

	inEnvelope := agent.Get()

	if inEnvelope == nil {
		t.Fatal("Failed to get envelope")
	}

	if (inEnvelope.Sender != outEnvelope.Sender) || (inEnvelope.To != outEnvelope.To) {
		t.Fatal("Envelopes don't match")
	}

	err = agent.Stop()
	if err != nil {
		t.Fatal("Failed to stop agent", err)
	}
}
