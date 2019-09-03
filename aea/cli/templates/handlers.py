# -*- coding: utf-8 -*-

"""
Implement the handler methods.
"""
import logging

from aea.protocols.base.abstract_handler import AbstractHandler

from aea.mail.base import Envelope

logger = logging.getLogger("aea")


class Handler(AbstractHandler):
    """Implement"""

    def handle_envelope(self, envelope: Envelope) -> None:
        """To be implemented."""
        logger.warning("'handle_envelope' method not implemented for agent {}. "
                       "The missed envelope is {}".format(self.agent.name, envelope))

    def teardown(self) -> None:
        """To be implemented"""
