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
	"aealite/helpers"
	"errors"
	"fmt"
)

type Role string
type EndStates string

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

func max(list []MessageId) MessageId {
	max := list[0]
	for i := 1; i < len(list); i++ {
		if max < list[i] {
			max = list[i]
		}
	}
	return max
}

func abs(id MessageId) MessageId {
	if id < 0 {
		return -id
	}
	return id
}

/* Definition of main data types */

type Rules struct {
	initialPerformatives  helpers.Set
	terminalPerformatives helpers.Set
	validReplies          map[Performative]helpers.Set
}

type DialogueInterface interface {
	// getters

	DialogueLabel() DialogueLabel
	IncompleteDialogueLabel() DialogueLabel
	DialogueLabels() [2]DialogueLabel
	SelfAddress() Address
	Role() Role
	Rules() Rules
	getMessageClass() *ProtocolMessageInterface
	IsSelfInitiated() bool
	LastIncomingMessage() *ProtocolMessageInterface
	LastOutgoingMessage() *ProtocolMessageInterface
	LastMessage() *ProtocolMessageInterface
	IsEmpty() bool
	Reply(
		Performative,
		ProtocolMessageInterface,
		*MessageId,
		map[string]interface{},
	) (ProtocolMessageInterface, error)
	String() string

	counterPartyFromMessage(*ProtocolMessageInterface) Address
	isMessageBySelf(*ProtocolMessageInterface) bool
	isMessageByOther(*ProtocolMessageInterface) bool
	hasMessageId(MessageId) bool
	update(*ProtocolMessageInterface)
	isBelongingToDialogue(*ProtocolMessageInterface) bool
	validateNextMessage(*ProtocolMessageInterface) error
	basicValidations(*ProtocolMessageInterface) error
	basicValidationInitialMessage(*ProtocolMessageInterface) error
	basicValidationNonInitialMessage(*ProtocolMessageInterface) error
	validateMessageTarget(*ProtocolMessageInterface) string
	validateMessageId(*ProtocolMessageInterface) string
	getMessageById(MessageId) *ProtocolMessageInterface
	getOutgoingNextMessageId() MessageId
	getIncomingNextMessageId() MessageId
	updateDialogueLabel(DialogueLabel) error
	customValidation(*ProtocolMessageInterface) error
}

/* Dialogue definition and methods */

type Dialogue struct {
	dialogueLabel          DialogueLabel              // dialogueLabel: the dialogue label for this dialogue
	role                   Role                       // role: the role of the agent this dialogue is maintained for
	selfAddress            Address                    // selfAddress: the address of the entity for whom this dialogue is maintained
	outgoingMessages       []ProtocolMessageInterface // outgoingMessages: list of outgoing messages
	incomingMessages       []ProtocolMessageInterface // incomingMessages: list of incoming messages
	lastMessageId          MessageId                  // lastMessageId: the last message id for this dialogue.
	orderedMessageIds      []MessageId                // orderedMessageIds: the ordered message ids.
	rules                  Rules                      // rules: the rules for this dialogue
	terminalStateCallbacks []func(*Dialogue)          // terminalStateCallbacks: the callbacks to be called when the dialogue reaches a terminal state.
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

func (dialogue *Dialogue) AddTerminalStateCallback(fn func(*Dialogue)) {
	dialogue.terminalStateCallbacks = append(dialogue.terminalStateCallbacks, fn)
}

// IsSelfInitiated Check whether the agent initiated the dialogue.
func (dialogue *Dialogue) IsSelfInitiated() bool {
	return dialogue.dialogueLabel.dialogueStarterAddress != dialogue.dialogueLabel.dialogueOpponentAddress
}

func (dialogue *Dialogue) LastIncomingMessage() ProtocolMessageInterface {
	if length := len(dialogue.incomingMessages); length > 0 {
		return dialogue.incomingMessages[length-1]
	}
	return nil
}

func (dialogue *Dialogue) LastOutgoingMessage() ProtocolMessageInterface {
	if length := len(dialogue.outgoingMessages); length > 0 {
		return dialogue.outgoingMessages[length-1]
	}
	return nil
}

func (dialogue *Dialogue) LastMessage() ProtocolMessageInterface {
	// check if message id is unset
	if dialogue.lastMessageId == 0 {
		return nil
	}
	lastIncomingMessage := dialogue.LastIncomingMessage()
	if lastIncomingMessage != nil && lastIncomingMessage.MessageId() == dialogue.lastMessageId {
		return lastIncomingMessage
	}
	return dialogue.LastOutgoingMessage()
}

func (dialogue *Dialogue) isEmpty() bool {
	return len(dialogue.outgoingMessages) == 0 && len(dialogue.incomingMessages) == 0
}

func (dialogue *Dialogue) counterPartyFromMessage(message ProtocolMessageInterface) Address {
	if dialogue.isMessageBySelf(message) {
		return message.To()
	}
	return message.Sender()
}

func (dialogue *Dialogue) isMessageBySelf(message ProtocolMessageInterface) bool {
	return message.Sender() == dialogue.selfAddress
}

func (dialogue *Dialogue) hasMessageId(messageId MessageId) bool {
	return dialogue.getMessageById(messageId) != nil
}

func (dialogue *Dialogue) update(message ProtocolMessageInterface) error {
	if !(message).HasSender() {
		// the error is safe to ignore thanks to the above check
		_ = (message).SetSender(dialogue.selfAddress)
	}
	isBelongingToDialogue := dialogue.isBelongingToDialogue(message)
	if !isBelongingToDialogue {
		return errors.New("message does not belong to this dialogue")
	}
	if err := dialogue.validateNextMessage(message); err != nil {
		return err
	}

	if dialogue.isMessageBySelf(message) {
		dialogue.outgoingMessages = append(dialogue.outgoingMessages, message)
	} else {
		dialogue.incomingMessages = append(dialogue.incomingMessages, message)
	}
	// update last message id
	dialogue.lastMessageId = message.MessageId()
	// append message ids in ordered manner
	dialogue.orderedMessageIds = append(dialogue.orderedMessageIds, message.MessageId())

	performative := message.Performative()
	if dialogue.rules.terminalPerformatives.Contains(performative) {
		for _, fn := range dialogue.terminalStateCallbacks {
			fn(dialogue)
		}
	}
	return nil
}

func (dialogue *Dialogue) isBelongingToDialogue(message ProtocolMessageInterface) bool {
	opponent := dialogue.counterPartyFromMessage(message)
	var label DialogueLabel
	if dialogue.IsSelfInitiated() {
		label = DialogueLabel{
			dialogueReference: DialogueReference{
				message.DialogueReference().dialogueStarterReference,
				UnassignedDialogueReference,
			},
			dialogueOpponentAddress: opponent,
			dialogueStarterAddress:  dialogue.selfAddress,
		}
	} else {
		label = DialogueLabel{
			dialogueReference:       message.DialogueReference(),
			dialogueOpponentAddress: opponent,
			dialogueStarterAddress:  opponent,
		}
	}
	result := dialogue.checkLabelBelongsToDialogue(label)
	return result
}

func (dialogue *Dialogue) Reply(
	performative Performative,
	targetMessage ProtocolMessageInterface,
	targetPtr *MessageId,
	body map[string]interface{},
) (ProtocolMessageInterface, error) {
	lastMessage := dialogue.LastMessage()
	if lastMessage == nil {
		return nil, errors.New("cannot reply in an empty dialogue")
	}
	var target MessageId
	msgIsNone := targetMessage == nil
	targetIsNone := targetPtr == nil

	if msgIsNone && !targetIsNone {
		target = *targetPtr
		targetMessage = dialogue.getMessageById(*targetPtr)
	} else if msgIsNone && targetIsNone {
		targetMessage = lastMessage
		target = lastMessage.MessageId()
	} else if !msgIsNone && targetIsNone {
		target = targetMessage.MessageId()
	} else if !msgIsNone && !targetIsNone {
		target = *targetPtr
		if target != targetMessage.MessageId() {
			return nil, errors.New("the provided target and target_message do not match")
		}
	}

	if targetMessage == nil {
		return nil, errors.New("no target message found")
	}

	if dialogue.hasMessageId(target) {
		return nil, errors.New("the target message does not exist in this dialogue")
	}

	reply := DialogueMessageWrapper{
		dialogueReference: dialogue.dialogueLabel.dialogueReference,
		messageId:         dialogue.getOutgoingNextMessageId(),
		sender:            dialogue.selfAddress,
		to:                dialogue.dialogueLabel.dialogueOpponentAddress,
		target:            target,
		performative:      performative,
		body:              body,
	}

	err := dialogue.update(&reply)
	if err != nil {
		return nil, err
	}
	return &reply, nil
}

func (dialogue *Dialogue) validateNextMessage(message ProtocolMessageInterface) error {
	err := dialogue.basicValidation(message)
	if err != nil {
		return err
	}
	// check if custom validation

	return nil
}

func (dialogue *Dialogue) checkLabelBelongsToDialogue(label DialogueLabel) bool {
	return label == dialogue.dialogueLabel || label == dialogue.dialogueLabel.IncompleteVersion()
}

func (dialogue *Dialogue) basicValidation(message ProtocolMessageInterface) error {
	if dialogue.isEmpty() {
		return dialogue.basicValidationInitialMessage(message)
	}
	return dialogue.basicValidationNonInitialMessage(message)
}

func (dialogue *Dialogue) basicValidationInitialMessage(
	message ProtocolMessageInterface,
) error {
	dialogueReference := message.DialogueReference()
	messageId := message.MessageId()
	performative := message.Performative()
	expectedReference := dialogue.dialogueLabel.dialogueReference.dialogueStarterReference
	actualReference := dialogueReference.dialogueStarterReference
	if expectedReference != actualReference {
		return fmt.Errorf(
			"invalid dialogue_reference.dialogueStarterReference: expected %s, found %s",
			expectedReference,
			actualReference,
		)
	}
	if messageId != StartingMessageId {
		return fmt.Errorf("invalid message id: expected %v, found %v", StartingMessageId, messageId)
	}

	err := dialogue.validateMessageTarget(message)
	if err != nil {
		return err
	}

	//check if performative exists in initial performatives
	if !dialogue.rules.initialPerformatives.Contains(performative) {
		return errors.New("invalid initial performative")
	}
	// The initial message passes basic validation -> no errors
	return nil
}

func (dialogue *Dialogue) basicValidationNonInitialMessage(
	message ProtocolMessageInterface,
) error {
	dialogueReference := message.DialogueReference()
	expectedReference := dialogue.dialogueLabel.dialogueReference.dialogueStarterReference
	actualReference := dialogueReference.dialogueStarterReference
	if expectedReference != actualReference {
		return fmt.Errorf(
			"invalid dialogue_reference.dialogueStarterReference: expected %s, found %s",
			expectedReference,
			actualReference,
		)
	}
	err := dialogue.validateMessageId(message)
	if err != nil {
		return err
	}
	err = dialogue.validateMessageTarget(message)
	if err != nil {
		return err
	}
	// The non-initial message passes basic validation.
	return nil
}

func (dialogue *Dialogue) validateMessageTarget(message ProtocolMessageInterface) error {
	target := message.Target()
	performative := message.Performative()

	if message.MessageId() == StartingMessageId {
		if target == StartingTarget {
			return nil
		}
		return fmt.Errorf("invalid target: expected 0, found %v", target)
	}

	if message.MessageId() != StartingMessageId && target == StartingTarget {
		return fmt.Errorf("invalid target: expected a non-zero integer, found %v", target)
	}

	var latestIds []MessageId
	var lastIncomingMessage = dialogue.LastIncomingMessage()
	if lastIncomingMessage != nil {
		latestIds = append(latestIds, abs(lastIncomingMessage.MessageId()))
	}
	var lastOutgoingMessage = dialogue.LastOutgoingMessage()
	if lastOutgoingMessage != nil {
		latestIds = append(latestIds, abs(lastOutgoingMessage.MessageId()))
	}

	if absoluteTarget, maxLatestIds := abs(target), max(latestIds); absoluteTarget > maxLatestIds {
		return fmt.Errorf("invalid target: expected a value less than or equal to %v. Found %v",
			maxLatestIds, absoluteTarget)
	}

	targetMessage := dialogue.getMessageById(target)
	if targetMessage == nil {
		return fmt.Errorf("invalid target %v: target message can not be found.", target)
	}
	targetPerformative := targetMessage.Performative()

	// check performatives
	setValidReplies := dialogue.rules.validReplies[targetPerformative]
	if setValidReplies.Contains(performative) {
		return fmt.Errorf("invalid performative: '%s' is not a valid reply", performative)
	}
	return nil
}

func (dialogue *Dialogue) validateMessageId(message ProtocolMessageInterface) error {
	var nextMessageId MessageId
	isOutgoing := message.To() != dialogue.selfAddress
	if isOutgoing {
		nextMessageId = dialogue.getOutgoingNextMessageId()
	} else {
		nextMessageId = dialogue.getIncomingNextMessageId()
	}
	if actual := message.MessageId(); actual != nextMessageId {
		return fmt.Errorf("invalid message id: expected %v, found %v",
			nextMessageId, actual)
	}
	return nil
}

func (dialogue *Dialogue) getMessageById(messageId MessageId) ProtocolMessageInterface {
	if dialogue.isEmpty() {
		return nil
	}
	if messageId == 0 {
		// message id == 0 is invalid
		return nil
	}
	var messagesList []ProtocolMessageInterface
	if (messageId > 0) == dialogue.IsSelfInitiated() {
		messagesList = dialogue.outgoingMessages
	} else {
		messagesList = dialogue.incomingMessages
	}
	if len(messagesList) == 0 {
		return nil
	}
	absoluteMessageId := abs(messageId)
	absoluteLastMessageId := abs(messagesList[len(messagesList)-1].MessageId())
	if absoluteMessageId > absoluteLastMessageId {
		return nil
	}
	return messagesList[absoluteMessageId-1]
}

func (dialogue *Dialogue) getOutgoingNextMessageId() MessageId {
	nextMessageId := StartingMessageId
	if dialogue.LastOutgoingMessage() != nil {
		nextMessageId = abs(dialogue.lastMessageId) + 1
	}
	if !dialogue.IsSelfInitiated() {
		nextMessageId = 0 - nextMessageId
	}
	return nextMessageId
}

func (dialogue *Dialogue) getIncomingNextMessageId() MessageId {
	nextMessageId := StartingMessageId
	if dialogue.LastIncomingMessage() != nil {
		nextMessageId = abs(dialogue.lastMessageId) + 1
	}
	if dialogue.IsSelfInitiated() {
		nextMessageId = 0 - nextMessageId
	}
	return nextMessageId
}

func (dialogue *Dialogue) updateDialogueLabel(finalDialogueLabel DialogueLabel) error {
	if dialogue.dialogueLabel.DialogueResponderReference() == UnassignedDialogueReference &&
		finalDialogueLabel.DialogueResponderReference() == UnassignedDialogueReference {
		return errors.New("dialogue label cannot be updated")
	}
	dialogue.dialogueLabel = finalDialogueLabel
	return nil
}
