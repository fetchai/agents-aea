#!/usr/bin/env python

import json

from collections import OrderedDict
from os.path import dirname, join as pjoin


class OperatingCompany(object):
    """
    For a description of the different codes, see:
    http://nrodwiki.rockshore.net/index.php/TOC_Codes
    """

    def __init__(self, data):
        assert isinstance(data["numeric_code"], int), (
            "OperatingCompany instantiated with non-integer numeric "
            "code: `{}`".format(data["numeric_code"])
        )

        self.name = data["name"]
        self.business_code = data["business_code"]
        self.numeric_code = data["numeric_code"]
        self.atoc_code = data["atoc_code"]

    def __str__(self):
        return self.name

    def __repr__(self):
        return 'OperatingCompany("{}")'.format(self.name)

    def serialize(self):
        return OrderedDict(
            [
                ("name", self.name),
                ("business_code", self.business_code),
                ("numeric_code", self.numeric_code),
                ("atoc_code", self.atoc_code),
            ]
        )


filename = pjoin(dirname(__file__), "operating_companies.json")

with open(filename, "r") as f:
    OPERATING_COMPANIES = [OperatingCompany(record) for record in json.load(f)]
    BUSINESS_CODE_LOOKUP = {oc.business_code: oc for oc in OPERATING_COMPANIES}
    NUMERIC_CODE_LOOKUP = {oc.numeric_code: oc for oc in OPERATING_COMPANIES}
    ATOC_CODE_LOOKUP = {oc.atoc_code: oc for oc in OPERATING_COMPANIES}


def from_business_code(business_code):
    return BUSINESS_CODE_LOOKUP[business_code]


def from_numeric_code(numeric_code):
    if not isinstance(numeric_code, int):
        raise TypeError(
            "Numeric code should be int, got {} `{}`".format(
                type(numeric_code), numeric_code
            )
        )

    return NUMERIC_CODE_LOOKUP[numeric_code]


def from_atoc_code(atoc_code):
    return ATOC_CODE_LOOKUP[atoc_code]
