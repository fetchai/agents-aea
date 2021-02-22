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

package aea

import (
	"os"
	"testing"
)

const (
	EnvTestFile = "test_env_file.env"
)

var (
	ledger_id           = "fetchai"
	address             = "fetch1x9v67meyfq4pkgy2n2yf6797cfkul327kpclqr"
	public_key          = "02ac514ba70de60ed5c30f90e3acdfc958ecb416d9676706bf013228abfb2c2816"
	private_key         = "6d8d2b87d987641e2ca3f1991c1cccf08a118759e81fabdbf7e8484f27af015e"
	por_service_id      = "acn"
	por_ledger_id       = "fetchai"
	por_peer_public_key = "0217a59bd805c310aca4febe0e99ce22ee3712ae085dc1e5630430b1e15a584bb7"
	por_signature       = "61767a48664c2f666a4d69647677654a4a4b6a74425569714a322b3661445571384d6f4e524269396e44492f6c576c65495833667452663653783555576d78635330535730334956726631694b545841357a654130673d3d"
	delegate_host       = "acn.fetch.ai"
	delegate_port       = uint16(11000)
)

// TestAgent apis
func TestAgent(t *testing.T) {
	os.Args = []string{"cmd", EnvTestFile}

	agent := Agent{}
	err := agent.InitFromEnv()

	if err != nil {
		t.Fatal("Failed to initialise agent", err)
	}

	if agent.Identity == nil {
		t.Fatal("AgentIdentity not set on Agent")
	}

	if agent.Identity.LedgerId != ledger_id {
		t.Fatal("AgentIdentity.LedgerId not set")
	}

	if agent.Identity.Address != address {
		t.Fatal("AgentIdentity.Address not set")
	}

	if agent.Identity.PublicKey != public_key {
		t.Fatal("AgentIdentity.PublicKey not set")
	}

	if agent.Identity.PrivateKey != private_key {
		t.Fatal("AgentIdentity.PrivateKey not set")
	}

	if agent.record == nil {
		t.Fatal("record not set on Agent")
	}

	if agent.record.ServiceId != por_service_id {
		t.Fatal("record.ServiceId not set")
	}

	if agent.record.LedgerId != por_ledger_id {
		t.Fatal("record.LedgerId not set")
	}

	if agent.record.Address != address {
		t.Fatal("record.Address not set")
	}

	if agent.record.PublicKey != public_key {
		t.Fatal("record.PublicKey not set")
	}

	if agent.record.PeerPublicKey != por_peer_public_key {
		t.Fatal("record.PublicKey not set")
	}

	if agent.record.Signature != por_signature {
		t.Fatal("record.Signature not set")
	}

	if agent.p2p_client_config == nil {
		t.Fatal("p2p_client_config not set on Agent")
	}

	if agent.p2p_client_config.host != delegate_host {
		t.Fatal("p2p_client_config.host not set")
	}

	if agent.p2p_client_config.port != delegate_port {
		t.Fatal("p2p_client_config.port not set")
	}

	if agent.p2p_client == nil {
		t.Fatal("p2p_client not set on Agent")
	}

	if agent.p2p_client.socket == nil {
		t.Fatal("p2p_client.socket not set")
	}

	err = agent.Start()

	if err != nil {
		t.Fatal("Failed to start agent", err)
	}

	agent.Stop()
}
