package protocols

import (
	"crypto/rand"
	"encoding/hex"
	"fmt"
)

type Address string
type Performative []string
type SomeMessageType string

const (
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
// Define RoleType, RuleType and figure out how to find role
type RoleType Address
type RuleType Address

type MessageId int
type targetMessage InitialMessage
type target []int
type DialogueInterface interface {
	initialize(dialogueLabel Label, message InitialMessage, selfAddress Address, role RoleType)
	equal(Dialogue) bool // compare two dialogues
	getDialogueLabel() Label
	getIncompleteDIalgueLabel() Label
	getDialogueLabels() []Label // returns both dialogue and incomplete dialog labels Label
	getSelfAddress() Address
	getRole() RoleType
	getRules() RuleType
	getMessageCLass() InitialMessage
	isSelfInitiated() bool
	getLastIncomingMessage() InitialMessage
	getLastOutgoingMessage() InitialMessage
	getLastMessage() InitialMessage
	isEmpty() bool
	counterPartyForMessage(InitialMessage) bool
	isMessageBySelf(InitialMessage) bool
	isMessageByOther(InitialMessage) bool
	getMessage(MessageId) InitialMessage
	hasMessageId(MessageId) bool
	update(InitialMessage)
	isBelongingToADialogue(InitialMessage) bool
	reply(Performative, targetMessage, target) InitialMessage
	validateNextMessage(InitialMessage) (bool, InitialMessage)
	basicValidations(InitialMessage) (bool, InitialMessage)
	basicValidationInitialMessage(InitialMessage) (bool, InitialMessage)
	basicValidationNonInitialMessage(InitialMessage) (bool, InitialMessage)
	validateMessageTarget(InitialMessage) string
	validateMessageId(InitialMessage) string
	getMessageById(MessageId) InitialMessage
	getOutgoingNextMessageId() int
	getIncomingNextMessageId() int
	updateDIalogueLabel(Label)
	customValidation(InitialMessage) (bool, string)
	getStringRepresentation() string
}

// TODO
// FIgure out this
type FrozenSet SomeMessageType
type DialoguesInterface interface {
	initialize(selfAddress Address, endStates FrozenSet, _message_class InitialMessage, dialogueClass Dialogue, roleFromFirstMessage RoleType, keepTerminalStateDialogues bool)
	isKeepDIaloguesInTerminalState() bool
	selfAddress() Address
	messageClass() InitialMessage
	dialogueClass() Dialogue
	getDialoguesWithCounterParty(counterPArty Address) []Dialogue
	isMessageBySelf(InitialMessage) bool
	isMessageByOther(InitialMessage) bool
	counterPartyFromMessage(InitialMessage) Address
	newSelfInitiatedDialogueReference() [2]string
	create(counterParty Address, performative Performative, message SomeMessageType) (InitialMessage, Dialogue)
	createWithMessage(counterParty Address, intitialMessage InitialMessage) Dialogue
	createDialogue(counterParty Address, intitialMessage InitialMessage) Dialogue
	update(InitialMessage) Dialogue
	completeDialogueReference(InitialMessage)
	getDialogue(InitialMessage) Dialogue
	getLatestLabel(Label) Label
	getDialogueFromLabel(Label) Dialogue
	createSelfInitiated(dialogueOpponentAddress Address, dialogueReference [2]string, role RoleType) Dialogue
	createOpponentInitiated(dialogueOpponentAddress Address, dialogueReference [2]string, role RoleType) Dialogue
	createInternal(incompleteDialogueLabel Label, role RoleType, completeDialogueLabel Label) Dialogue
	generateDialogueNonce() string
	setUpDialogueStorage()
	tearDownDialogueStorage()
}

type MessageInterface interface {
	initialize(message SomeMessageType)
	validPerformatives() []string
	hasSender() bool
	sender() Address
	hasTo() bool
	to() Address
	dialogueReference() [2]string
	messageId() MessageId
	performative() Performative
	target() int
	equal(InitialMessage) bool
}

type Label struct {
	dialogueReference       [2]string
	dialogueOpponentAddress Address
	dialogueStarterAddress  Address
}

type Dialogue struct {
	dialogueLabel   Label
	dialogueMessage *InitialMessage
	selfAddress     Address
	// role RoleType
}

var dialogueStorage map[Address][]Label

type InitialMessage struct {
	dialogueReference [2]string
	message_id        int
	target            int
	performative      []string
	message           SomeMessageType
	to                Address
	sender            Address
}

func create(selfAddress Address, counterParty Address, performative Performative, message SomeMessageType) *Dialogue {

	if selfAddress == counterParty {
		fmt.Println("sender and receiver cannot be the same")
	}

	dialogueStorage = make(map[Address][]Label)

	intitialMessage := &InitialMessage{
		message_id:   0,
		target:       1,
		performative: performative,
		message:      message,
		to:           counterParty,
		sender:       selfAddress,
	}
	intitialMessage.dialogueReference[0] = generateDialogueNonce()
	intitialMessage.dialogueReference[1] = ""

	// process dialogue creation
	dialogue := intitialMessage.createDialogue()

	return dialogue
}

func (dialogue *Dialogue) update(selfAddress Address) {

	if dialogue.dialogueMessage.sender != "" || dialogue.dialogueMessage.to != "" {
		fmt.Println("Error : dialogue sender & receiver should not be empty")
	}

	if selfAddress != dialogue.selfAddress {
		fmt.Println("Error : Sender should be dialogue initiator")
	}

	if dialogue.dialogueMessage.sender == dialogue.dialogueMessage.to {
		fmt.Println("Error : Sender and receiver cannot be the same")
	}

	// check if diaglogReference is invalid
	invalid_label := dialogue.dialogueMessage.dialogueReference[0] != "" || dialogue.dialogueMessage.dialogueReference[1] != ""

	// check if dialog is new
	new_dialogue := dialogue.dialogueMessage.dialogueReference[0] != "" && dialogue.dialogueMessage.dialogueReference[1] == "" && dialogue.dialogueMessage.message_id == 1

	// check if dialogue is incomplete and having non-initial message
	incompleteLableAndNonInitialMessage := dialogue.dialogueMessage.dialogueReference[0] != "" && dialogue.dialogueMessage.dialogueReference[1] == "" && dialogue.dialogueMessage.message_id != 0 || dialogue.dialogueMessage.message_id != 1

	if invalid_label {
		// dialogue = empty
		return
	} else if new_dialogue {
		dialogue.createOpponentInitiated()
	} else if incompleteLableAndNonInitialMessage {
		dialogue.getDialogue()
	} else {
		dialogue.completeDialogurReference()
		dialogue.dialogueMessage.getDialogue()
	}
	if dialogue != nil {
		dialogue.internalUpdate()
		// if errors remove from storage
	}
}

func (dialogue *Dialogue) createOpponentInitiated() {
	if dialogue.dialogueMessage.dialogueReference[0] != "" && dialogue.dialogueMessage.dialogueReference[1] == "" {
		fmt.Println("Cannot initiate dialogue with preassigned dialogue responder")
	}
	dialogue.dialogueMessage.dialogueReference[0] = generateDialogueNonce()
	dialogue.dialogueMessage.createDialogue()
}

func (dialogue *Dialogue) getDialogue() {
	// self_inititalted_dialogue_label
	self_inititiated_dialogue_label := &Label{
		dialogueReference:       dialogue.dialogueLabel.dialogueReference,
		dialogueOpponentAddress: dialogue.dialogueMessage.to,
		dialogueStarterAddress:  dialogue.selfAddress,
	}
	// other inititalted_dialogue label
	other_inititiated_dialogue_label := &Label{
		dialogueReference:       dialogue.dialogueLabel.dialogueReference,
		dialogueOpponentAddress: dialogue.dialogueMessage.to,
		dialogueStarterAddress:  dialogue.dialogueMessage.to,
	}
	// get latest self initiated dialogur label
	pair := dialogue.dialogueMessage.sender + dialogue.dialogueMessage.to
	if len(dialogueStorage[pair]) > 0 {
		index := len(dialogueStorage[pair])
		dialogueStorage[pair][index]
	}

	// get other initiated dialogue label
	// get delf initiated dialogue from label
	// get other initiated dialogue from label
}

func (data *InitialMessage) createDialogue() *Dialogue {

	// TODO
	// define dialog ROLE for dialog initiator

	incompleteDialogueLabel := data.checkAndProcessLabels()
	pair := data.sender + data.to
	if len(dialogueStorage[pair]) > 0 {
		for _, dialogue := range dialogueStorage[pair] {
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
		for _, dialogue := range dialogueStorage[data.sender+data.to] {
			if dialogueLabel == dialogue {
				fmt.Println("Error : Dialogue label already present in storage")
				return nil
			}
		}
	}

	dialogue := &Dialogue{
		dialogueLabel:   dialogueLabel,
		dialogueMessage: data,
		selfAddress:     data.sender,
	}

	return dialogue

}

func (data *InitialMessage) checkAndProcessLabels() Label {
	if !(data.dialogueReference[0] != "" && data.dialogueReference[1] == "") {
		fmt.Println("Error : Reference address label already exists")
	}
	return Label{
		dialogueReference:       data.dialogueReference,
		dialogueOpponentAddress: data.to,
		dialogueStarterAddress:  data.sender,
	}
}

func generateDialogueNonce() string {
	hexValue := randomHex(NONCE_BYTES_NB)
	return hexValue
}

func randomHex(n int) string {
	bytes := make([]byte, n)
	if _, err := rand.Read(bytes); err != nil {
		return ""
	}
	return hex.EncodeToString(bytes)
}
