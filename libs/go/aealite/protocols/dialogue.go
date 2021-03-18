package protocols

import (
	"fmt"
	"crypto/rand"
	"encoding/hex"
)

type Address string
type Performative string
type SomeMessageType string

const(
	NONCE_BYTES_NB = 32
)

// type Dialogue struct {
// 	_dialogues_storage
// 	_dialogues_stats
// 	_keep_terminal_state_dialogues
// 	_message_class
// 	_dialogue_class
// 	_role_from_first_message
// 	_self_address
// 	_outgoing_messages
// 	_incoming_messages
// }

type Dialogue stuct {
	counterParty Address
	performative Performative
	startingMessageId int
	to Address
	sender Address
	dialogueReference [2]string
	incomplete_to_complete_dialogue_labels []string
	message SomeMessageType
}

func create(counterParty Address, performative Performative, message SomeMessageType) *Dialogue {

	dialogue := &{
		message : message,
		counterParty : counterParty,
		startingMessageId : 1,
		target : 0,
		performative : performative
		to : counterParty,
	}

	//TODO

	// figure out what is _message_class ? know more about this.

	// figure out what is performative? how will it be used?

	// create initial message using :
	// 1. dialog reference
	// 2. message_id
	// 3. target
	// 4. permormative
	// 5. message


	// TODO
	// get initiaor address
	// selfAddress := getInititatorAddress()

	// set initial message sender and counterparty address
	dialogue.sender = selfAddress
	dialogue.dialogueReference[0] := generateDialogueNonce()
	dialogue.dialogueReference[1] := ""

	

	// process dialogue creation 
	dialogue.createDialogue();
	
	
	return dialogue

}

func (dialogue *Dialogue) createDialogue() {

	// TODO
	// define dialog ROLE for dialog inititor
	
	// define 2 lables, incomplete and complete
	// lable will be set with reference to complete if it exist else incomplete

	if dialogueReference[0] == "" || dialogueReference[1] != "" {
		// throw error for responder reference already existing
	}

	if dialog.incomplete_to_complete_dialogue_labels.length() > 0 {
		// throw error for incomplete label already present
	}

	// check dialog lable not be present

	// add missing relevant fields for dialogue
	
	// add dialogue to storage
	// maybe create a map of dialoges in dialogue struct
	
}

func generateDialogueNonce() string {
	hexValue, _ := randomHex(NONCE_BYTES_NB)
	retuen hexValue
}

func randomHex(n int) (string) {
  bytes := make([]byte, n)
  if _, err := rand.Read(bytes); err != nil {
    return "", err
  }
  return hex.EncodeToString(bytes), nil
}
