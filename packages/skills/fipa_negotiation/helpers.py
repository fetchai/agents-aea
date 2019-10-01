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

"""This class contains the helpers for FIPA negotiation."""

from aea.protocols.oef.models import Description

SUPPLY_DATAMODEL_NAME = "supply"
DEMAND_DATAMODEL_NAME = "demand"

def build_datamodel(good_pbk_to_quantities: Dict[str, int], is_supply: bool) -> DataModel:
    """
    Build a data model for supply and demand (i.e. for offered or requested goods).

    :param good_pbk_to_quantities: a dictionary mapping the public keys of the goods to the quantities.
    :param is_supply: Boolean indicating whether it is a supply or demand data model

    :return: the data model.
    """
    goods_quantities_attributes = [Attribute(good_pbk, int, False)
                                   for good_pbk in good_pbk_to_quantities.keys()]
    price_attribute = Attribute("price", float, False)
    description = SUPPLY_DATAMODEL_NAME if is_supply else DEMAND_DATAMODEL_NAME
    attributes = goods_quantities_attributes + [price_attribute]
    data_model = DataModel(description, attributes)
    return data_model

def build_goods_quantities_description(good_pbk_to_quantities: Dict[str, int], is_supply: bool) -> Description:
    """
    Get the service description (good quantities supplied or demanded and their price).

    :param good_pbk_to_quantities: a dictionary mapping the public keys of the goods to the quantities.
    :param is_supply: True if the description is indicating supply, False if it's indicating demand.

    :return: the description to advertise on the Service Directory.
    """
    data_model = build_datamodel(good_pbk_to_quantities, is_supply=is_supply)
    desc = Description(good_pbk_to_quantities, data_model=data_model)
    return desc

def is_compatible(self, cfp_services: Dict[str, Union[bool, List[Any]]], goods_description: Description) -> bool:
    """
    Check for a match between the CFP services and the goods description.

    :param cfp_services: the services associated with the cfp.
    :param goods_description: a description of the goods.

    :return: Bool
    """
    services = cfp_services['services']
    services = cast(List[Any], services)
    if cfp_services['description'] is goods_description.data_model.name:
        # The call for proposal description and the goods model name cannot be the same for trading agent pairs.
        return False
    for good_pbk in goods_description.data_model.attributes_by_name.keys():
        if good_pbk not in services: continue
        return True
    return False
