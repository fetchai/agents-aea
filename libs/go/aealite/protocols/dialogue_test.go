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

package protocols

import (
	"reflect"
	"testing"
)

func TestDialogue(t *testing.T) {
	label := getTestDialogueLabel()
	initialPerformatives := []Performative{"start"}
	terminalPerformatives := []Performative{"end"}
	validReplies := map[Performative][]Performative{"start": {"end"}}
	rules := NewRules(initialPerformatives, terminalPerformatives, validReplies)
	dialogue := NewDialogue(
		label,
		senderAddress,
		Role1,
		initialPerformatives,
		terminalPerformatives,
		validReplies,
	)
	// test getters
	if dialogue.DialogueLabel() != label {
		t.Fatalf("unexpected return value of DialogueLabel()")
	}
	if dialogue.IncompleteDialogueLabel() != label.IncompleteVersion() {
		t.Fatalf("unexpected return value of IncompleteDialogueLabel()")
	}
	if dialogue.DialogueLabels() != [2]DialogueLabel{label, label.IncompleteVersion()} {
		t.Fatalf("unexpected return value of DialogueLabels()")
	}
	if dialogue.SelfAddress() != senderAddress {
		t.Fatalf("unexpected return value of SelfAddress()")
	}
	if dialogue.Role() != Role1 {
		t.Fatalf("unexpected return value of Role()")
	}
	if !reflect.DeepEqual(dialogue.Rules(), rules) {
		t.Fatalf("unexpected return value of Rules()")
	}
	if dialogue.LastIncomingMessage() != nil {
		t.Fatalf("unexpected return value of LastIncomingMessage(): the dialogue should be empty")
	}
	if dialogue.LastOutgoingMessage() != nil {
		t.Fatalf("unexpected return value of LastOutgoingMessage(): the dialogue should be empty")
	}
	if dialogue.LastMessage() != nil {
		t.Fatalf("unexpected return value of LastMessage(): the dialogue should be empty")
	}

}

////func TestDialogue(t *testing.T) {
//	var performative Performative = "sample_performative"
//	// createing initital dialogue instance
//	message, dialogue := Create(
//		counterPartyAddress,
//		senderAddress,
//		performative,
//		[]byte("initial message"),
//	)
//	// cheking if message returned has a sender same as senderAddress
//	if address, err := message.HasSender(); err != nil {
//		log.Fatal(err)
//	} else {
//		if address != senderAddress {
//			log.Fatal("Error: Sender address invalid.", address, " ", senderAddress)
//		}
//	}
//	// cheking if message returned has a counter party same as counterPartyAddress
//	if address, err := message.HasCounterparty(); err != nil {
//		log.Fatal(err)
//	} else {
//		if address != counterPartyAddress {
//			log.Fatal("Error: CounterParty address invalid.")
//		}
//	}
//	// checking if length of outgoing messages list is 1
//	if len(dialogue.outgoingMessages) != 1 {
//		log.Fatal(
//			"dialogue outgoing messages length is ",
//			len(dialogue.outgoingMessages),
//			" should be 1",
//		)
//	}
//	// checking if length of incoming messages list is 0
//	if len(dialogue.incomingMessages) != 0 {
//		log.Fatal(
//			"dialogue incoming messages length is ",
//			len(dialogue.incomingMessages),
//			" should be 0",
//		)
//	}
//	if dialogue.IsEmpty() == true {
//		log.Fatal("dialogue should not be empty")
//	}
//	// fetch message id for next mesaage in the dialogue
//	var nextMessageId MessageId
//	if dialogue.selfAddress == senderAddress {
//		nextMessageId = dialogue.getOutgoingNextMessageId()
//	} else {
//		nextMessageId = dialogue.getIncomingNextMessageId()
//	}
//	// inititlaizing a new message and updating dialogue using it
//	newMessage := InitializeMessage(
//		counterPartyAddress,
//		senderAddress,
//		performative,
//		[]byte("second message"),
//		dialogue.dialogueLabel.DialogueReference(),
//		nextMessageId,
//		dialogue.lastMessageId,
//	)
//	dialogue.update(newMessage)
//	// checking if length of outgoing messages list is 2
//	if len(dialogue.outgoingMessages) != 2 {
//		log.Fatal(
//			"dialogue outgoing messages length is ",
//			len(dialogue.outgoingMessages),
//			" should be 2",
//		)
//	}
//	// checking if length of incoming messages list is 0
//	if len(dialogue.incomingMessages) != 0 {
//		log.Fatal(
//			"dialogue incoming messages length is ",
//			len(dialogue.incomingMessages),
//			" should be 0",
//		)
//	}
//}
