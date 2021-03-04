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
	ledger_id        = "fetchai"
	address          = "fetch1x9v67meyfq4pkgy2n2yf6797cfkul327kpclqr"
	public_key       = "02ac514ba70de60ed5c30f90e3acdfc958ecb416d9676706bf013228abfb2c2816"
	private_key      = "6d8d2b87d987641e2ca3f1991c1cccf08a118759e81fabdbf7e8484f27af015e"
	test_protocol_id = "test_protocol_id"
	test_message     = []byte{0x00}
)

// TestAgent apis
func TestAgent(t *testing.T) {
	os.Args = []string{"cmd", EnvTestFile}

	agent := Agent{}
	if agent.connection != nil {
		t.Fatal("Agent connection not empty")
	}

	// set p2p client
	agent.connection = &connections.P2PClientApi{}

	// initialise
	err := agent.InitFromEnv()

	if err != nil {
		t.Fatal("Failed to initialise agent", err)
	}

	if agent.Wallet == nil {
		t.Fatal("Wallet not set on Agent")
	}

	if agent.Wallet.LedgerId != ledger_id {
		t.Fatal("Wallet.LedgerId not set")
	}

	if agent.Wallet.Address != address {
		t.Fatal("Wallet.Address not set")
	}

	if agent.Wallet.PublicKey != public_key {
		t.Fatal("Wallet.PublicKey not set")
	}

	if agent.Wallet.PrivateKey != private_key {
		t.Fatal("Wallet.PrivateKey not set")
	}

	if !agent.connection.Initialised() {
		t.Fatal("connection not initialised")
	}

	err = agent.Start()

	if err != nil {
		t.Fatal("Failed to start agent", err)
	}

	out_envelope := &protocols.Envelope{
		To:         agent.Address(),
		Sender:     agent.Address(),
		ProtocolId: test_protocol_id,
		Message:    test_message,
	}

	err = agent.Put(out_envelope)

	if err != nil {
		t.Fatal("Failed to send envelope", err)
	}

	in_envelope := agent.Get()

	if in_envelope == nil {
		t.Fatal("Failed to get envelope")
	}

	if (in_envelope.Sender != out_envelope.Sender) || (in_envelope.To != out_envelope.To) {
		t.Fatal("Envelopes don't match")
	}

	agent.Stop()
}
