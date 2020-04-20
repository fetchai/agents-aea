import datetime

from packages.aris.protocols.rail_stomp.locations import from_stanox

from packages.aris.protocols.rail_stomp.operating_companies import from_numeric_code


class Helper:
    @staticmethod
    def decode_boolean(string):
        if string == "true":
            return True
        elif string == "false":
            return False
        raise ValueError("Invalid boolean: `{}`".format(string))

    @staticmethod
    def decode_stanox(stanox):
        return from_stanox(stanox)

    @staticmethod
    def decode_operating_company(numeric_code):
        """
        eg: "88"
        """
        if numeric_code == "00":
            return None

        return from_numeric_code(int(numeric_code))

    @staticmethod
    def decode_timestamp(string):
        """
        Timestamp appears to be in milliseconds:
        `1455887700000` : Tue, 31 Mar in the year 48105.
        `1455887700`    : Fri, 19 Feb 2016 13:15:00 GMT
        """

        if string == "":
            return None

        try:
            return datetime.datetime.fromtimestamp(int(string) / 1000)
        except ValueError as e:
            raise ValueError("Choked on `{}`: {}".format(string, repr(e)))
