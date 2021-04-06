package protocols

import (
	"crypto/rand"
	"encoding/hex"
	"errors"
	"fmt"
)

type Address string
type Performative string
type SomeMessageType string

const (
	NonceBytesNb = 32
)

type Role string

const (
	Role1             Role      = "role1"
	Role2             Role      = "role2"
	StartingMessageId MessageId = 1
	StartingTarget    MessageId = 0
)

type RuleType struct {
	initialPerformatives  Performative
	terminalPerformatives Performative
	validReplies          map[Performative][]Performative
}

type MessageId int
type DialogueInterface interface {
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
	getOutgoingNextMessageId() MessageId
	getIncomingNextMessageId() MessageId
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
	target() MessageId
}

func (message AbstractMessage) hasSender() (Address, error) {
	if message.sender != "" {
		return message.sender, nil
	}
	return "", errors.New("sender address does not exist")
}

func (message AbstractMessage) hasCounterparty() (Address, error) {
	if message.to != "" {
		return message.to, nil
	}
	return "", errors.New("counterparty address does not exist")
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
	lastMessageId     MessageId
	orderedMessageIds []MessageId
	rules             RuleType
}
type AbstractMessage struct {
	dialogueReference [2]string
	messageId         MessageId
	target            MessageId
	performative      Performative
	message           []byte
	to                Address
	sender            Address
}

// store dialogues by opponent address
var dialogueStorage = make(map[Address][]Dialogue)

// store dialogue by dialogue label
var dialogueByDialogueLabel = make(map[DialogueLabel]Dialogue)

func (dialogue Dialogue) update(message AbstractMessage) error {
	if message.sender == "" {
		message.sender = dialogue.selfAddress
	}
	messageExistence := dialogue.isBelongingToADialogue(message)
	if !messageExistence {
		return errors.New("message does not exist to this dialogue")
	}

	// TODO
	// validate next message
	// check if dialogue message is valid
	dialogue.validateNextMessage(message)
	dialogue.updateIncomingAndOutgoingMessages(message)
	return nil
}

func (dialogue Dialogue) validateNextMessage(message AbstractMessage) (bool, string) {
	isBasicValidated, msgBasicValidation := dialogue.basicValidation(message)
	if !isBasicValidated {
		return false, msgBasicValidation
	}
	// TODO
	// check if custom validation
	return true, "Message is valid with respect to this dialogue."
}

func (dialogue Dialogue) basicValidation(message AbstractMessage) (bool, string) {
	if dialogue.isEmpty() {
		return dialogue.basicValidationInitialMessage(message)
	}
	return dialogue.basicValidationNonInitialMessage(message)
}

func (dialogue Dialogue) basicValidationInitialMessage(message AbstractMessage) (bool, string) {
	dialogueReference := message.dialogueReference
	messageId := message.messageId
	// performative := message.performative
	if dialogueReference[0] != dialogue.dialogueLabel.dialogueReference[0] {
		return false, "Invalid dialogue_reference[0]."
	}
	if messageId != StartingMessageId {
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

func (dialogue Dialogue) basicValidationNonInitialMessage(message AbstractMessage) (bool, string) {
	dialogueReference := message.dialogueReference
	if dialogueReference[0] != dialogue.dialogueLabel.dialogueReference[0] {
		return false, "Invalid dialogue_reference[0]."
	}
	err := dialogue.validateMessageId(message)
	if err != nil {
		return false, err.Error()
	}
	err = dialogue.validateMessageTarget(message)
	if err != nil {
		return false, err.Error()
	}
	return true, "The non-initial message passes basic validation."
}

func (dialogue Dialogue) validateMessageTarget(message AbstractMessage) error {
	target := message.target
	performative := message.performative

	if message.messageId == StartingMessageId {
		if target == StartingTarget {
			return nil
		}
		return errors.New(fmt.Sprintf("invalid target; expected 0, found %v", target))
	}
	if message.messageId != StartingMessageId && target == StartingTarget {
		return errors.New(
			fmt.Sprintf("invalid target, expected a non-zero integer, found %v", target),
		)
	}
	var latestIds []MessageId
	var lastIncomingMessage = dialogue.lastIncomingMessage()
	if lastIncomingMessage != nil {
		latestIds = append(latestIds, lastIncomingMessage.messageId)
	}
	var lastOutgoingMessage = dialogue.lastIncomingMessage()
	if lastOutgoingMessage != nil {
		latestIds = append(latestIds, lastOutgoingMessage.messageId)
	}
	if target > max(latestIds) {
		return errors.New("invalid target")
	}

	// TODO
	// implement function getmessageby id
	targetMessage := dialogue.getMessageById(target)

	if targetMessage == nil {
		return errors.New("invalid target")
	}
	targetPerformative := targetMessage.performative
	//if performative not in self.rules.get_valid_replies(targetPerformative):
	//    return "Invalid performative. Expected one of {}. Found {}.".format(
	//        self.rules.get_valid_replies(targetPerformative), performative
	//    )
	return nil
}

func max(list []MessageId) MessageId {
	currentMax := list[0]
	for _, element := range list {
		if currentMax < element {
			currentMax = element
		}
	}
	return currentMax
}

func (dialogue Dialogue) validateMessageId(message AbstractMessage) error {
	var nextMessageId MessageId
	if message.to != dialogue.selfAddress {
		nextMessageId = dialogue.getOutgoingNextMessageId()
	} else {
		nextMessageId = dialogue.getIncomingNextMessageId()
	}
	if message.messageId != nextMessageId {
		return errors.New("invalid message_id")
	}
	return nil
}

func (dialogue Dialogue) getOutgoingNextMessageId() MessageId {
	nextMessageId := StartingMessageId
	if dialogue.lastOutgoingMessage() != nil {
		nextMessageId = dialogue.lastMessageId + 1
	}
	if dialogue.isSelfInitiated() {
		nextMessageId = 0 - nextMessageId
	}
	return nextMessageId
}

func (dialogue Dialogue) getMessageById(messageId MessageId) *AbstractMessage {
	// TODO
}

func (dialogue Dialogue) getIncomingNextMessageId() MessageId {
	nextMessageId := StartingMessageId
	if dialogue.lastIncomingMessage() != nil {
		nextMessageId = dialogue.lastMessageId + 1
	}
	if dialogue.isSelfInitiated() {
		nextMessageId = 0 - nextMessageId
	}
	return nextMessageId
}

func (dialogue Dialogue) lastOutgoingMessage() *AbstractMessage {
	length := len(dialogue.outgoingMessages)
	if length > 0 {
		return &dialogue.outgoingMessages[length-1]
	}
	return nil
}

func (dialogue Dialogue) lastIncomingMessage() *AbstractMessage {
	length := len(dialogue.incomingMessages)
	if length > 0 {
		return &dialogue.incomingMessages[length-1]
	}
	return nil
}

func (dialogue Dialogue) isSelfInitiated() bool {
	return dialogue.dialogueLabel.dialogueStarterAddress == dialogue.dialogueLabel.dialogueOpponentAddress
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

func create(
	counterParty Address,
	selfAddress Address,
	performative Performative,
	content []byte,
) (AbstractMessage, Dialogue) {
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
	hexValue := randomHex(NonceBytesNb)
	return hexValue
}

func randomHex(n int) string {
	bytes := make([]byte, n)
	if _, err := rand.Read(bytes); err != nil {
		return ""
	}
	return hex.EncodeToString(bytes)
}
