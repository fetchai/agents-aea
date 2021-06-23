# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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

"""Helpers for the logging module."""

import logging
import sys
from typing import Any, Callable

import click


OFF = 100
logging.addLevelName(OFF, "OFF")

LOG_LEVELS = ["NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "OFF"]


class ColorFormatter(logging.Formatter):
    """The default formatter for cli output."""

    colors = {
        "error": dict(fg="red"),
        "exception": dict(fg="red"),
        "critical": dict(fg="red"),
        "debug": dict(fg="blue"),
        "info": dict(fg="green"),
        "warning": dict(fg="yellow"),
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format the log message."""
        if not record.exc_info:
            level = record.levelname.lower()
            msg = record.getMessage()
            if level in self.colors:
                prefix = click.style("{}: ".format(level), **self.colors[level])  # type: ignore
                msg = "\n".join(prefix + x for x in msg.splitlines())
            return msg
        return logging.Formatter.format(self, record)  # pragma: no cover


def simple_verbosity_option(
    logger_: logging.Logger, *names: str, **kwargs: Any
) -> Callable:  # pylint: disable=redefined-outer-name,keyword-arg-before-vararg
    """Add a decorator that adds a `--verbosity, -v` option to the decorated command.

    Name can be configured through `*names`. Keyword arguments are passed to
    the underlying `click.option` decorator.

    :param logger_: the logger
    :param names: list of names
    :param kwargs: keyword arguments
    :return: callable
    """
    if not names:
        names = ("--verbosity", "-v")

    kwargs.setdefault("default", "INFO")
    kwargs.setdefault("type", click.Choice(LOG_LEVELS, case_sensitive=False))
    kwargs.setdefault("metavar", "LVL")
    kwargs.setdefault("expose_value", False)
    kwargs.setdefault("help", "One of {}".format(", ".join(LOG_LEVELS)))
    kwargs.setdefault("is_eager", True)

    def decorator(f: Callable) -> Callable:
        def _set_level(
            ctx: click.Context,
            param: Any,  # pylint: disable=unused-argument
            value: str,
        ) -> None:
            level = logging.getLevelName(value)
            logger_.setLevel(level)
            # save verbosity option so it can be
            # read in the main CLI entrypoint
            ctx.meta["verbosity"] = value

        return click.option(*names, callback=_set_level, **kwargs)(f)

    return decorator


def default_logging_config(
    logger_: logging.Logger,
) -> logging.Logger:  # pylint: disable=redefined-outer-name
    """Set up the default handler and formatter on the given logger."""
    default_handler = logging.StreamHandler(stream=sys.stdout)
    default_handler.formatter = ColorFormatter()
    logger_.handlers = [default_handler]
    logger_.propagate = True
    return logger_


logger = logging.getLogger("aea")
logger = default_logging_config(logger)
