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

import "aealite/helpers"

type DialogueMap map[DialogueLabel]*Dialogue

// Dialogue storage
type DialogueStorageInterface interface {
	IsInIncomplete(dialogueLabel DialogueLabel) bool
	SetIncompleteDialogue(
		incompleteDialogueLabel DialogueLabel,
		completeDialogueLabel DialogueLabel,
	)
	IsDialoguePresent(dialogueLabel DialogueLabel) bool
	AddDialogue(dialogue *Dialogue)
	RemoveDialogue(dialogueLabel DialogueLabel)
	GetDialogue(label DialogueLabel) *Dialogue
	GetDialoguesWithCounterparty(counterparty Address) []*Dialogue
	GetLatestLabel(dialogueLabel DialogueLabel) DialogueLabel
}

type SimpleDialogueStorage struct {
	dialogues                          *Dialogues
	dialoguesByDialogueLabel           map[DialogueLabel]*Dialogue
	dialoguesByAddress                 map[Address][]*Dialogue
	incompleteToCompleteDialogueLabels map[DialogueLabel]DialogueLabel
	terminalStateDialogueLabels        helpers.Set
}

func (dialogueStorage *SimpleDialogueStorage) IsInIncomplete(dialogueLabel DialogueLabel) bool {
	_, ok := dialogueStorage.incompleteToCompleteDialogueLabels[dialogueLabel]
	return ok
}

func (dialogueStorage *SimpleDialogueStorage) SetIncompleteDialogue(
	incompleteDialogueLabel DialogueLabel,
	completeDialogueLabel DialogueLabel,
) {
	dialogueStorage.incompleteToCompleteDialogueLabels[incompleteDialogueLabel] = completeDialogueLabel
}

func (dialogueStorage *SimpleDialogueStorage) AddDialogue(dialogue *Dialogue) {
	dialogue.AddTerminalStateCallback(dialogueStorage.dialogueTerminalStateCallback)
	dialogueStorage.dialoguesByDialogueLabel[dialogue.dialogueLabel] = dialogue

	opponent := dialogue.dialogueLabel.dialogueOpponentAddress
	dialogueList, ok := dialogueStorage.dialoguesByAddress[opponent]
	if !ok {
		dialogueList = make([]*Dialogue, 0)
		dialogueStorage.dialoguesByAddress[opponent] = dialogueList
	}
	dialogueStorage.dialoguesByAddress[opponent] = append(dialogueList, dialogue)
}

func (dialogueStorage *SimpleDialogueStorage) RemoveDialogue(dialogueLabel DialogueLabel) {
	_, ok := dialogueStorage.dialoguesByDialogueLabel[dialogueLabel]
	delete(dialogueStorage.dialoguesByDialogueLabel, dialogueLabel)
	delete(dialogueStorage.incompleteToCompleteDialogueLabels, dialogueLabel)

	dialogueStorage.terminalStateDialogueLabels.Remove(dialogueLabel)
	if ok {
		array := dialogueStorage.dialoguesByAddress[dialogueLabel.dialogueOpponentAddress]
		dialogueStorage.dialoguesByAddress[dialogueLabel.dialogueOpponentAddress] = removeDialogueFromArray(
			array,
			dialogueLabel,
		)
	}
}

func removeDialogueFromArray(array []*Dialogue, dialogueLabel DialogueLabel) []*Dialogue {
	var index int
	var dialogue *Dialogue
	for index, dialogue = range array {
		if dialogue.dialogueLabel == dialogueLabel {
			break
		}
	}
	newArray := append(array[:index], array[index+1:]...)
	return newArray
}

func (dialogueStorage *SimpleDialogueStorage) IsDialoguePresent(dialogueLabel DialogueLabel) bool {
	panic("implement me")
}

func (dialogueStorage *SimpleDialogueStorage) dialogueTerminalStateCallback(dialogue *Dialogue) {
	if dialogueStorage.dialogues.IsKeepDialoguesInTerminalStates() {
		dialogueStorage.terminalStateDialogueLabels.Add(dialogue.dialogueLabel)
	} else {
		dialogueStorage.RemoveDialogue(dialogue.dialogueLabel)
	}
}

func (dialogueStorage *SimpleDialogueStorage) GetDialoguesWithCounterparty(
	counterparty Address,
) []*Dialogue {
	result := make([]*Dialogue, 0)
	result = append(result, dialogueStorage.dialoguesByAddress[counterparty]...)
	return result
}

func (dialogueStorage *SimpleDialogueStorage) GetLatestLabel(
	dialogueLabel DialogueLabel,
) DialogueLabel {
	result, ok := dialogueStorage.incompleteToCompleteDialogueLabels[dialogueLabel]
	if !ok {
		result = dialogueLabel
	}
	return result
}

func (dialogueStorage *SimpleDialogueStorage) GetDialogue(label DialogueLabel) *Dialogue {
	return dialogueStorage.dialoguesByDialogueLabel[label]
}

func NewSimpleDialogueStorage() *SimpleDialogueStorage {
	result := SimpleDialogueStorage{
		dialoguesByDialogueLabel:           make(map[DialogueLabel]*Dialogue),
		dialoguesByAddress:                 make(map[Address][]*Dialogue),
		incompleteToCompleteDialogueLabels: make(map[DialogueLabel]DialogueLabel),
		terminalStateDialogueLabels:        helpers.NewSet(),
	}
	return &result
}
