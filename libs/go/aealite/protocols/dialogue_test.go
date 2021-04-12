package protocols

import (
	"encoding/json"
	"log"
	"testing"
)

const (
	senderAddress       = "ba6b08b13043e83a962a3a5eeaad3b6c"
	counterPartyAddress = "1ba5cb6f46f426a27ec53064032419f1"
	starterReference    = "starterReference"
	responderReference  = "responderReference"
)

// get a default dialogue label for testing purposes
func getTestDialogueLabel() DialogueLabel {
	return DialogueLabel{
		[2]string{starterReference, responderReference},
		counterPartyAddress,
		senderAddress,
	}
}

// Test DialogueLabel initialization and getters
func TestDialogueLabelGetters(t *testing.T) {
	starterReference := "starterReference"
	responderReference := "responderReference"
	label := DialogueLabel{
		[2]string{starterReference, responderReference},
		counterPartyAddress,
		senderAddress,
	}

	if actual := label.getDialogueStarterReference(); actual != starterReference {
		t.Fatalf("Expected %s, got: %s", starterReference, actual)
	}
	if actual := label.getDialogueResponderReference(); actual != responderReference {
		t.Fatalf("Expected %s, got: %s", responderReference, actual)
	}

}

// Test getIncompleteVersion function
func TestGetIncompleteVersion(t *testing.T) {
	label := getTestDialogueLabel()
	actualIncompleteVersion := label.getIncompleteVersion()
	expectedIncompleteVersion := DialogueLabel{
		[2]string{label.getDialogueStarterReference(), UnassignedDialogueReference},
		label.DialogueOpponentAddress,
		label.DialogueStarterAddress,
	}
	if actualIncompleteVersion != expectedIncompleteVersion {
		t.Errorf("getIncompleteVersion gave unexpected result.")
	}
}

// Test marshalling and unmarshalling
func TestMarshalAndUnmarshal(t *testing.T) {
	label := getTestDialogueLabel()

	data, err := json.Marshal(label)
	if err != nil {
		t.Fatalf("DialogueLabel JSON marshalling failed with error: %s", err.Error())
	}

	result := DialogueLabel{}
	err = json.Unmarshal(data, &result)
	if err != nil {
		t.Fatalf("DialogueLabel JSON unmarshalling failed with error: %s", err.Error())
	}
	if result != label {
		t.Fatal("the DialogueLabel parsed from JSON is not the same of the original one.")
	}
}

// Test ToString and FromString methods.
func TestToStringAndFromString(t *testing.T) {
	label := getTestDialogueLabel()
	result := DialogueLabel{}
	err := result.FromString(label.String())
	if err != nil {
		t.Fatalf("Cannot parse string: %s", err.Error())
	}
	if label != result {
		t.Fatal("the DialogueLabel parsed from string is not the same of the original one.")
	}
}

func TestDialogue(t *testing.T) {
	var performative Performative = "sample_performative"
	// createing initital dialogue instance
	message, dialogue := Create(
		counterPartyAddress,
		senderAddress,
		performative,
		[]byte("initial message"),
	)
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
		log.Fatal(
			"dialogue outgoing messages length is ",
			len(dialogue.outgoingMessages),
			" should be 1",
		)
	}
	// checking if length of incoming messages list is 0
	if len(dialogue.incomingMessages) != 0 {
		log.Fatal(
			"dialogue incoming messages length is ",
			len(dialogue.incomingMessages),
			" should be 0",
		)
	}
	if dialogue.isEmpty() == true {
		log.Fatal("dialogue should not be empty")
	}
	// fetch message id for next mesaage in the dialogue
	var nextMessageId MessageId
	if dialogue.selfAddress == senderAddress {
		nextMessageId = dialogue.getOutgoingNextMessageId()
	} else {
		nextMessageId = dialogue.getIncomingNextMessageId()
	}
	// inititlaizing a new message and updating dialogue using it
	newMessage := InitializeMessage(
		counterPartyAddress,
		senderAddress,
		performative,
		[]byte("second message"),
		dialogue.dialogueLabel.DialogueReference,
		nextMessageId,
		dialogue.lastMessageId,
	)
	dialogue.update(newMessage)
	// checking if length of outgoing messages list is 2
	if len(dialogue.outgoingMessages) != 2 {
		log.Fatal(
			"dialogue outgoing messages length is ",
			len(dialogue.outgoingMessages),
			" should be 2",
		)
	}
	// checking if length of incoming messages list is 0
	if len(dialogue.incomingMessages) != 0 {
		log.Fatal(
			"dialogue incoming messages length is ",
			len(dialogue.incomingMessages),
			" should be 0",
		)
	}
}
