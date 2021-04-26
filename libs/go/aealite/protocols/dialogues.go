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
	"crypto/rand"
	"encoding/hex"
	"errors"
	"fmt"
	"log"
)

const (
	IncompleteDialogues     = "incomplete_dialogues"
	TerminalDialoguesSuffix = "_terminal"
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

func newSelfInitiatedDialogueReference() DialogueReference {
	return DialogueReference{generateDialogueNonce(), UnassignedDialogueReference}
}

type Dialogues struct {
	selfAddress                Address
	endStates                  helpers.Set
	roleFromFirstMessage       func(ProtocolMessageInterface, Address) Role
	keepTerminalStateDialogues bool

	dialogueName    string
	dialogueStorage DialogueStorageInterface

	initialPerformatives  []Performative
	terminalPerformatives []Performative
	validReplies          map[Performative][]Performative
}

func (dialogues *Dialogues) IsKeepDialoguesInTerminalStates() bool {
	return dialogues.keepTerminalStateDialogues
}

func (dialogues *Dialogues) SelfAddress() (Address, error) {
	if dialogues.selfAddress == "" {
		return "", errors.New("'self address' is not set")
	}
	return dialogues.selfAddress, nil
}

func (dialogues *Dialogues) GetDialoguesWithCounterparty(counterparty Address) []*Dialogue {
	return dialogues.dialogueStorage.GetDialoguesWithCounterparty(counterparty)
}

func (dialogues *Dialogues) isMessageBySelf(message ProtocolMessageInterface) bool {
	return message.Sender() == dialogues.selfAddress
}

func (dialogues *Dialogues) isMessageByOther(message ProtocolMessageInterface) bool {
	return !dialogues.isMessageBySelf(message)
}

func (dialogues *Dialogues) counterpartyFromMessage(message ProtocolMessageInterface) Address {
	if dialogues.isMessageBySelf(message) {
		return message.To()
	}
	return message.Sender()
}

func (dialogues *Dialogues) Create(
	counterparty Address,
	performative Performative,
	body map[string]interface{},
) (ProtocolMessageInterface, *Dialogue, error) {
	dialogueReference := newSelfInitiatedDialogueReference()
	initialMessage := DialogueMessageWrapper{
		dialogueReference: dialogueReference,
		messageId:         StartingMessageId,
		target:            StartingTarget,
		performative:      performative,
	}
	// safe to ignore errors as the message was just created
	_ = initialMessage.SetSender(dialogues.selfAddress)
	_ = initialMessage.SetTo(counterparty)

	dialogue, err := dialogues.createDialogue(counterparty, &initialMessage)
	if err != nil {
		return nil, nil, err
	}
	return &initialMessage, dialogue, nil
}

func (dialogues *Dialogues) CreateWithMessage(
	counterparty Address,
	initialMessage ProtocolMessageInterface,
) (*Dialogue, error) {
	err := initialMessage.SetSender(dialogues.selfAddress)
	if err != nil {
		return nil, err
	}
	err = initialMessage.SetTo(counterparty)
	if err != nil {
		return nil, err
	}
	return dialogues.createDialogue(counterparty, initialMessage)
}

func (dialogues *Dialogues) createDialogue(
	counterparty Address,
	initialMessage ProtocolMessageInterface,
) (*Dialogue, error) {
	dialogue, err := dialogues.createSelfInitiated(counterparty,
		initialMessage.DialogueReference(),
		dialogues.roleFromFirstMessage(initialMessage, dialogues.selfAddress))
	if err != nil {
		return nil, err
	}
	err = dialogue.update(initialMessage)
	if err != nil {
		// if update fails, we don't propagate the error.
		return nil, nil
	}
	return dialogue, nil
}

func (dialogues *Dialogues) Update(message ProtocolMessageInterface) (*Dialogue, error) {
	if !(message.HasSender() && dialogues.isMessageByOther(message)) {
		return nil, errors.New(
			"invalid update: this method must only be used with a message by another agent",
		)
	}
	if !message.HasTo() {
		return nil, errors.New("the message's 'to' field is not set")
	}
	if message.To() != dialogues.selfAddress {
		return nil, fmt.Errorf(
			"message 'to' and dialogue 'self address' do not match: got 'to=%s' expected 'to=%s'",
			message.To(),
			dialogues.selfAddress,
		)
	}

	dialogueReference := message.DialogueReference()
	starterRefAssigned := dialogueReference.dialogueStarterReference != UnassignedDialogueReference
	responderRefAssigned := dialogueReference.dialogueResponderReference != UnassignedDialogueReference
	isStartingMsgId := message.MessageId() == StartingMessageId
	isStartingTarget := message.MessageId() == StartingTarget
	isInvalidLabel := !starterRefAssigned && responderRefAssigned
	isNewDialogue := starterRefAssigned && !responderRefAssigned && isStartingMsgId
	isIncompleteLabelAndNotInitialMsg := starterRefAssigned && !responderRefAssigned && !isStartingMsgId &&
		!isStartingTarget

	//log.Printf("dialogueReference:  %s", message.DialogueReference())
	//log.Printf("starterRefAssigned:  %s", starterRefAssigned, dialogueReference.dialogueStarterReference, UnassignedDialogueReference)
	//log.Printf("responderRefAssigned:  %s", responderRefAssigned, dialogueReference.dialogueResponderReference, UnassignedDialogueReference)
	//log.Printf("isStartingMsgId:  %s", isStartingMsgId, message.MessageId(), StartingMessageId)
	//log.Printf("isStartingTarget:  %s", isStartingTarget,message.MessageId(), StartingTarget)
	//log.Printf("isInvalidLabel:  %s", isInvalidLabel, starterRefAssigned, responderRefAssigned)
	//log.Printf("isNewDialogue:  %s", isNewDialogue,starterRefAssigned,responderRefAssigned,isStartingMsgId)
	//log.Printf("isIncompleteLabelAndNotInitialMsg:  %s", isIncompleteLabelAndNotInitialMsg, starterRefAssigned,responderRefAssigned,isStartingMsgId, isStartingTarget)

	var dialogue *Dialogue
	var err error
	if isInvalidLabel {
		log.Print("invalid label")
		dialogue = nil
	} else if isNewDialogue {
		log.Print("Go new dialogue")
		dialogue, err = dialogues.createOpponentInitiated(message.Sender(), dialogueReference, dialogues.roleFromFirstMessage(message, dialogues.selfAddress))
		if err != nil {
			// propagate the error
			log.Print("2")
			return nil, err
		}
	} else if isIncompleteLabelAndNotInitialMsg {
		// we can allow a dialogue to have incomplete reference
		// as multiple messages can be sent before one is received with complete reference
		dialogue = dialogues.GetDialogue(message)
	} else {
		err = dialogues.completeDialogueReference(message)
		if err != nil {
			log.Print("3")
			return nil, err
		}
		dialogue = dialogues.GetDialogue(message)
	}

	if dialogue != nil {
		err := dialogue.update(message)

		if err != nil {
			// invalid message for the dialogue found
			if isNewDialogue {
				// remove the newly created dialogue if the initial message is invalid
				dialogues.dialogueStorage.RemoveDialogue(dialogue.dialogueLabel)
			}
			log.Printf("fail to update!!! %s", err)
			dialogue = nil
			return dialogue, err
		}
		log.Print("ok ret dialogue!!!")
		return dialogue, nil
	}
	// couldn't find the dialogue referenced by the message
	log.Print("default one?")
	return nil, nil

}

func (dialogues *Dialogues) completeDialogueReference(message ProtocolMessageInterface) error {
	completeDialogueReference := message.DialogueReference()
	starterRef := completeDialogueReference.dialogueStarterReference
	responderRef := completeDialogueReference.dialogueResponderReference
	if !(starterRef != UnassignedDialogueReference && responderRef != UnassignedDialogueReference) {
		return errors.New("only complete dialogue references allowed")
	}
	incompleteDialogueReference := DialogueReference{
		starterRef,
		UnassignedDialogueReference,
	}
	incompleteDialogueLabel := DialogueLabel{
		incompleteDialogueReference,
		message.Sender(),
		dialogues.selfAddress,
	}

	if dialogues.dialogueStorage.IsDialoguePresent(incompleteDialogueLabel) &&
		!(dialogues.dialogueStorage.IsInIncomplete(incompleteDialogueLabel)) {
		dialogue := dialogues.dialogueStorage.GetDialogue(incompleteDialogueLabel)
		if dialogue == nil {
			return errors.New("dialogue not found")
		}
		dialogues.dialogueStorage.RemoveDialogue(incompleteDialogueLabel)
		finalDialogueLabel := DialogueLabel{
			completeDialogueReference,
			incompleteDialogueLabel.dialogueOpponentAddress,
			incompleteDialogueLabel.dialogueStarterAddress,
		}
		err := dialogue.updateDialogueLabel(finalDialogueLabel)
		if err != nil {
			// propagate error
			return err
		}
		dialogues.dialogueStorage.AddDialogue(dialogue)
		dialogues.dialogueStorage.SetIncompleteDialogue(incompleteDialogueLabel, finalDialogueLabel)
	}

	return nil
}

func (dialogues *Dialogues) GetDialogue(message ProtocolMessageInterface) *Dialogue {
	counterpartyFromMessage := dialogues.counterpartyFromMessage(message)
	dialogueReference := message.DialogueReference()

	selfInitiatedDialogueLabel := DialogueLabel{
		dialogueReference,
		counterpartyFromMessage,
		dialogues.selfAddress,
	}
	otherInitiatedDialogueLabel := DialogueLabel{
		dialogueReference,
		counterpartyFromMessage,
		counterpartyFromMessage,
	}

	selfInitiatedDialogueLabel = dialogues.getLatestLabel(selfInitiatedDialogueLabel)
	otherInitiatedDialogueLabel = dialogues.getLatestLabel(otherInitiatedDialogueLabel)

	selfInitiatedDialogue := dialogues.GetDialogueFromLabel(selfInitiatedDialogueLabel)
	otherInitiatedDialogue := dialogues.GetDialogueFromLabel(otherInitiatedDialogueLabel)
	if selfInitiatedDialogue != nil {
		return selfInitiatedDialogue
	}
	return otherInitiatedDialogue

}

func (dialogues *Dialogues) getLatestLabel(label DialogueLabel) DialogueLabel {
	return dialogues.dialogueStorage.GetLatestLabel(label)
}

func (dialogues *Dialogues) GetDialogueFromLabel(label DialogueLabel) *Dialogue {
	return dialogues.dialogueStorage.GetDialogue(label)
}

func (dialogues *Dialogues) createSelfInitiated(
	dialogueOpponentAddress Address,
	dialogueReference DialogueReference,
	role Role,
) (*Dialogue, error) {
	starterRef := dialogueReference.DialogueStarterReference()
	responderRef := dialogueReference.DialogueResponderReference()
	if !(starterRef != UnassignedDialogueReference && responderRef == UnassignedDialogueReference) {
		return nil, errors.New(
			"cannot initiate dialogue with preassigned dialogue_responder_reference",
		)
	}
	incompleteDialogueLabel := DialogueLabel{
		dialogueReference:       dialogueReference,
		dialogueOpponentAddress: dialogueOpponentAddress,
		dialogueStarterAddress:  dialogues.selfAddress,
	}
	dialogue, err := dialogues.create(incompleteDialogueLabel, role, nil)
	if err != nil {
		return nil, err
	}
	return dialogue, nil
}

func (dialogues *Dialogues) createOpponentInitiated(dialogueOpponentAddress Address,
	dialogueReference DialogueReference,
	role Role,
) (*Dialogue, error) {
	starterRef := dialogueReference.DialogueStarterReference()
	responderRef := dialogueReference.DialogueResponderReference()
	if !(starterRef != UnassignedDialogueReference && responderRef == UnassignedDialogueReference) {
		return nil, errors.New(
			"cannot initiate dialogue with preassigned dialogue_responder_reference",
		)
	}
	incompleteDialogueLabel := DialogueLabel{
		dialogueReference,
		dialogueOpponentAddress,
		dialogueOpponentAddress,
	}
	newDialogueReference := DialogueReference{
		dialogueReference.dialogueStarterReference,
		generateDialogueNonce(),
	}
	completeDialogueLabel := DialogueLabel{
		newDialogueReference,
		dialogueOpponentAddress,
		dialogueOpponentAddress,
	}
	dialogue, err := dialogues.create(incompleteDialogueLabel, role, &completeDialogueLabel)
	if err != nil {
		return nil, err
	}
	return dialogue, nil
}

func (dialogues *Dialogues) create(
	incompleteDialogueLabel DialogueLabel,
	role Role,
	completeDialogueLabel *DialogueLabel,
) (*Dialogue, error) {
	var dialogueLabel DialogueLabel
	if dialogues.dialogueStorage.IsInIncomplete(incompleteDialogueLabel) {
		return nil, errors.New("incomplete dialogue label already present")
	}
	if completeDialogueLabel == nil {
		dialogueLabel = incompleteDialogueLabel
	} else {
		copyLabel := *completeDialogueLabel
		dialogues.dialogueStorage.SetIncompleteDialogue(incompleteDialogueLabel, copyLabel)
	}
	if dialogues.dialogueStorage.IsDialoguePresent(dialogueLabel) {
		return nil, errors.New("dialogue label already present in dialogues")
	}
	dialogue := NewDialogue(
		dialogueLabel,
		dialogues.selfAddress,
		role,
		dialogues.initialPerformatives,
		dialogues.terminalPerformatives,
		dialogues.validReplies,
	)
	dialogues.dialogueStorage.AddDialogue(&dialogue)
	return &dialogue, nil
}

func NewDialogues(
	selfAddress Address,
	roleFromFirstMessage func(ProtocolMessageInterface, Address) Role,
	keepTerminalStateDialogues bool,
	dialogueName string,

	initialPerformatives []Performative,
	terminalPerformatives []Performative,
	validReplies map[Performative][]Performative) *Dialogues {

	endStatesSet := helpers.NewSet()

	for _, endState := range terminalPerformatives {
		endStatesSet.Add(endState)
	}

	dialogues := Dialogues{
		selfAddress:                selfAddress,
		endStates:                  endStatesSet,
		roleFromFirstMessage:       roleFromFirstMessage,
		keepTerminalStateDialogues: keepTerminalStateDialogues,
		dialogueName:               dialogueName,
		initialPerformatives:       initialPerformatives,
		terminalPerformatives:      terminalPerformatives,
		validReplies:               validReplies,
	}
	storage := NewSimpleDialogueStorage()
	dialogues.dialogueStorage = storage

	return &dialogues
}
