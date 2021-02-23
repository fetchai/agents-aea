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

package connections

import (
	"os"
	"testing"
)

const (
	EnvTestFile = "../test_env_file.env"
)

var (
	address             = "fetch1x9v67meyfq4pkgy2n2yf6797cfkul327kpclqr"
	public_key          = "02ac514ba70de60ed5c30f90e3acdfc958ecb416d9676706bf013228abfb2c2816"
	por_service_id      = "acn"
	por_ledger_id       = "fetchai"
	por_peer_public_key = "0217a59bd805c310aca4febe0e99ce22ee3712ae085dc1e5630430b1e15a584bb7"
	por_signature       = "61767a48664c2f666a4d69647677654a4a4b6a74425569714a322b3661445571384d6f4e524269396e44492f6c576c65495833667452663653783555576d78635330535730334956726631694b545841357a654130673d3d"
	delegate_host       = "acn.fetch.ai"
	delegate_port       = uint16(11000)
)

// TestP2PClientApiInit
func TestP2PClientApiInit(t *testing.T) {
	os.Args = []string{"cmd", EnvTestFile}

	client := &P2PClientApi{}

	// initialise
	err := client.InitFromEnv()

	if err != nil {
		t.Fatal("Failed to initialise client", err)
	}

	if client.client_config == nil {
		t.Fatal("client_config not set", err)
	}

	if client.client_config.host != delegate_host {
		t.Fatal("client_config.host not set", err)
	}

	if client.client_config.port != delegate_port {
		t.Fatal("client_config.port not set", err)
	}

	if client.agent_record == nil {
		t.Fatal("client.agent_record not set")
	}

	if client.agent_record.ServiceId != por_service_id {
		t.Fatal("agent_record.ServiceId not set")
	}

	if client.agent_record.LedgerId != por_ledger_id {
		t.Fatal("agent_record.LedgerId not set")
	}

	if client.agent_record.Address != address {
		t.Fatal("agent_record.Address not set")
	}

	if client.agent_record.PublicKey != public_key {
		t.Fatal("agent_record.PublicKey not set")
	}

	if client.agent_record.PeerPublicKey != por_peer_public_key {
		t.Fatal("agent_record.PublicKey not set")
	}

	if client.agent_record.Signature != por_signature {
		t.Fatal("agent_record.Signature not set")
	}

	if client.socket == nil {
		t.Fatal("client.socket not set")
	}

	if !client.initialised {
		t.Fatal("client not initialised")
	}

	if client.connected {
		t.Fatal("client connected")
	}
}
