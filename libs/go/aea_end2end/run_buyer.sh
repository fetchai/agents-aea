#!/bin/bash
source fipa_dummy_seller.env

SELLER_ADDR=${AEA_ADDRESS}
aea --registry-path ../../../packages fetch fetchai/fipa_dummy_buyer --local
cd fipa_dummy_buyer
aea build
aea config set vendor.fetchai.skills.fipa_dummy_buyer.behaviours.initializer.args.opponent_address $SELLER_ADDR
aea generate-key fetchai
aea add-key fetchai
aea add-key fetchai --connection
aea issue-certificates
aea -v DEBUG run
cd ../
rm -fr ./fipa_dummy_buyer
