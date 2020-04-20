#!/usr/bin/env python

import json

from collections import OrderedDict
from os.path import dirname, join as pjoin


class Location(object):
    """
    Reference data:
    http://nrodwiki.rockshore.net/index.php/Reference_Data
    """

    def __init__(self, data):
        """
        ```
        {
            "TIPLOC": "KETR",
            "UIC": "18570",
            "NLCDESC16": " ",
            "STANOX": "61009",
            "NLC": "185700",
            "3ALPHA": "KET",
            "NLCDESC": "KETTERING"
        },

        ```
        """

        self.raw = data

    @property
    def name(self):
        """
        http://nrodwiki.rockshore.net/index.php/NLC
        """
        return self.raw["NLCDESC"]

    @property
    def tiploc_code(self):
        """
        http://nrodwiki.rockshore.net/index.php/TIPLOC
        """
        return self._strip(self.raw["TIPLOC"])

    @property
    def timing_point_location(self):
        return self._strip(self.tiploc)

    @property
    def uic_code(self):
        return self._strip(self.raw["UIC"])

    @property
    def national_location_code(self):
        """
        http://nrodwiki.rockshore.net/index.php/NLC
        """
        return self._strip(self.raw["NLC"])

    @property
    def stanox_code(self):
        return self._strip(self.raw["STANOX"])

    @property
    def three_alpha(self):
        """
        A 3-character code used for stations. Previously referred to as CRS
        (Computer Reservation System) or NRS (National Reservation System)
        codes.
        eg: 'KET' (Kettering)
        """
        return self._strip(self.raw["3ALPHA"])

    @property
    def crs_code(self):
        return self.three_alpha

    def __str__(self):
        return self.name

    def __repr__(self):
        return 'Location("{}")'.format(self.name)

    def serialize(self):
        return OrderedDict(
            [
                ("name", self.name),
                ("stanox_code", self.stanox_code),
                ("three_alpha", self.three_alpha),
            ]
        )

    @staticmethod
    def _strip(string):
        string = string.strip()
        return string if string != "" else None


filename = pjoin(dirname(__file__), "CORPUSExtract.json")

with open(filename, "r") as f:

    def filter_empty_stanox(record):
        return record["STANOX"].strip() != ""

    LOCATIONS = [
        Location(record)
        for record in filter(filter_empty_stanox, json.load(f)["TIPLOCDATA"])
    ]
    # STANOX_LOOKUP = {loc.stanox_code: loc for loc in LOCATIONS}
    STANOX_LOOKUP = {}
    for loc in LOCATIONS:
        if len(loc.stanox_code) == 4:
            stanox = "0" + loc.stanox_code
            STANOX_LOOKUP.update({stanox: loc})
        else:
            STANOX_LOOKUP.update({loc.stanox_code: loc})

def from_stanox(stanox):
    try:
        lookup_stanox = STANOX_LOOKUP[stanox]
    except KeyError:
        lookup_stanox = ""
    #     data = {
    #         "TIPLOC": "UNKNOWN",
    #         "UIC": "00000",
    #         "NLCDESC16": " ",
    #         "STANOX": "00000",
    #         "NLC": "00000",
    #         "3ALPHA": "",
    #         "NLCDESC": "UNKNOWN"
    #     }
    #     lookup_stanox = Location(data)
    #     import pdb; pdb.set_trace()
    return lookup_stanox
