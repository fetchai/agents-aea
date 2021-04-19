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

type DialogueMap map[DialogueLabel]*Dialogue

type StorageInterface interface {
	Put(collectionName string, dialogue *Dialogue)
	Get(collectionName string, label DialogueLabel) *Dialogue
	Remove(collectionName string, label DialogueLabel)
	List(collectionName string) []*Dialogue
	FindByDialogueOpponentAddress(
		collectionName string,
		address Address,
	) []*Dialogue
}

type SimpleStorage struct {
	// container: collectionName -> opponentAddress -> dialogueLabel -> Dialogue
	container map[string]map[Address]DialogueMap
}

func (storage *SimpleStorage) Put(collectionName string, dialogue *Dialogue) {
	// first level - collection name
	collection, ok := storage.container[collectionName]
	if !ok {
		collection = make(map[Address]DialogueMap)
		storage.container[collectionName] = collection
	}

	// second level - opponent address
	label := dialogue.DialogueLabel()
	dialogueOpponentAddress := label.DialogueOpponentAddress()
	dialogueMap, ok := collection[dialogueOpponentAddress]
	if !ok {
		dialogueMap = make(DialogueMap, 0)
		collection[dialogueOpponentAddress] = dialogueMap
	}

	// third level - dialogue label
	dialogueMap[label] = dialogue
}

func (storage *SimpleStorage) Get(
	collectionName string,
	label DialogueLabel,
) *Dialogue {
	// first level - collection name
	collection, ok := storage.container[collectionName]
	if !ok {
		return nil
	}

	// second level - opponent address
	opponentAddress := label.DialogueOpponentAddress()
	dialogueMap, ok := collection[opponentAddress]
	if !ok {
		return nil
	}
	// third level - dialogue label
	dialogue, ok := dialogueMap[label]
	if !ok {
		return nil
	}
	return dialogue
}

func (storage *SimpleStorage) Remove(collectionName string, label DialogueLabel) {
	collection, ok := storage.container[collectionName]
	if !ok {
		// return - no collection found
		return
	}

	opponentAddress := label.DialogueOpponentAddress()
	dialogueMap, ok := collection[opponentAddress]
	if !ok {
		// return - no object found with the opponent address
		return
	}

	delete(dialogueMap, label)

	// remove empty sub-containers
	if len(dialogueMap) != 0 {
		// return - no need to change the data structure
		return
	}
	delete(collection, opponentAddress)
	if len(collection) != 0 {
		// return - no need to change the data structure
		return
	}
	delete(storage.container, collectionName)
}

func (storage *SimpleStorage) FindByDialogueOpponentAddress(
	collectionName string,
	address Address,
) []*Dialogue {
	result := make([]*Dialogue, 0)
	collection, ok := storage.container[collectionName]
	if !ok {
		// return - no collection found
		return result
	}

	dialogueMap, ok := collection[address]
	if !ok {
		// return - no dialogue found with that address
		return result
	}

	for _, value := range dialogueMap {
		result = append(result, value)
	}
	return result
}
func (storage *SimpleStorage) List(collectionName string) []*Dialogue {
	collection, ok := storage.container[collectionName]
	if !ok {
		// return - no collection found
		return make([]*Dialogue, 0)
	}
	result := make([]*Dialogue, len(collection))
	for _, mapByOpponentAddress := range collection {
		for _, dialogue := range mapByOpponentAddress {
			result = append(result, dialogue)
		}
	}
	return result
}

func NewSimpleStorage() SimpleStorage {
	var s SimpleStorage
	s.container = make(map[string]map[Address]DialogueMap)
	return s
}
