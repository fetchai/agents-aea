
"""This package contains the dataModel for the carpark detection agent."""

from aea.helpers.search.models import DataModel, Attribute


class CarParkDataModel (DataModel):
    """Data model for the Carpark Agent."""

    def __init__(self):
        """Initialise the dataModel."""
        self.ATTRIBUTE_LATITUDE = Attribute("latitude", float, True)
        self.ATTRIBUTE_LONGITUDE = Attribute("longitude", float, True)
        self.ATTRIBUTE_UNIQUE_ID = Attribute("unique_id", str, True)

        super().__init__("carpark_detection_datamodel", [
            self.ATTRIBUTE_LATITUDE,
            self.ATTRIBUTE_LONGITUDE,
            self.ATTRIBUTE_UNIQUE_ID])
