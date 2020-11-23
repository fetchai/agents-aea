# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2020 fetchai
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

"""This module contains class representations corresponding to every custom type in the protocol specification."""

from aea.helpers.transaction.base import RawTransaction as BaseRawTransaction
from aea.helpers.transaction.base import SignedTransaction as BaseSignedTransaction
from aea.helpers.transaction.base import Terms as BaseTerms
from aea.helpers.transaction.base import TransactionDigest as BaseTransactionDigest
from aea.helpers.transaction.base import TransactionReceipt as BaseTransactionReceipt


RawTransaction = BaseRawTransaction
SignedTransaction = BaseSignedTransaction
Terms = BaseTerms
TransactionDigest = BaseTransactionDigest
TransactionReceipt = BaseTransactionReceipt
