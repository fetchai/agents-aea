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

"""Import patcher."""

import builtins


class ImportWrapper:
    """This class patches the built-in __import__ function."""

    _builtin_import = builtins.__import__

    @staticmethod
    def wrapped_import(name: str, globals=None, locals=None, fromlist=(), level=0):
        """
        The patched __import__ function.

        It acts as a wrapper to the built-in __import__ function.

        It only gets activated if the first part of the import path
        is equal to "packages". Otherwise, it forwards the call to
        the builtins.__import__ function.

        For documentation on the parameters,
        please look at https://docs.python.org/3/library/functions.html#__import__.
        """
        kwargs = dict(globals=globals, locals=locals, fromlist=fromlist, level=level)
        # print(name, globals, locals, fromlist, level)
        parts = name.split(".")
        root = parts[0]
        if root == "packages" and level == 0:
            return ImportWrapper.handle_package_import(name, **kwargs)
        else:
            return ImportWrapper._builtin_import(name, **kwargs)

    @classmethod
    def handle_package_import(
        cls, name: str, globals=None, locals=None, fromlist=(), level=0
    ):
        """
        Handle the import for an AEA import path (i.e. with the leading 'packages.').

        The parameters of this function are the same of the builtins.__import__ function.
        """
        parts = name.split(".")
        root = parts[0]
        assert root == "packages"

        try:
            return ImportWrapper._builtin_import(
                name, globals=globals, locals=locals, fromlist=fromlist, level=level
            )
        except ModuleNotFoundError as e:
            cls.handle_module_not_found_error(
                e, name, globals=globals, locals=locals, fromlist=fromlist, level=level
            )

    @classmethod
    def wrap(cls):
        builtins.__import__ = cls.wrapped_import

    @classmethod
    def unwrap(cls):
        builtins.__import__ = cls._builtin_import

    @classmethod
    def handle_module_not_found_error(
        cls, e, fullname, globals, locals, fromlist, level
    ):
        """
        This method handles a 'ModuleNotFoundError' raised from wrong AEA package import.

        It will re-raise the exception with a more meaningful error message (when possible).

        :param e is the exception object. The other parameters are the arguments to the
        function __import__.
        """
        parts = fullname.split(".")
        nb_parts = len(parts)
        if nb_parts == 2:
            author = parts[1]
            raise ModuleNotFoundError(
                "No AEA package found with author name {}. The import of {} failed.".format(
                    author, fullname
                )
            )
        elif nb_parts == 3:
            author = parts[1]
            pkg_type = parts[2]
            raise ModuleNotFoundError(
                "No AEA package found with author name {} and type {}. The import of {} failed.".format(
                    author, pkg_type, fullname
                )
            )
        elif nb_parts >= 4:
            author = parts[1]
            pkg_type = parts[2]
            pkg_name = parts[3]
            raise ModuleNotFoundError(
                "No AEA package found with author name {}, type {}, and name {}. The import of {} failed.".format(
                    author, pkg_type, pkg_name, fullname
                )
            )
        else:
            raise e
