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
	"log"
	"os"
	"strconv"

	"github.com/joho/godotenv"
)

type Agent struct {
	Identity          *AgentIdentity
	record            *AgentRecord
	p2p_client_config *P2PClientConfig
	p2p_client        *P2PClientApi
}

func (agent *Agent) InitFromEnv() error {
	env_file := os.Args[1]
	logger.Debug().Msgf("env_file: %s", env_file)
	err := godotenv.Overload(env_file)
	if err != nil {
		log.Fatal("Error loading env file")
	}
	ledger_id := os.Getenv("AEA_LEDGER_ID")
	address := os.Getenv("AEA_ADDRESS")
	public_key := os.Getenv("AEA_PUBLIC_KEY")
	agent_id := &AgentIdentity{LedgerId: ledger_id, Address: address, PublicKey: public_key}
	agent_id.PrivateKey = os.Getenv("AEA_PRIVATE_KEY")
	agent_record := &AgentRecord{Address: address, PublicKey: public_key}
	agent_record.ServiceId = os.Getenv("AEA_P2P_POR_SERVICE_ID")
	agent_record.LedgerId = os.Getenv("AEA_P2P_POR_LEDGER_ID")
	agent_record.PeerPublicKey = os.Getenv("AEA_P2P_POR_PEER_PUBKEY")
	agent_record.Signature = os.Getenv("AEA_P2P_POR_SIGNATURE")
	host := os.Getenv("AEA_P2P_DELEGATE_HOST")
	port := os.Getenv("AEA_P2P_DELEGATE_PORT")
	port_conv, err := strconv.ParseUint(port, 10, 16)
	if err != nil {
		panic(err)
	}
	client_config := &P2PClientConfig{host: host, port: uint16(port_conv)}
	agent.Identity = agent_id
	agent.record = agent_record
	agent.p2p_client_config = client_config
	p2p_client := &P2PClientApi{client_config: client_config, agent_record: agent_record}
	err = p2p_client.Init()
	if err != nil {
		logger.Error().Str("err", err.Error()).Msgf("agent init failed")
		return err
	}
	agent.p2p_client = p2p_client
	return nil
}

func (agent *Agent) Start() error {
	return agent.p2p_client.Connect()
}

func (agent *Agent) Put(envelope *Envelope) error {
	return agent.p2p_client.Put(envelope)
}

func (agent *Agent) Get() *Envelope {
	return agent.p2p_client.Get()
}

func (agent *Agent) Stop() {
	agent.p2p_client.Stop()
}
