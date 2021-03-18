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

// TODO
// Define LableType
// Define RoleType and figure out how to find role

type Dialogue stuct {
	dialogueLabel LableType
	dialogueMessage *InitialMessage
	selfAddress Address
	// role RoleType
}

dialogueStorage := make(map[string][]Dialogue)

type InitialMessage struct {
	dialogueReference [2]string
	message_id string
	target int
	performative string
	message SomeMessageType
	to Address
	sender Address
}

func create(selfAddress Address, counterParty Address, performative Performative, message SomeMessageType) *Dialogue {

	intitialMessage := &InitialMessage{
		dialogueReference : ,
		message_id : ,
		target : ,
		performative : performative,
		message : message,
		to : counterParty,
		sender : selfAddress
	}
	initialMessage.dialogueReference[0] := generateDialogueNonce()
	initialMessage.dialogueReference[1] := ""
	
	// process dialogue creation 
	dialogue := initialMessage.createDialogue();

	return dialogue
}

func (data *InitialMessage) createDialogue() *Dialogue{

	// TODO
	// define dialog ROLE for dialog initiator
	
	incompleteDialogueLabel := data.checkAndProcessLabels()
	if dialogueStorage[data.sender+data.to].length() > 0 {
		for dialogue := range dialogueStorage[data.sender+data.to] {
			if incompleteDialogueLabel == dialogue {
				fmt.Println("Error : incomplete dialogue label already present in storage")
				return
			}
		}
	}
	dialogueLabel := incompleteDialogueLabel
	
	// TODO
	// initialize completeLabel
	// if completeLabel != nil {
	// 	dialogueLabel = completeDialogueLabel
	// }

	if dialogueStorage[data.sender+data.to].length() > 0 {
		for dialogue := range dialogueStorage[data.sender+data.to] {
			if dialogueLabel == dialogue {
				fmt.Println("Error : Dialogue label already present in storage")
				return
			}
		}
	}

	dialogue := &Dialogue{
		dialogueLabel : dialogueLabel,
		message : data,
		selfAddress : data.sender
	}

	return dialogue
	
}

func (data *InitialMessage)checkAndProcessLabels() {
	if ! (data.dialogueReference[0] != "" && data.dialogueReference[1] == "") {
		fmt.Println("Error : Reference address label already exists")
		return
	}
	return {
		dialogueReference := data.dialogueReference,
		dialogueOpponentAddress := data.to,
		dialogueStarterAddress := data.sender
	}
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
