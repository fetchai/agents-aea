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
	message                    *ProtocolMessageInterface // type
	dialogue                   *Dialogue                 // type
	roleFromFirstMessage       func(*ProtocolMessageInterface, Address) Role
	keepTerminalStateDialogues bool

	dialogueName    string
	dialogueStorage DialogueStorageInterface
}

func (dialogues *Dialogues) IsKeepDialoguesInTerminalStates() bool {
	return dialogues.keepTerminalStateDialogues
}

func (dialogues *Dialogues) SelfAddress() Address {
	return dialogues.selfAddress
}

func (dialogues *Dialogues) Message() *ProtocolMessageInterface {
	return dialogues.message
}

func (dialogues *Dialogues) Dialogue() *Dialogue {
	return dialogues.dialogue
}

func (dialogues *Dialogues) Create(
	counterparty Address,
	performative Performative,
	body map[string]interface{},
) (ProtocolMessageInterface, *Dialogue) {
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
	return &initialMessage, nil
}

func (dialogues *Dialogues) createDialogue(
	incompleteDialogueLabel DialogueLabel,
	role Role,
	completeDialogueLabel *DialogueLabel,
) *Dialogue {
	var dialogueLabel DialogueLabel
	// TODO if true, stop here
	dialogues.dialogueStorage.IsInIncomplete(incompleteDialogueLabel)
	if completeDialogueLabel == nil {
		dialogueLabel = incompleteDialogueLabel
	} else {
		dialogues.dialogueStorage.SetIncompleteDialogueLabel(incompleteDialogueLabel, *completeDialogueLabel)
	}
	// TODO if true, stop here
	dialogues.dialogueStorage.IsDialoguePresent(dialogueLabel)
	dialogue := Dialogue{
		dialogueLabel: dialogueLabel,
		selfAddress:   dialogues.selfAddress,
		role:          role,
	}
	dialogues.dialogueStorage.AddDialogue(&dialogue)
	return &dialogue
}

func (dialogues *Dialogues) createSelfInitiated(
	dialogueOpponentAddress Address,
	dialogueReference DialogueReference,
	role Role,
) *Dialogue {
	incompleteDialogueLabel := DialogueLabel{
		dialogueReference:       dialogueReference,
		dialogueOpponentAddress: dialogueOpponentAddress,
		dialogueStarterAddress:  dialogues.selfAddress,
	}
	dialogue := dialogues.createDialogue(incompleteDialogueLabel, role, nil)
	return dialogue
}

//func (dialogues *Dialogues) GetDialoguesByOpponentAddress(counterparty Address) []*Dialogue {
//	result, ok := dialogues.dialoguesByAddress[counterparty]
//	if !ok {
//		return make([]*Dialogue, 0)
//	}
//	return result
//}

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

func (dialogues *Dialogues) GetDialoguesWithCounterparty(counterparty Address) []*Dialogue {
	return dialogues.dialogueStorage.GetDialoguesWithCounterparty(counterparty)
}

func NewDialogues(
	selfAddress Address,
	endStates helpers.Set,
	message *ProtocolMessageInterface,
	dialogue *Dialogue,
	roleFromFirstMessage func(*ProtocolMessageInterface, Address) Role,
	keepTerminalStateDialogues bool,
	dialogueName string,
) *Dialogues {
	dialogues := Dialogues{
		selfAddress:                selfAddress,
		endStates:                  endStates,
		message:                    message,
		dialogue:                   dialogue,
		roleFromFirstMessage:       roleFromFirstMessage,
		keepTerminalStateDialogues: keepTerminalStateDialogues,
		dialogueName:               dialogueName,
	}
	storage := NewSimpleDialogueStorage()
	dialogues.dialogueStorage = storage

	return &dialogues
}
