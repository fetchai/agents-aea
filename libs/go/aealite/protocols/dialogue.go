package protocols

import (
	"crypto/rand"
	"encoding/hex"
	"errors"
	"fmt"
	"math"
)

type Address string
type Performative []string

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
	validReplies          map[string][]Performative
}

type MessageId int
type Target int
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

func (dialogue *Dialogue) update(message AbstractMessage) error {
	if message.sender == "" {
		message.sender = dialogue.selfAddress
	}
	messageExistence := dialogue.isBelongingToADialogue(message)
	if !messageExistence {
		return errors.New("message does not exist to this dialogue")
	}
	if _, err := dialogue.validateNextMessage(message); err != nil {
		return err
	}
	fmt.Println("-----", dialogue.orderedMessageIds)
	dialogue.updateIncomingAndOutgoingMessages(message)
	return nil
}

func (dialogue *Dialogue) validateNextMessage(message AbstractMessage) (bool, error) {
	isBasicValidated, msgBasicValidation := dialogue.basicValidation(message)
	if !isBasicValidated {
		return false, msgBasicValidation
	}
	// TODO
	// check if custom validation
	return true, nil
}

func (dialogue *Dialogue) basicValidation(message AbstractMessage) (bool, error) {
	if dialogue.isEmpty() {
		return dialogue.basicValidationInitialMessage(message)
	}
	return dialogue.basicValidationNonInitialMessage(message)
}

func (dialogue *Dialogue) basicValidationInitialMessage(message AbstractMessage) (bool, error) {
	dialogueReference := message.dialogueReference
	messageId := message.messageId
	// performative := message.performative
	if dialogueReference[0] != dialogue.dialogueLabel.dialogueReference[0] {
		return false, errors.New("Invalid dialogue_reference[0].")
	}
	if messageId != StartingMessageId {
		return false, errors.New("Invalid message_id.")
	}

	err := dialogue.validateMessageTarget(message)
	if err != nil {
		return false, err
	}

	// TODO
	// check if performative exists in intial performatives
	// if dialogue.rules.initial_performatives {
	// 	return (
	//         false,
	//         "Invalid initial performative."
	//     )
	// }
	return true, errors.New("The initial message passes basic validation.")
}

func (dialogue *Dialogue) basicValidationNonInitialMessage(message AbstractMessage) (bool, error) {
	dialogueReference := message.dialogueReference
	if dialogueReference[0] != dialogue.dialogueLabel.dialogueReference[0] {
		return false, errors.New("Invalid dialogue_reference[0].")
	}
	err := dialogue.validateMessageId(message)
	if err != nil {
		return false, err
	}
	error := dialogue.validateMessageTarget(message)
	if error != nil {
		return false, error
	}
	return true, errors.New("The non-initial message passes basic validation.")
}

func (dialogue *Dialogue) validateMessageTarget(message AbstractMessage) error {
	target := message.target
	// performative := message.performative

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
	if ok, id := dialogue.lastIncomingMessage(); ok {
		latestIds = append(latestIds, id)
	}
	if ok, id := dialogue.lastOutgoingMessage(); ok {
		latestIds = append(latestIds, id)
	}
	if target > max(latestIds) {
		return errors.New("invalid target")
	}
	if _, err := dialogue.getMessageById(int(target)); err != nil {
		return err
	}
	// TODO
	// check performatives

	// target_performative = target_message.performative
	// if performative not in self.rules.get_valid_replies(target_performative):
	//     return "Invalid performative. Expected one of {}. Found {}.".format(
	//         self.rules.get_valid_replies(target_performative), performative
	//     )
	return nil
}

func (dialogue *Dialogue) getMessageById(messageId int) (AbstractMessage, error) {
	if dialogue.isEmpty() {
		return AbstractMessage{}, errors.New("Error : Dialogue is empty.")
	}
	if messageId == 0 {
		return AbstractMessage{}, errors.New("message_id = 0 is invalid!")

	}
	var messages_list []AbstractMessage
	if messageId > 0 && dialogue.isSelfInitiated() {
		messages_list = dialogue.outgoingMessages
	} else {
		messages_list = dialogue.incomingMessages
	}
	if len(messages_list) == 0 {
		return AbstractMessage{}, errors.New("Dialogue is empty.")
	}
	if MessageId(messageId) > messages_list[len(messages_list)-1].messageId {
		return AbstractMessage{}, errors.New("Message id is invalid,  > max existing.")
	}
	return messages_list[messageId-1], nil
}

func max(list []MessageId) MessageId {
	max := list[0]
	for i := 1; i < len(list); i++ {
		if max < list[i] {
			max = list[i]
		}
	}
	return max
}

func (dialogue *Dialogue) validateMessageId(message AbstractMessage) error {
	var nextMessageId MessageId
	if message.to != dialogue.selfAddress {
		nextMessageId = dialogue.getOutgoingNextMessageId()
	} else {
		nextMessageId = dialogue.getIncomingNextMessageId()
	}
	fmt.Println("next message id should be : ", nextMessageId, "  current message id is : ", message.messageId)
	if message.messageId != nextMessageId {
		return errors.New("invalid message_id")
	}
	return nil
}

func (dialogue *Dialogue) getOutgoingNextMessageId() MessageId {
	nextMessageId := StartingMessageId
	if ok, _ := dialogue.lastOutgoingMessage(); ok {
		nextMessageId = MessageId(math.Abs(float64(dialogue.lastMessageId))) + 1
	}
	if dialogue.isSelfInitiated() {
		nextMessageId = 0 - nextMessageId
	}
	return nextMessageId
}

func (dialogue *Dialogue) getIncomingNextMessageId() MessageId {
	nextMessageId := StartingMessageId
	if ok, _ := dialogue.lastIncomingMessage(); ok {
		nextMessageId = MessageId(math.Abs(float64(dialogue.lastMessageId))) + 1
	}
	if dialogue.isSelfInitiated() {
		nextMessageId = 0 - nextMessageId
	}
	return nextMessageId
}

func (dialogue *Dialogue) lastOutgoingMessage() (bool, MessageId) {
	if len(dialogue.outgoingMessages) > 0 {
		return true, dialogue.outgoingMessages[len(dialogue.outgoingMessages)-1].messageId
	} else {
		return false, 0
	}
}

func (dialogue *Dialogue) lastIncomingMessage() (bool, MessageId) {
	if len(dialogue.incomingMessages) > 0 {
		return true, dialogue.incomingMessages[len(dialogue.incomingMessages)-1].messageId
	} else {
		return false, 0
	}
}

func (dialogue *Dialogue) isSelfInitiated() bool {
	return dialogue.dialogueLabel.dialogueStarterAddress != dialogue.dialogueLabel.dialogueOpponentAddress
}

func (dialogue *Dialogue) isEmpty() bool {
	return len(dialogue.outgoingMessages) == 0 && len(dialogue.incomingMessages) == 0
}

func (dialogue *Dialogue) updateIncomingAndOutgoingMessages(message AbstractMessage) {
	if dialogue.dialogueLabel.dialogueStarterAddress == dialogue.selfAddress {
		dialogue.outgoingMessages = append(dialogue.outgoingMessages, message)
	} else {
		dialogue.incomingMessages = append(dialogue.incomingMessages, message)
	}
	// update last message id
	dialogue.lastMessageId = message.messageId
	// append message ids in ordered manner
	dialogue.orderedMessageIds = append(dialogue.orderedMessageIds, message.messageId)
}

func (dialogue *Dialogue) isBelongingToADialogue(message AbstractMessage) bool {
	opponent, err := message.hasCounterparty()
	if err != nil {
		fmt.Println("Error:", err)
		return false
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

func InitializeMessage(counterParty Address, selfAddress Address, performative Performative, content []byte, ref [2]string, messageId MessageId) AbstractMessage {
	var reference [2]string
	if ref[0] != "" || ref[1] != "" {
		reference = ref
	} else {
		reference = [2]string{
			generateDialogueNonce(), "",
		}
	}
	var target MessageId
	if messageId == StartingMessageId {
		target = StartingTarget
	} else {
		target = messageId - 1
	}
	initialMessage := AbstractMessage{
		dialogueReference: reference,
		messageId:         MessageId(messageId),
		target:            target,
		performative:      performative,
		to:                counterParty,
		sender:            selfAddress,
		message:           content,
	}
	return initialMessage
}

func (dialogue *Dialogue) getNextMessageId() MessageId {
	if len(dialogue.orderedMessageIds) == 0 {
		return StartingMessageId
	}
	return dialogue.orderedMessageIds[len(dialogue.orderedMessageIds)-1] + 1
}

func Create(counterParty Address, selfAddress Address, performative Performative, content []byte) (AbstractMessage, Dialogue) {
	initialMessage := InitializeMessage(counterParty, selfAddress, performative, content, [2]string{"", ""}, StartingMessageId)
	dialogue := createDialogue(initialMessage)
	return initialMessage, dialogue
}

func createDialogue(message AbstractMessage) Dialogue {
	dialogueLabel := checkReferencesAndCreateLabels(message)
	if validation := validateDialogueLabelExistence(dialogueLabel); !validation {
		dialogue := Dialogue{
			dialogueLabel:   dialogueLabel,
			dialogueMessage: message,
			selfAddress:     message.sender,
		}
		dialogueStorage[message.to] = append(dialogueStorage[message.to], dialogue)
		dialogueByDialogueLabel[dialogueLabel] = dialogue
		// update dialogue using abstractmessage
		dialogue.updateInitialDialogue(message)
		return dialogue
	}
	return Dialogue{}
}

func (dialogue *Dialogue) updateInitialDialogue(message AbstractMessage) {
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
	if _, ok := dialogueByDialogueLabel[dialogueLabel]; !ok {
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
