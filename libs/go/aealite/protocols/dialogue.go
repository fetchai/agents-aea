package protocols

import (
	"fmt"
	"crypto/rand"
	"encoding/hex"
)

type Address string
type Performative []string
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
// Define RoleType and figure out how to find role

type Label struct {
	dialogueReference [2]string
	dialogueOpponentAddress Address
	dialogueStarterAddress Address
}

type Dialogue struct {
	dialogueLabel Label
	dialogueMessage *InitialMessage
	selfAddress Address
	// role RoleType
}

var dialogueStorage map[Address][]Label

type InitialMessage struct {
	dialogueReference [2]string
	message_id int
	target int
	performative []string
	message SomeMessageType
	to Address
	sender Address
}

func create(selfAddress Address, counterParty Address, performative Performative, message SomeMessageType) *Dialogue {

	dialogueStorage = make(map[Address][]Label)

	intitialMessage := &InitialMessage{
		message_id : 0,
		target : 1,
		performative : performative,
		message : message,
		to : counterParty,
		sender : selfAddress,
	}
	intitialMessage.dialogueReference[0] = generateDialogueNonce()
	intitialMessage.dialogueReference[1] = ""
	
	// process dialogue creation 
	dialogue := intitialMessage.createDialogue();

	return dialogue
}

func (data *InitialMessage) createDialogue() *Dialogue{

	// TODO
	// define dialog ROLE for dialog initiator
	
	incompleteDialogueLabel := data.checkAndProcessLabels()
	pair := data.sender+data.to
	if len(dialogueStorage[pair]) > 0 {
		for _,dialogue := range dialogueStorage[pair] {
			if incompleteDialogueLabel == dialogue {
				fmt.Println("Error : incomplete dialogue label already present in storage")
				return nil
			}
		}
	}
	dialogueLabel := incompleteDialogueLabel
	
	// TODO
	// initialize completeLabel
	// if completeLabel != nil {
	// 	dialogueLabel = completeDialogueLabel
	// }

	if len(dialogueStorage[data.sender+data.to]) > 0 {
		for _,dialogue := range dialogueStorage[data.sender+data.to] {
			if dialogueLabel == dialogue {
				fmt.Println("Error : Dialogue label already present in storage")
				return nil
			}
		}
	}

	dialogue := &Dialogue{
		dialogueLabel : dialogueLabel,
		dialogueMessage : data,
		selfAddress : data.sender,
	}

	return dialogue
	
}

func (data *InitialMessage)checkAndProcessLabels() Label {
	if ! (data.dialogueReference[0] != "" && data.dialogueReference[1] == "") {
		fmt.Println("Error : Reference address label already exists")
	}
	return Label{
		dialogueReference : data.dialogueReference,
		dialogueOpponentAddress : data.to,
		dialogueStarterAddress : data.sender,
	}
}

func generateDialogueNonce() string {
	hexValue := randomHex(NONCE_BYTES_NB)
	return hexValue
}

func randomHex(n int) (string) {
  bytes := make([]byte, n)
  if _, err := rand.Read(bytes); err != nil {
    return ""
  }
  return hex.EncodeToString(bytes)
}