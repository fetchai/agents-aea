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

package identity

import (
	"os"
	"testing"
)

const (
	EnvTestFile = "../test_env_file.env"
)

var (
	ledger_id   = "fetchai"
	address     = "fetch1x9v67meyfq4pkgy2n2yf6797cfkul327kpclqr"
	public_key  = "02ac514ba70de60ed5c30f90e3acdfc958ecb416d9676706bf013228abfb2c2816"
	private_key = "6d8d2b87d987641e2ca3f1991c1cccf08a118759e81fabdbf7e8484f27af015e"
)

// TestIdentity
func TestIdentity(t *testing.T) {
	os.Args = []string{"cmd", EnvTestFile}

	identity := AgentIdentity{}

	// initialise
	err := identity.InitFromEnv()

	if err != nil {
		t.Fatal("Failed to initialise identity", err)
	}

	if identity.LedgerId != ledger_id {
		t.Fatal("AgentIdentity.LedgerId not set")
	}

	if identity.Address != address {
		t.Fatal("AgentIdentity.Address not set")
	}

	if identity.PublicKey != public_key {
		t.Fatal("AgentIdentity.PublicKey not set")
	}

	if identity.PrivateKey != private_key {
		t.Fatal("AgentIdentity.PrivateKey not set")
	}
}
