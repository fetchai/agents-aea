/* -*- coding: utf-8 -*-
* ------------------------------------------------------------------------------
*
*   Copyright 2018-2019 Fetch.AI Limited
*
*   Licensed under the Apache License, Version 2.0 (the "License");
*   you may not use this file except in compliance with the License.
*   You may obtain a copy of the License at
*
*       http://www.apache.org/licenses/LICENSE-2.0
*
*   Unless required by applicable law or agreed to in writing, software
*   distributed under the License is distributed on an "AS IS" BASIS,
*   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
*   See the License for the specific language governing permissions and
*   limitations under the License.
*
* ------------------------------------------------------------------------------
 */

package protocols

import (
	"crypto/rand"
	"encoding/hex"
	"errors"
	"fmt"
	"math"
)

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

/* Utility methods */

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

/* Definition of main data types */

type Rules struct {
	initialPerformatives  Performative
	terminalPerformatives Performative
	validReplies          map[string][]Performative
}

type DialogueInterface interface {
	// getters

	DialogueLabel() DialogueLabel
	IncompleteDialogueLabel() DialogueLabel
	DialogueLabels() [2]DialogueLabel
	SelfAddress() Address
	Role() Role
	Rules() Rules
	getMessageClass() AbstractMessage
	IsSelfInitiated() bool
	LastIncomingMessage() AbstractMessage
	LastOutgoingMessage() AbstractMessage
	LastMessage() AbstractMessage

	counterPartyFromMessage(AbstractMessage) Address
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

/* Dialogue definition and methods */

type Dialogue struct {
	dialogueLabel          DialogueLabel     // dialogueLabel: the dialogue label for this dialogue
	role                   Role              // role: the role of the agent this dialogue is maintained for
	selfAddress            Address           // selfAddress: the address of the entity for whom this dialogue is maintained
	dialogueMessage        AbstractMessage   // TODO (should be a type but golang does not support type variables)
	outgoingMessages       []AbstractMessage // outgoingMessages: list of outgoing messages
	incomingMessages       []AbstractMessage // incomingMessages: list of incoming messages
	lastMessageId          MessageId         // lastMessageId: the last message id for this dialogue.
	orderedMessageIds      []MessageId       // orderedMessageIds: the ordered message ids.
	rules                  Rules             // rules: the rules for this dialogue
	terminalStateCallbacks []func(Dialogue)  // terminalStateCallbacks: the callbacks to be called when the dialogue reaches a terminal state.
}

// DialogueLabel return the dialogue label.
func (dialogue *Dialogue) DialogueLabel() DialogueLabel {
	return dialogue.dialogueLabel
}

// IncompleteDialogueLabel return the incomplete dialogue label.
func (dialogue *Dialogue) IncompleteDialogueLabel() DialogueLabel {
	return dialogue.dialogueLabel.IncompleteVersion()
}

// DialogueLabels get the dialogue labels (incomplete and complete, if it exists).
func (dialogue *Dialogue) DialogueLabels() [2]DialogueLabel {
	return [2]DialogueLabel{dialogue.dialogueLabel, dialogue.IncompleteDialogueLabel()}
}

// SelfAddress get the address of the entity for whom this dialogues is maintained.
func (dialogue *Dialogue) SelfAddress() Address {
	return dialogue.selfAddress
}

// Role get the agent's role in the dialogue.
func (dialogue *Dialogue) Role() Role {
	return dialogue.role
}

// Rules get the dialogue rules.
func (dialogue *Dialogue) Rules() Rules {
	return dialogue.rules
}

// TODO message class

// IsSelfInitiated Check whether the agent initiated the dialogue.
func (dialogue *Dialogue) IsSelfInitiated() bool {
	return dialogue.dialogueLabel.dialogueStarterAddress != dialogue.dialogueLabel.dialogueOpponentAddress
}

func (dialogue *Dialogue) LastIncomingMessage() *AbstractMessage {
	if length := len(dialogue.incomingMessages); length > 0 {
		return &dialogue.incomingMessages[length-1]
	}
	return nil
}

func (dialogue *Dialogue) LastOutgoingMessage() *AbstractMessage {
	if length := len(dialogue.outgoingMessages); length > 0 {
		return &dialogue.outgoingMessages[length-1]
	}
	return nil
}

func (dialogue *Dialogue) LastMessage() *AbstractMessage {
	// check if message id is unset
	if dialogue.lastMessageId == 0 {
		return nil
	}
	lastIncomingMessage := dialogue.LastIncomingMessage()
	if lastIncomingMessage != nil && (*lastIncomingMessage).MessageId() == dialogue.lastMessageId {
		return lastIncomingMessage
	}
	return dialogue.LastOutgoingMessage()
}

func (dialogue *Dialogue) isEmpty() bool {
	return len(dialogue.outgoingMessages) == 0 && len(dialogue.incomingMessages) == 0
}

func (dialogue *Dialogue) isMessageBySelf(message *AbstractMessage) bool {
	return (*message).Sender() == dialogue.selfAddress
}
func (dialogue *Dialogue) isMessageByOther(message *AbstractMessage) bool {
	return !dialogue.isMessageBySelf(message)
}

func (dialogue *Dialogue) counterPartyFromMessage(message *AbstractMessage) Address {
	if dialogue.isMessageBySelf(message) {
		return (*message).To()
	}
	return (*message).Sender()
}

func (dialogue *Dialogue) update(message AbstractMessage) error {
	if sender := message.Sender(); sender == "" {
		message.SetSender(dialogue.selfAddress)
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
	dialogueReference := message.DialogueReference()
	messageId := message.MessageId()
	// performative := message.performative
	if dialogueReference.dialogueStarterReference != dialogue.dialogueLabel.dialogueReference.dialogueStarterReference {
		return false, errors.New("Invalid dialogue_reference.dialogueStarterReference")
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
	dialogueReference := message.DialogueReference()
	if dialogueReference.dialogueStarterReference != dialogue.dialogueLabel.dialogueReference.dialogueStarterReference {
		return false, errors.New("Invalid dialogue_reference.dialogueStarterReference.")
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
	target := message.Target()
	// performative := message.performative

	if message.MessageId() == StartingMessageId {
		if target == StartingTarget {
			return nil
		}
		return errors.New(fmt.Sprintf("invalid target; expected 0, found %v", target))
	}

	if message.MessageId() != StartingMessageId && target == StartingTarget {
		return errors.New(
			fmt.Sprintf("invalid target, expected a non-zero integer, found %v", target),
		)
	}

	var latestIds []MessageId
	var lastIncomingMessage = dialogue.LastIncomingMessage()
	if lastIncomingMessage != nil {
		latestIds = append(latestIds, (*lastIncomingMessage).MessageId())
	}
	var lastOutgoingMessage = dialogue.LastOutgoingMessage()
	if lastOutgoingMessage != nil {
		latestIds = append(latestIds, (*lastOutgoingMessage).MessageId())
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
	if messageId > 0 && dialogue.IsSelfInitiated() {
		messages_list = dialogue.outgoingMessages
	} else {
		messages_list = dialogue.incomingMessages
	}
	if len(messages_list) == 0 {
		return nil, errors.New("Dialogue is empty.")
	}
	if MessageId(messageId) > messages_list[len(messages_list)-1].MessageId() {
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
	if message.To() != dialogue.selfAddress {
		nextMessageId = dialogue.getOutgoingNextMessageId()
	} else {
		nextMessageId = dialogue.getIncomingNextMessageId()
	}
	if message.MessageId() != nextMessageId {
		return errors.New("invalid message_id")
	}
	return nil
}

func (dialogue *Dialogue) getOutgoingNextMessageId() MessageId {
	nextMessageId := StartingMessageId
	if dialogue.LastOutgoingMessage() != nil {
		nextMessageId = dialogue.lastMessageId + 1
	}
	if dialogue.IsSelfInitiated() {
		nextMessageId = 0 - nextMessageId
	}
	return nextMessageId
}

func (dialogue *Dialogue) getIncomingNextMessageId() MessageId {
	nextMessageId := StartingMessageId
	if dialogue.LastIncomingMessage() != nil {
		nextMessageId = dialogue.lastMessageId + 1
	}
	if dialogue.IsSelfInitiated() {
		nextMessageId = 0 - nextMessageId
	}
	return nextMessageId
}

func (dialogue *Dialogue) updateIncomingAndOutgoingMessages(message AbstractMessage) {
	if dialogue.dialogueLabel.dialogueStarterAddress == dialogue.selfAddress {
		dialogue.outgoingMessages = append(dialogue.outgoingMessages, message)
	} else {
		dialogue.incomingMessages = append(dialogue.incomingMessages, message)
	}
	// update last message id
	dialogue.lastMessageId = message.MessageId()
	// append message ids in ordered manner
	dialogue.orderedMessageIds = append(dialogue.orderedMessageIds, message.MessageId())
}

func (dialogue *Dialogue) isBelongingToADialogue(message AbstractMessage) bool {
	return false
	//opponent := message.HasCounterparty()
	//var label DialogueLabel
	//if dialogue.selfAddress == dialogue.dialogueLabel.dialogueStarterAddress {
	//	label = DialogueLabel{
	//		dialogueReference:       [2]string{message.dialogueReference[0], ""},
	//		dialogueOpponentAddress: opponent,
	//		dialogueStarterAddress:  dialogue.selfAddress,
	//	}
	//} else {
	//	label = DialogueLabel{
	//		dialogueReference:       message.dialogueReference,
	//		dialogueOpponentAddress: opponent,
	//		dialogueStarterAddress:  opponent,
	//	}
	//}
	//result := validateDialogueLabelExistence(label)
	//return result
}

// func (dialogue *Dialogue) getNextMessageId() MessageId {
// 	if len(dialogue.orderedMessageIds) == 0 {
// 		return StartingMessageId
// 	}
// 	return dialogue.orderedMessageIds[len(dialogue.orderedMessageIds)-1] + 1
// }

// TODO

// store dialogues by opponent address
var dialogueStorage = make(map[Address][]Dialogue)

// store dialogue by dialogue label
var dialogueByDialogueLabel = make(map[DialogueLabel]Dialogue)

//func Create(counterParty Address,
//	selfAddress Address,
//	performative Performative,
//	content []byte) (AbstractMessage, Dialogue) {
//	initialMessage := InitializeMessage(
//		counterParty,
//		selfAddress,
//		performative,
//		content,
//		[2]string{"", ""},
//		StartingMessageId,
//		StartingTarget,
//	)
//	dialogue := createDialogue(initialMessage)
//	return initialMessage, dialogue
//}

func createDialogue(message AbstractMessage) Dialogue {
	dialogueLabel := checkReferencesAndCreateLabels(message)
	if validation := validateDialogueLabelExistence(dialogueLabel); !validation {
		dialogue := Dialogue{
			dialogueLabel:   dialogueLabel,
			dialogueMessage: message,
			selfAddress:     message.Sender(),
		}
		dialogueStorage[message.To()] = append(dialogueStorage[message.To()], dialogue)
		dialogueByDialogueLabel[dialogueLabel] = dialogue
		// update dialogue using AbstractMessage
		dialogue.updateInitialDialogue(message)
		return dialogue
	}
	return Dialogue{}
}

func (dialogue *Dialogue) updateInitialDialogue(message AbstractMessage) {
	// check if message has sender
	//if _, err := message.HasSender(); err != nil {
	//	fmt.Println(err)
	//	return
	//}
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
	dialogueReference := message.DialogueReference()
	if !(dialogueReference.dialogueStarterReference != "" && dialogueReference.dialogueResponderReference == "") {
		fmt.Println("Error : Reference address label already exists")
	}
	return DialogueLabel{
		dialogueReference:       dialogueReference,
		dialogueOpponentAddress: message.To(),
		dialogueStarterAddress:  message.Sender(),
	}
}

func validateDialogueLabelExistence(dialogueLabel DialogueLabel) bool {
	if _, ok := dialogueByDialogueLabel[dialogueLabel]; !ok {
		return false
	}
	return true
}
