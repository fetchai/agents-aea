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

package helpers

type JsonType interface{}

type StorageRecord struct {
	key   string
	value JsonType
}

type StorageInterface interface {
	Put(collectionName string, objectId string, objectBody JsonType)
	Get(collectionName string, objectId string) *JsonType
	Remove(collectionName string, objectId string)
	Find(collectionName string, objectId string, equals interface{}) []StorageRecord
	List(collectionName string) []StorageRecord
}

type SimpleStorage struct {
	container map[string]map[string]JsonType
}

func (storage *SimpleStorage) Put(collectionName string, objectId string, objectBody JsonType) {
	collection := storage.getCollectionOrSetDefault(collectionName)
	collection[objectId] = objectBody
}

func (storage SimpleStorage) Get(collectionName string, objectId string) *JsonType {
	collection := storage.getCollectionOrSetDefault(collectionName)
	obj, ok := collection[objectId]
	if !ok {
		return nil
	}
	objCopy := obj
	return &objCopy
}

func (storage *SimpleStorage) Remove(collectionName string, objectId string) {
	collection, ok := storage.container[collectionName]
	if !ok {
		// return - no collection found
		return
	}

	_, ok = collection[objectId]
	if !ok {
		// return - no object found
		return
	}
	delete(collection, objectId)
}

func (storage *SimpleStorage) Find(
	collectionName string,
	field string,
	equals JsonType,
) []StorageRecord {
	//collection, ok := storage.container[collectionName]
	//if !ok {
	//	// return - no collection found
	//	return make([]StorageRecord, 0)
	//}
	// TODO
	return make([]StorageRecord, 0)
}
func (storage *SimpleStorage) List(collectionName string) []StorageRecord {
	collection, ok := storage.container[collectionName]
	if !ok {
		// return - no collection found
		return make([]StorageRecord, 0)
	}
	result := make([]StorageRecord, len(collection))
	for key, value := range collection {
		result = append(result, StorageRecord{key, value})
	}
	return result
}

func (storage *SimpleStorage) getCollectionOrSetDefault(collectionName string) map[string]JsonType {
	var collection map[string]JsonType
	collection, ok := storage.container[collectionName]
	if !ok {
		collection = make(map[string]JsonType)
		storage.container[collectionName] = collection
	}
	return collection
}

func NewSimpleStorage() *SimpleStorage {
	var s SimpleStorage
	s.container = make(map[string]map[string]JsonType)
	return &s
}
