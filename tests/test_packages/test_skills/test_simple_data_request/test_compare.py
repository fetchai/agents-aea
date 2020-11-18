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
"""This module ensures that the "simple_data_request" skill under tests and packages have the expected changes and are otherwise identical."""

from pathlib import Path

from tests.conftest import ROOT_DIR, match_files


def test_compare_test_skill_with_actual_skill():
    """Test that the "simple_data_request" skill in tests with the actual package are identical except couple of changes in skill.yaml"""
    path_to_actual_skill = Path(
        ROOT_DIR, "packages", "fetchai", "skills", "simple_data_request"
    )
    path_to_test_skill = Path(
        ROOT_DIR,
        "tests",
        "test_packages",
        "test_skills",
        "test_simple_data_request",
        "simple_data_request",
    )

    # compare __init__.py
    init_file_original = Path(path_to_actual_skill, "__init__.py")
    init_file_test = Path(path_to_test_skill, "__init__.py")
    is_matched, msg = match_files(init_file_original, init_file_test)
    assert is_matched, msg

    # compare behaviours.py
    behaviours_file_original = Path(path_to_actual_skill, "behaviours.py")
    behaviours_file_test = Path(path_to_test_skill, "behaviours.py")
    is_matched, msg = match_files(behaviours_file_original, behaviours_file_test)
    assert is_matched, msg

    # compare dialogues.py
    dialogues_file_original = Path(path_to_actual_skill, "dialogues.py")
    dialogues_file_test = Path(path_to_test_skill, "dialogues.py")
    is_matched, msg = match_files(dialogues_file_original, dialogues_file_test)
    assert is_matched, msg

    # compare handlers.py
    handlers_file_original = Path(path_to_actual_skill, "handlers.py")
    handlers_file_test = Path(path_to_test_skill, "handlers.py")
    is_matched, msg = match_files(handlers_file_original, handlers_file_test)
    assert is_matched, msg

    # compare README.md
    readme_file_original = Path(path_to_actual_skill, "README.md")
    readme_file_test = Path(path_to_test_skill, "README.md")
    is_matched, msg = match_files(readme_file_original, readme_file_test)
    assert is_matched, msg

    # compare skill.yaml
    skill_yaml_file_original = Path(path_to_actual_skill, "skill.yaml")
    skill_yaml_file_test = Path(path_to_test_skill, "skill.yaml")
    is_matched, msg = match_files(skill_yaml_file_original, skill_yaml_file_test)
    assert not is_matched, "the files are identical while they should NOT be!"
    assert msg == "      method: null\n      shared_state_key: null\n      url: null\n"
