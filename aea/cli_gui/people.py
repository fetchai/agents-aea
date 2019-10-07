# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2019 Fetch.AI Limited
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------
"""This is the people module and supports all the ReST actions for the PEOPLE collection."""
# System modules
from datetime import datetime

# 3rd party modules
from flask import make_response, abort


def get_timestamp():
    """Return the timestamp."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# Data to serve with our API
PEOPLE = {
    "Farrell": {
        "fname": "Doug",
        "lname": "Farrell",
        "timestamp": get_timestamp(),
    },
    "Brockman": {
        "fname": "Kent",
        "lname": "Brockman",
        "timestamp": get_timestamp(),
    },
    "Easter": {
        "fname": "Bunny",
        "lname": "Easter",
        "timestamp": get_timestamp(),
    },
}


def read_all():
    """
    Respond to a request for /api/people with the complete lists of people.

    :return:        json string of list of people
    """
    # Create the list of people from our data
    return [PEOPLE[key] for key in sorted(PEOPLE.keys())]


def read_one(lname):
    """
    Respond to a request for /api/people/{lname} with one matching person from people.

    :param lname:   last name of person to find
    :return:        person matching last name
    """
    # Does the person exist in people?
    if lname in PEOPLE:
        person = PEOPLE.get(lname)

    # otherwise, nope, not found
    else:
        abort(
            404, "Person with last name {lname} not found".format(lname=lname)
        )

    return person


def create(person):
    """
    Create a new person in the people structure based on the passed in person data.

    :param person:  person to create in people structure
    :return:        201 on success, 406 on person exists
    """
    lname = person.get("lname", None)
    fname = person.get("fname", None)

    # Does the person exist already?
    if lname not in PEOPLE and lname is not None:
        PEOPLE[lname] = {
            "lname": lname,
            "fname": fname,
            "timestamp": get_timestamp(),
        }
        return PEOPLE[lname], 201

    # Otherwise, they exist, that's an error
    else:
        abort(
            406,
            "Peron with last name {lname} already exists".format(lname=lname),
        )


def update(lname, person):
    """
    Update an existing person in the people structure.

    :param lname:   last name of person to update in the people structure
    :param person:  person to update
    :return:        updated person structure
    """
    # Does the person exist in people?
    if lname in PEOPLE:
        PEOPLE[lname]["fname"] = person.get("fname")
        PEOPLE[lname]["timestamp"] = get_timestamp()

        return PEOPLE[lname]

    # otherwise, nope, that's an error
    else:
        abort(
            404, "Person with last name {lname} not found".format(lname=lname)
        )


def delete(lname):
    """
    Delete a person from the people structure.

    :param lname:   last name of person to delete
    :return:        200 on successful delete, 404 if not found
    """
    # Does the person to delete exist?
    if lname in PEOPLE:
        del PEOPLE[lname]
        return make_response(
            "{lname} successfully deleted".format(lname=lname), 200
        )

    # Otherwise, nope, person to delete not found
    else:
        abort(
            404, "Person with last name {lname} not found".format(lname=lname)
        )
