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
	"log"

	connections "aealite/connections"
	protocols "aealite/protocols"
	wallet "aealite/wallet"
)

const (
	DefaultLedger = "fetchai"
)

type Agent struct {
	Wallet     *wallet.Wallet
	Connection connections.Connection
}

func (agent *Agent) InitFromEnv(envFile string) error {
	if agent.Connection == nil {
		log.Fatal("Must set connection on agent before calling InitFromEnv().")
	}
	agent.Wallet = &wallet.Wallet{}
	err := agent.Wallet.InitFromEnv(envFile)
	if err != nil {
		log.Fatal("Error initialising identity.")
	}
	err = agent.Connection.InitFromEnv(envFile)
	if err != nil {
		log.Fatal("Error initialising connection.")
	}
	return nil
}

func (agent *Agent) Address() string {
	return agent.Wallet.Address
}

func (agent *Agent) Start() error {
	return agent.Connection.Connect()
}

func (agent *Agent) Put(envelope *protocols.Envelope) error {
	return agent.Connection.Put(envelope)
}

func (agent *Agent) Get() *protocols.Envelope {
	return agent.Connection.Get()
}

func (agent *Agent) Stop() error {
	err := agent.Connection.Disconnect()
	if err != nil {
		log.Fatal(err)
	}
	return err
}
