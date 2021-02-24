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
	connection connections.Connection
}

func (agent *Agent) InitFromEnv() error {
	if agent.connection == nil {
		log.Fatal("Must set connection on agent before calling InitFromEnv().")
	}
	agent.Wallet = &wallet.Wallet{}
	err := agent.Wallet.InitFromEnv()
	if err != nil {
		log.Fatal("Error initialising identity.")
	}
	err = agent.connection.InitFromEnv()
	if err != nil {
		log.Fatal("Error initialising connection.")
	}
	return nil
}

func (agent *Agent) Start() error {
	return agent.connection.Connect()
}

func (agent *Agent) Put(envelope *protocols.Envelope) error {
	return agent.connection.Put(envelope)
}

func (agent *Agent) Get() *protocols.Envelope {
	return agent.connection.Get()
}

func (agent *Agent) Stop() {
	err := agent.connection.Disconnect()
	if err != nil {
		log.Fatal(err)
	}
}
