package protocols

import (
	"crypto/rand"
	"encoding/hex"
	"errors"
	"fmt"
)

type Address string
type Performative []string
type SomeMessageType string

const (
	NONCE_BYTES_NB = 32
)

type Role string

const (
	Role1             Role = "role1"
	Role2             Role = "role2"
	StartingMessageId      = 1
	StartingTarget         = 0
)

type RuleType struct {
	initialPerformative  Performative
	terminalPerformative Performative
	// validReplies
}

type MessageId int
type Target []int
type DialogueInterface interface {
	initialize(selfAddress Address, counterParty Address, role Role)
	getSelfAddress() Address
	getRole() Role
	getRules() RuleType
	getMessageClass() AbstractMessage
	isSelfInitiated() bool
	getLastIncomingMessage() AbstractMessage
	getLastOutgoingMessage() AbstractMessage
	getLastMessage() AbstractMessage
	counterPartyForMessage(AbstractMessage) bool
	isMessageBySelf(AbstractMessage) bool
	isMessageByOther(AbstractMessage) bool
	getMessage(MessageId) AbstractMessage
	hasMessageId(MessageId) bool

	update(AbstractMessage)
	validateNextMessage(AbstractMessage) (bool, string)
	basicValidations(AbstractMessage) (bool, string)
	basicValidationInitialMessage(AbstractMessage) (bool, string)
	basicValidationNonInitialMessage(AbstractMessage) (bool, string)
	isEmpty() bool
	updateIncomingAndOutgoingMessages(AbstractMessage)
	isBelongingToADialogue(AbstractMessage) bool

	validateMessageTarget(AbstractMessage) string
	validateMessageId(AbstractMessage) string
	getMessageById(MessageId) AbstractMessage
	getOutgoingNextMessageId() int
	getIncomingNextMessageId() int
	updateDialogueLabel(DialogueLabel)
	customValidation(AbstractMessage) (bool, string)
	getStringRepresentation() string
}
type AbstractMessageInterface interface {
	validPerformatives() []string
	hasSender() (Address, error)
	hasCounterparty() (Address, error)
	dialogueReference() [2]string
	messageId() MessageId
	performative() Performative
	target() int
}

func (message AbstractMessage) hasSender() (Address, error) {
	if message.sender != "" {
		return message.sender, nil
	}
	return "", errors.New("Sender address does not exist.")
}

func (message AbstractMessage) hasCounterparty() (Address, error) {
	if message.to != "" {
		return message.to, nil
	}
	return "", errors.New("Counterparty address does not exist.")
}

type DialogueLabel struct {
	dialogueReference       [2]string
	dialogueOpponentAddress Address
	dialogueStarterAddress  Address
}

type Dialogue struct {
	dialogueLabel     DialogueLabel
	dialogueMessage   AbstractMessage
	selfAddress       Address
	outgoingMessages  []AbstractMessage
	incomingMessages  []AbstractMessage
	lastMessageId     int
	orderedMessageIds []int
	rules             RuleType
}
type AbstractMessage struct {
	dialogueReference [2]string
	messageId         int
	target            int
	performative      []string
	message           []byte
	to                Address
	sender            Address
}

// store dialogues by opponent address
var dialogueStorage = make(map[Address][]Dialogue)

// store dialogue by dialogue label
var dialogueByDialogueLabel = make(map[DialogueLabel]Dialogue)

func (dialogue Dialogue) update(message AbstractMessage) {
	if message.sender == "" {
		message.sender = dialogue.selfAddress
	}
	messageExistence := dialogue.isBelongingToADialogue(message)
	if !messageExistence {
		fmt.Println("Error: message does not exist to this dialogue")
	}

	// TODO
	// validate next message
	// check if dialogue message is valid
	dialogue.validateNextMessage(message)
	dialogue.updateIncomingAndOutgoingMessages(message)
}

func (dialogue Dialogue) validateNextMessage(message AbstractMessage) (bool, string) {
	is_basic_validated, msg_basic_validation := dialogue.basicValidation(message)
	if !is_basic_validated {
		return false, msg_basic_validation
	}
	// TODO
	// check if custom validation
	return True, "Message is valid with respect to this dialogue."
}

func (dialogue Dialogue) basicValidation(message AbstractMessage) {
	if dialogue.isEmpty() {
		return dialogue.basicValidationInitialMessage(message)
	}
	return dialogue.basicValidationNonInitialMessage(message)
}

func (dialogue Dialogue) basicValidationInitialMessage(message AbstractMessage) (bool, string) {
	dialogue_reference := message.dialogueReference
	message_id := message.messageId
	// performative := message.performative
	if dialogue_reference[0] != dialogue.dialogueLabel.dialogueReference[0] {
		return false, "Invalid dialogue_reference[0]."
	}
	if message_id != StartingMessageId {
		return false, "Invalid message_id."
	}

	// TODO
	// validate message target
	// err := dialogue.validateMessageTarget(message)
	// if err != nil{
	// 	return false, err
	// }

	// TODO
	// check if performative exists in intial performatives
	// if dialogue.rules.initial_performatives {
	// 	return (
	//         false,
	//         "Invalid initial performative."
	//     )
	// }
	return true, "The initial message passes basic validation."
}

func (dialogue Dialogue) isEmpty() bool {
	return len(dialogue.outgoingMessages) == 0 && len(dialogue.incomingMessages) == 0
}

func (dialogue Dialogue) updateIncomingAndOutgoingMessages(message AbstractMessage) {
	if message.sender == dialogue.selfAddress {
		dialogue.outgoingMessages = append(dialogue.outgoingMessages, message)
	} else {
		dialogue.incomingMessages = append(dialogue.incomingMessages, message)
	}
	// update last message id
	dialogue.lastMessageId = message.messageId
	// append message ids in ordered manner
	dialogue.orderedMessageIds = append(dialogue.orderedMessageIds, message.messageId)
}

func (dialogue Dialogue) isBelongingToADialogue(message AbstractMessage) bool {
	opponent, err := message.hasCounterparty()
	if err != nil {
		fmt.Println("Error:", err)
	}
	var label DialogueLabel
	if dialogue.selfAddress == dialogue.dialogueLabel.dialogueStarterAddress {
		label = DialogueLabel{
			dialogueReference:       [2]string{message.dialogueReference[0], ""},
			dialogueOpponentAddress: opponent,
			dialogueStarterAddress:  dialogue.selfAddress,
		}
	} else {
		label = DialogueLabel{
			dialogueReference:       message.dialogueReference,
			dialogueOpponentAddress: opponent,
			dialogueStarterAddress:  opponent,
		}
	}
	result := validateDialogueLabelExistence(label)
	return result
}

func create(counterParty Address, selfAddress Address, performative Performative, content []byte) (AbstractMessage, Dialogue) {
	reference := [2]string{
		generateDialogueNonce(), "",
	}
	initialMessage := AbstractMessage{
		dialogueReference: reference,
		messageId:         StartingMessageId,
		target:            StartingTarget,
		performative:      performative,
		to:                counterParty,
		sender:            selfAddress,
		message:           content,
	}
	dialogue := createDialogue(initialMessage)

	return initialMessage, dialogue
}

func createDialogue(message AbstractMessage) Dialogue {
	dialogueLabel := checkReferencesAndCreateLabels(message)
	if validation := validateDialogueLabelExistence(dialogueLabel); validation {
		dialogue := Dialogue{
			dialogueLabel:   dialogueLabel,
			dialogueMessage: message,
			selfAddress:     message.sender,
		}
		dialogueStorage[message.to] = append(dialogueStorage[message.to], dialogue)
		dialogueByDialogueLabel[dialogueLabel] = dialogue
		// update dialogue using abstractmessage
		updateInitialDialogue(message, dialogue)
		return dialogue
	}
	return Dialogue{}
}

func updateInitialDialogue(message AbstractMessage, dialogue Dialogue) {
	// check if message has sender
	if _, err := message.hasSender(); err != nil {
		fmt.Println(err)
		return
	}
	// check if message belongs to a dialogue

	// TODO
	// create and check labels considering self initiated addresses
	label := checkReferencesAndCreateLabels(message)
	if _, ok := dialogueByDialogueLabel[label]; !ok {
		fmt.Println("Message does not belong to a dialogue")
	}

	// TODO
	// validate next message
	// check if dialogue message is valid

	// check if message is by self
	// append message to outgoing message, if not append to incoming message
	dialogue.updateIncomingAndOutgoingMessages(message)
}

func checkReferencesAndCreateLabels(message AbstractMessage) DialogueLabel {
	if !(message.dialogueReference[0] != "" && message.dialogueReference[1] == "") {
		fmt.Println("Error : Reference address label already exists")
	}
	return DialogueLabel{
		dialogueReference:       message.dialogueReference,
		dialogueOpponentAddress: message.to,
		dialogueStarterAddress:  message.sender,
	}
}

func validateDialogueLabelExistence(dialogueLabel DialogueLabel) bool {
	if _, ok := dialogueByDialogueLabel[dialogueLabel]; ok {
		return false
	}
	return true
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
