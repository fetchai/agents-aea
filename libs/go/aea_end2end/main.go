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
	proto "google.golang.org/protobuf/proto"
	"log"
	"os"
	"os/signal"
	local_protocols "seller_agent/protocols"
)

func getRole(protocols.ProtocolMessageInterface, protocols.Address) protocols.Role {
	return protocols.Role("some")
}

func makeSellerDialogues(address string) *protocols.Dialogues {
	initialPerformatives := []protocols.Performative{"cfp"}
	terminalPerformatives := []protocols.Performative{"decline", "end"}
	validReplies := map[protocols.Performative][]protocols.Performative{
		"cfp":                   []protocols.Performative{"propose", "decline"},
		"propose":               []protocols.Performative{"accept", "accept_w_inform", "decline", "propose"},
		"accept":                []protocols.Performative{"decline", "match_accept", "match_accept_w_inform"},
		"accept_w_inform":       []protocols.Performative{"decline", "match_accept", "match_accept_w_inform"},
		"decline":               []protocols.Performative{},
		"match_accept":          []protocols.Performative{"inform", "end"},
		"match_accept_w_inform": []protocols.Performative{"inform", "end"},
		"inform":                []protocols.Performative{"inform", "end"},
		"end":                   []protocols.Performative{},
	}
	dialogues := protocols.NewDialogues(protocols.Address(address), getRole, false, "my dialogues", initialPerformatives, terminalPerformatives, validReplies)
	return dialogues
}

func makeResponseEnvelope(wrapped_msg_dialogue protocols.ProtocolMessageInterface, protocol_id string, content []byte) (protocols.Envelope, error) {
	dialogueRef := wrapped_msg_dialogue.DialogueReference()

	message := protocols.Message{
		Message: &protocols.Message_DialogueMessage{
			DialogueMessage: &protocols.DialogueMessage{
				MessageId:                  int32(wrapped_msg_dialogue.MessageId()),
				DialogueStarterReference:   dialogueRef.DialogueStarterReference(),
				DialogueResponderReference: dialogueRef.DialogueResponderReference(),
				Target:                     int32(wrapped_msg_dialogue.Target()),
				Content:                    content,
			},
		},
	}

	out, err := proto.Marshal(&message)
	if err != nil {
		log.Print("marshal dialogue messge failed")
		return protocols.Envelope{}, err
	}
	env := protocols.Envelope{
		To:         string(wrapped_msg_dialogue.To()),
		Sender:     string(wrapped_msg_dialogue.Sender()),
		ProtocolId: protocol_id,
		Message:    out,
		Uri:        "",
	}
	return env, nil

}

func handleEnvelope(envelope *protocols.Envelope, dialogues *protocols.Dialogues, agent *aea.Agent) {
	fipa_protocol_id := "fetchai/fipa:1.0.0"

	if envelope.GetProtocolId() != fipa_protocol_id {
		log.Printf("Not Fipa message!.")
		return
	}

	fipa_message := &local_protocols.FipaMessage{}
	dialogue_message_wrapped, err := protocols.GetDialogueMessageWrappedAndSetContentFromEnvelope(envelope, fipa_message)
	if err != nil {
		log.Printf("Failed to get dialogue message message: %s", err)
		return
	}
	log.Printf("Fipa message:  %s", fipa_message)
	log.Printf("dialogue message sender:  %s", dialogue_message_wrapped.Sender())
	log.Printf("dialogue message to:  %s", dialogue_message_wrapped.To())
	log.Printf("dialogue message wrapped:  %s", dialogue_message_wrapped)

	dialogue, err := dialogues.Update(dialogue_message_wrapped)
	if err != nil {
		log.Printf("Failed to update dialogue:  %s", err)
		return
	}

	msg, err := dialogue.Reply("propose", dialogue_message_wrapped, nil)
	if err != nil {
		log.Printf("Failed to reply dialogue:  %s", err)
		return
	}
	log.Printf("msg: %s", msg)

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
	propose_msg := &local_protocols.FipaMessage{
		Performative: &local_protocols.FipaMessage_Propose{
			Propose: &local_protocols.FipaMessage_Propose_Performative{
				Proposal: &local_protocols.FipaMessage_Description{DescriptionBytes: out},
			},
		},
	}

	log.Printf("propose_msg %s", propose_msg)
	content, err := proto.Marshal(propose_msg)
	log.Printf("content %s", content, len(content))
	if err != nil {
		log.Printf("Failed to encode content:  %s", err)
		return
	}
	reply_envelope, err := makeResponseEnvelope(msg, fipa_protocol_id, content)
	if err != nil {
		log.Printf("Failed to make envelope  %s", err)
		return
	}
	agent.Put(&reply_envelope)

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
	log.Print("My Address is", agent.Address())

	dialogues := makeSellerDialogues(agent.Address())
	envelope := agent.Get()

	handleEnvelope(envelope, dialogues, &agent)

	log.Printf("got incoming envelope: %s", envelope.String())

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
