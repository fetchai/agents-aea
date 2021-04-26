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
	"log"
	"os"
	"os/signal"
	aea "aealite"
	connections "aealite/connections"
	protocols "aealite/protocols"
)


func getRole(protocols.ProtocolMessageInterface, protocols.Address) protocols.Role {
	return protocols.Role("some")
}


func makeSellerDialogues(address string) *protocols.Dialogues {
	initialPerformatives := []protocols.Performative{"cfp"}
	terminalPerformatives := []protocols.Performative{"decline", "end"}
	validReplies := map[protocols.Performative][]protocols.Performative{
		  "cfp": []protocols.Performative{"propose", "decline"},
		  "propose": []protocols.Performative{"accept", "accept_w_inform", "decline", "propose"},
		  "accept": []protocols.Performative{"decline", "match_accept", "match_accept_w_inform"},
		  "accept_w_inform": []protocols.Performative{"decline", "match_accept", "match_accept_w_inform"},
		  "decline": []protocols.Performative{},
		  "match_accept": []protocols.Performative{"inform", "end"},
		  "match_accept_w_inform": []protocols.Performative{"inform", "end"},
		  "inform": []protocols.Performative{"inform", "end"},
		  "end": []protocols.Performative{},
	}
	dialogues := protocols.NewDialogues(protocols.Address(address), getRole, false, "my dialogues", initialPerformatives, terminalPerformatives, validReplies)
	return dialogues
}




func handleEnvelope(envelope *protocols.Envelope, dialogues *protocols.Dialogues){
	fipa_protocol_id := "fetchai/fipa:1.0.0"
	
	if envelope.GetProtocolId() != fipa_protocol_id {
		log.Printf("Not Fipa message!.")
		return
	}
	
	
	fipa_message := &FipaMessage{}
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
	log.Printf("Dialogue: %s", dialogue)
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
	
	handleEnvelope(envelope, dialogues)
		
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
