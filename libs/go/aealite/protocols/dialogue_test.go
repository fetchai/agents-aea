package protocols

import (
	"fmt"
	"log"
	"testing"
)

const (
	senderAddress       = "ba6b08b13043e83a962a3a5eeaad3b6c"
	counterPartyAddress = "1ba5cb6f46f426a27ec53064032419f1"
)

func TestDialogue(t *testing.T) {
	performative := Performative{}
	// createing initital dialogue instance
	message, dialogue := Create(counterPartyAddress, senderAddress, performative, []byte("initial message"))
	// cheking if message returned has a sender same as senderAddress
	if address, err := message.hasSender(); err != nil {
		log.Fatal(err)
	} else {
		if address != senderAddress {
			log.Fatal("Error: Sender address invalid.", address, " ", senderAddress)
		}
	}
	// cheking if message returned has a counter party same as counterPartyAddress
	if address, err := message.hasCounterparty(); err != nil {
		log.Fatal(err)
	} else {
		if address != counterPartyAddress {
			log.Fatal("Error: CounterParty address invalid.")
		}
	}
	// checking if length of outgoing messages list is 1
	if len(dialogue.outgoingMessages) != 1 {
		log.Fatal("dialogue outgoing messages length is ", len(dialogue.outgoingMessages), " should be 1")
	}
	// checking if length of incoming messages list is 0
	if len(dialogue.incomingMessages) != 0 {
		log.Fatal("dialogue incoming messages length is ", len(dialogue.incomingMessages), " should be 0")
	}
	fmt.Println(dialogue.lastMessageId, dialogue.orderedMessageIds, len(dialogue.incomingMessages), len(dialogue.outgoingMessages))
	nextMessageId := dialogue.getNextMessageId()
	// inititlaizing a new message and updating dialogue using it
	newMessage := InitializeMessage(counterPartyAddress, senderAddress, performative, []byte("second message"), dialogue.dialogueLabel.dialogueReference, nextMessageId)
	dialogue.update(newMessage)
	// fmt.Println(dialogue.lastMessageId, dialogue.orderedMessageIds, len(dialogue.incomingMessages), len(dialogue.outgoingMessages))
}
