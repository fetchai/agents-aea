/* -*- coding: utf-8 -*-
* ------------------------------------------------------------------------------
*
*   Copyright 2018-2021 Fetch.AI Limited
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
	aea "aealite"
	connections "aealite/connections"
	protocols "aealite/protocols"
	"log"
	"os"
	"os/signal"
	local_protocols "seller_agent/protocols"

	proto "google.golang.org/protobuf/proto"
)

func getRole(protocols.ProtocolMessageInterface, protocols.Address) protocols.Role {
	return protocols.Role("some")
}

func makeSellerDialogues(address string) *protocols.Dialogues {
	initialPerformatives := []protocols.Performative{"cfp"}
	terminalPerformatives := []protocols.Performative{"decline", "end"}
	validReplies := map[protocols.Performative][]protocols.Performative{
		"cfp": []protocols.Performative{"propose", "decline"},
		"propose": []protocols.Performative{
			"accept",
			"accept_w_inform",
			"decline",
			"propose",
		},
		"accept": []protocols.Performative{
			"decline",
			"match_accept",
			"match_accept_w_inform",
		},
		"accept_w_inform": []protocols.Performative{
			"decline",
			"match_accept",
			"match_accept_w_inform",
		},
		"decline":               []protocols.Performative{},
		"match_accept":          []protocols.Performative{"inform", "end"},
		"match_accept_w_inform": []protocols.Performative{"inform", "end"},
		"inform":                []protocols.Performative{"inform", "end"},
		"end":                   []protocols.Performative{},
	}
	dialogues := protocols.NewDialogues(
		protocols.Address(address),
		getRole,
		false,
		"my dialogues",
		initialPerformatives,
		terminalPerformatives,
		validReplies,
	)
	return dialogues
}

func handleEnvelope(
	envelope *protocols.Envelope,
	dialogues *protocols.Dialogues,
	agent *aea.Agent,
) {
	fipaProtocolID := "fetchai/fipa:1.0.0"

	if envelope.GetProtocolId() != fipaProtocolID {
		log.Printf("Not Fipa message!.")
		return
	}

	fipaMessage := &local_protocols.FipaMessage{}
	dialogueMessageWrapped, err := protocols.GetDialogueMessageWrappedAndSetContentFromEnvelope(
		envelope,
		fipaMessage,
	)
	if err != nil {
		log.Printf("Failed to get dialogue message message: %s", err)
		return
	}
	dialogue, err := dialogues.Update(dialogueMessageWrapped)
	if err != nil {
		log.Printf("Failed to update dialogue:  %s", err)
		return
	}
	switch dialogueMessageWrapped.Performative() {
	case "cfp":
		{
			msg, err := dialogue.Reply("propose", dialogueMessageWrapped, nil)
			if err != nil {
				log.Printf("Failed to reply dialogue:  %s", err)
				return
			}
			q := &protocols.Query_Instance{
				Model: &protocols.Query_DataModel{
					Name:        "string",
					Attributes:  []*protocols.Query_Attribute{},
					Description: "desc",
				},
				Values: []*protocols.Query_KeyValue{},
			}

			out, err := proto.Marshal(q)
			if err != nil {
				log.Printf("Failed to encode q:  %s", err)
				return
			}
			proposeMsg := &local_protocols.FipaMessage{
				Performative: &local_protocols.FipaMessage_Propose{
					Propose: &local_protocols.FipaMessage_Propose_Performative{
						Proposal: &local_protocols.FipaMessage_Description{DescriptionBytes: out},
					},
				},
			}

			content, err := proto.Marshal(proposeMsg)
			if err != nil {
				log.Printf("Failed to encode content:  %s", err)
				return
			}
			replyEnvelope, err := protocols.MakeResponseEnvelope(msg, fipaProtocolID, content)
			if err != nil {
				log.Printf("Failed to make envelope  %s", err)
				return
			}
			err = agent.Put(replyEnvelope)
			if err != nil {
				log.Printf("Error on send reply: %s", err)
				return
			}
		}
	case "accept":
		{
			msg, err := dialogue.Reply("match_accept", dialogueMessageWrapped, nil)
			if err != nil {
				log.Printf("Failed to reply dialogue:  %s", err)
				return
			}
			matchMsg := &local_protocols.FipaMessage{
				Performative: &local_protocols.FipaMessage_MatchAccept{},
			}

			content, err := proto.Marshal(matchMsg)
			if err != nil {
				log.Printf("Failed to encode content:  %s", err)
				return
			}
			replyEnvelope, err := protocols.MakeResponseEnvelope(msg, fipaProtocolID, content)
			if err != nil {
				log.Printf("Failed to make envelope  %s", err)
				return
			}
			err = agent.Put(replyEnvelope)
			if err != nil {
				log.Printf("Error on send reply: %s", err)
				return
			}
		}
	case "end":
		{
			log.Print("It's done")
			log.Print("FIPA INTERACTION COMPLETE")
		}
	default:
		{
			log.Printf("Unsupported performative:  %s", dialogueMessageWrapped.Performative())
			return
		}

	}

	log.Print("envelope handled successfully")
}

func getEnvelopeAndProcess(
	dialogues *protocols.Dialogues,
	agent *aea.Agent) {
	for {
		envelope := agent.Get()
		log.Printf("got incoming envelope: %s", envelope.String())
		handleEnvelope(envelope, dialogues, agent)
	}
}

func main() {

	var err error

	// env file
	if len(os.Args) != 2 {
		log.Print("Usage: main ENV_FILE")
		os.Exit(1)
	}
	envFile := os.Args[1]

	log.Print("Agent starting ...")

	// Create agent
	agent := aea.Agent{}

	// Set connection
	agent.Connection = &connections.P2PClientApi{}

	// Initialise agent from environment file (first arg to process)
	err = agent.InitFromEnv(envFile)
	if err != nil {
		log.Fatal("Failed to initialise agent", err)
	}
	log.Print("successfully initialized AEA!")

	err = agent.Start()
	if err != nil {
		log.Fatal("Failed to start agent", err)
	}
	log.Print("successfully started AEA!")
	log.Print("My Address is ", agent.Address())

	dialogues := makeSellerDialogues(agent.Address())

	go getEnvelopeAndProcess(dialogues, &agent)

	// Wait until Ctrl+C or a termination call is done.
	c := make(chan os.Signal, 1)
	signal.Notify(c, os.Interrupt)
	<-c

	err = agent.Stop()
	if err != nil {
		log.Fatal("Failed to stop agent", err)
	}
	log.Print("Agent stopped")
}
