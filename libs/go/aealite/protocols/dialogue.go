package protocols

import (
	"bytes"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"math"
	"strings"
)

type Address string
type Performative string
type Role string

const (
	NonceBytesNb                           = 32
	Role1                        Role      = "role1"
	Role2                        Role      = "role2"
	StartingMessageId            MessageId = 1
	StartingTarget               MessageId = 0
	UnassignedDialogueReference            = ""
	DialogueLabelStringSeparator           = "_"
)

type RuleType struct {
	initialPerformatives  Performative
	terminalPerformatives Performative
	validReplies          map[string][]Performative
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
	DialogueReference       [2]string
	DialogueOpponentAddress Address
	DialogueStarterAddress  Address
}

// Get the dialogue starter reference.
func (dialogueLabel *DialogueLabel) getDialogueStarterReference() string {
	return dialogueLabel.DialogueReference[0]
}

// Get the dialogue responder reference.
func (dialogueLabel *DialogueLabel) getDialogueResponderReference() string {
	return dialogueLabel.DialogueReference[1]
}

// Get the incomplete version of the label.
func (dialogueLabel *DialogueLabel) getIncompleteVersion() DialogueLabel {
	return DialogueLabel{
		[2]string{dialogueLabel.getDialogueStarterReference(), UnassignedDialogueReference},
		dialogueLabel.DialogueOpponentAddress,
		dialogueLabel.DialogueStarterAddress,
	}
}

func (dialogueLabel DialogueLabel) MarshalJSON() ([]byte, error) {
	data := map[string]string{
		"dialogue_starter_reference":   dialogueLabel.getDialogueStarterReference(),
		"dialogue_responder_reference": dialogueLabel.getDialogueResponderReference(),
		"dialogue_opponent_addr":       string(dialogueLabel.DialogueOpponentAddress),
		"dialogue_starter_addr":        string(dialogueLabel.DialogueStarterAddress),
	}
	buffer := bytes.NewBufferString("{")
	for key, value := range data {
		buffer.WriteString(fmt.Sprintf("\"%s\": \"%s\",", key, value))
	}
	buffer.Truncate(buffer.Len() - 1)
	buffer.WriteString("}")
	return buffer.Bytes(), nil
}

func (dialogueLabel *DialogueLabel) UnmarshalJSON(b []byte) error {
	var data map[string]string
	err := json.Unmarshal(b, &data)
	if err != nil {
		return err
	}
	starterReference := data["dialogue_starter_reference"]
	responderReference := data["dialogue_responder_reference"]
	dialogueLabel.DialogueReference = [2]string{starterReference, responderReference}
	dialogueLabel.DialogueOpponentAddress = Address(data["dialogue_opponent_addr"])
	dialogueLabel.DialogueStarterAddress = Address(data["dialogue_starter_addr"])
	return nil
}

func (dialogueLabel *DialogueLabel) String() string {
	return strings.Join([]string{dialogueLabel.getDialogueStarterReference(),
		dialogueLabel.getDialogueResponderReference(),
		string(dialogueLabel.DialogueOpponentAddress),
		string(dialogueLabel.DialogueStarterAddress)}, DialogueLabelStringSeparator)
}

func (dialogueLabel *DialogueLabel) FromString(s string) error {
	result := strings.Split(s, DialogueLabelStringSeparator)
	if length := len(result); length != 4 {
		return errors.New(fmt.Sprintf("Expected exactly 4 parts, got %d", length))
	}
	dialogueLabel.DialogueReference = [2]string{result[0], result[1]}
	dialogueLabel.DialogueOpponentAddress = Address(result[2])
	dialogueLabel.DialogueStarterAddress = Address(result[3])
	return nil
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
	if dialogueReference[0] != dialogue.dialogueLabel.DialogueReference[0] {
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
	if dialogueReference[0] != dialogue.dialogueLabel.DialogueReference[0] {
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
	var lastIncomingMessage = dialogue.lastIncomingMessage()
	if lastIncomingMessage != nil {
		latestIds = append(latestIds, lastIncomingMessage.messageId)
	}
	var lastOutgoingMessage = dialogue.lastOutgoingMessage()
	if lastOutgoingMessage != nil {
		latestIds = append(latestIds, lastOutgoingMessage.messageId)
	}
	// TODO
	//targetMessage, err := dialogue.getMessageById(target)
	//if err != nil {
	//	return err
	//}
	//targetPerformative := targetMessage.performative

	// check performatives

	// target_performative = target_message.performative
	// if performative not in self.rules.get_valid_replies(target_performative):
	//     return "Invalid performative. Expected one of {}. Found {}.".format(
	//         self.rules.get_valid_replies(target_performative), performative
	//     )
	return nil
}

func (dialogue *Dialogue) getMessageById(messageId MessageId) (*AbstractMessage, error) {
	if dialogue.isEmpty() {
		return nil, errors.New("Error : Dialogue is empty.")
	}
	if messageId == 0 {
		return nil, errors.New("message_id = 0 is invalid!")

	}
	var messages_list []AbstractMessage
	if messageId > 0 && dialogue.isSelfInitiated() {
		messages_list = dialogue.outgoingMessages
	} else {
		messages_list = dialogue.incomingMessages
	}
	if len(messages_list) == 0 {
		return nil, errors.New("Dialogue is empty.")
	}
	if MessageId(messageId) > messages_list[len(messages_list)-1].messageId {
		return nil, errors.New("Message id is invalid,  > max existing.")
	}
	return &messages_list[MessageId(math.Abs(float64(messageId)))-1], nil
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
	if message.messageId != nextMessageId {
		return errors.New("invalid message_id")
	}
	return nil
}

func (dialogue *Dialogue) getOutgoingNextMessageId() MessageId {
	nextMessageId := StartingMessageId
	if dialogue.lastOutgoingMessage() != nil {
		nextMessageId = dialogue.lastMessageId + 1
	}
	if dialogue.isSelfInitiated() {
		nextMessageId = 0 - nextMessageId
	}
	return nextMessageId
}

func (dialogue *Dialogue) getIncomingNextMessageId() MessageId {
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
	if length := len(dialogue.outgoingMessages); length > 0 {
		return &dialogue.outgoingMessages[length-1]
	}
	return nil
}

func (dialogue Dialogue) lastIncomingMessage() *AbstractMessage {
	if length := len(dialogue.incomingMessages); length > 0 {
		return &dialogue.incomingMessages[length-1]
	}
	return nil
}

func (dialogue *Dialogue) isSelfInitiated() bool {
	return dialogue.dialogueLabel.DialogueStarterAddress != dialogue.dialogueLabel.DialogueOpponentAddress
}

func (dialogue *Dialogue) isEmpty() bool {
	return len(dialogue.outgoingMessages) == 0 && len(dialogue.incomingMessages) == 0
}

func (dialogue *Dialogue) updateIncomingAndOutgoingMessages(message AbstractMessage) {
	if dialogue.dialogueLabel.DialogueStarterAddress == dialogue.selfAddress {
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
	if dialogue.selfAddress == dialogue.dialogueLabel.DialogueStarterAddress {
		label = DialogueLabel{
			DialogueReference:       [2]string{message.dialogueReference[0], ""},
			DialogueOpponentAddress: opponent,
			DialogueStarterAddress:  dialogue.selfAddress,
		}
	} else {
		label = DialogueLabel{
			DialogueReference:       message.dialogueReference,
			DialogueOpponentAddress: opponent,
			DialogueStarterAddress:  opponent,
		}
	}
	result := validateDialogueLabelExistence(label)
	return result
}

func InitializeMessage(
	counterParty Address,
	selfAddress Address,
	performative Performative,
	content []byte,
	ref [2]string,
	messageId MessageId,
	target MessageId,
) AbstractMessage {
	var reference [2]string
	if ref[0] != "" || ref[1] != "" {
		reference = ref
	} else {
		reference = [2]string{
			generateDialogueNonce(), "",
		}
	}
	initialMessage := AbstractMessage{
		dialogueReference: reference,
		messageId:         messageId,
		target:            target,
		performative:      performative,
		to:                counterParty,
		sender:            selfAddress,
		message:           content,
	}
	return initialMessage
}

// func (dialogue *Dialogue) getNextMessageId() MessageId {
// 	if len(dialogue.orderedMessageIds) == 0 {
// 		return StartingMessageId
// 	}
// 	return dialogue.orderedMessageIds[len(dialogue.orderedMessageIds)-1] + 1
// }

func Create(counterParty Address,
	selfAddress Address,
	performative Performative,
	content []byte) (AbstractMessage, Dialogue) {
	initialMessage := InitializeMessage(
		counterParty,
		selfAddress,
		performative,
		content,
		[2]string{"", ""},
		StartingMessageId,
		StartingTarget,
	)
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
		DialogueReference:       message.dialogueReference,
		DialogueOpponentAddress: message.to,
		DialogueStarterAddress:  message.sender,
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
