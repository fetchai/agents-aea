# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""Parser and plotter for profiling logs."""
import datetime
import json
from typing import Tuple

import matplotlib.patches as mpatches  # type: ignore
from matplotlib import pyplot as plt


LOG_FILE_PATH = "/tmp/docker_log"
LOG_INSTANCE_LINES = 19
TIME_FORMAT = "relative"


# Tracked elements and line indices relative to the profile message.
# To add more here, also edit aea/cli/run.py::_profiling_context::OBJECTS_INSTANCES
element_to_indices = {
    "Total": 5,
    "Message": 8,
    "Dialogue": 9,
    "Handler": 10,
    "Model": 11,
    "Behaviour": 12,
    "Skill": 13,
    "Connection": 14,
    "Contract": 15,
    "Protocol": 16,
}

# Optionally limit the elements to be plotted
PLOT_LIST = element_to_indices.keys()


def extract_data(
    line: str, value_multiplier: float = 1.0
) -> Tuple[datetime.datetime, float]:
    """Read value and time for a given log line."""
    data = json.loads(line)
    value = (
        float(data["log"].split(":")[-1].replace("MB", "").strip()) * value_multiplier
    )
    time = datetime.datetime.strptime(data["time"][:-4], "%Y-%m-%dT%H:%M:%S.%f")
    return time, value


def main() -> None:
    """Main script."""

    # Load data
    data: dict = {e: {"times": [], "values": []} for e in element_to_indices.keys()}

    settlement_times = []

    with open(LOG_FILE_PATH, "r") as log_file:
        content = log_file.readlines()
        for line_index, line in enumerate(content):
            # Find profiling logs
            if line.startswith('{"log":"Profiling details'):
                for e, i in element_to_indices.items():
                    time, value = extract_data(content[line_index + i])
                    data[e]["times"].append(time)
                    data[e]["values"].append(value)
                line_index += LOG_INSTANCE_LINES

            elif "Finalization tx digest:" in line:
                data_point = json.loads(line)
                time = datetime.datetime.strptime(
                    data_point["time"][:-4], "%Y-%m-%dT%H:%M:%S.%f"
                )
                settlement_times.append(time)

    # Optionally transform time to minutes from start
    if TIME_FORMAT == "relative":
        time_origins = [data[key]["times"][0] for key in data.keys()]
        time_origins.append(settlement_times[0])
        time_origin = min(time_origins)

        for e in data.keys():
            data[e]["times"] = [
                (t - time_origin).seconds / 60 for t in data[e]["times"]
            ]

        settlement_times = [(t - time_origin).seconds / 60 for t in settlement_times]

    # Max y value
    max_memory_value = max(data["Total"]["values"])
    max_count_values = [
        max(data[key]["values"])
        for key in data.keys()
        if key in PLOT_LIST and key != "Total"
    ]
    max_count_value = max(max_count_values) * 1.05

    # Memory plot
    plt.plot(data["Total"]["times"], data["Total"]["values"], "g-", label="Memory")

    for t in settlement_times:
        plt.plot([t, t], [0, 1.1 * max_memory_value], "k", linewidth=0.5)

    minutes_tag = " (minutes)" if TIME_FORMAT == "relative" else ""

    plt.xlabel(f"Time{minutes_tag}")
    plt.ylabel("Memory (MB)")

    handles, _ = plt.gca().get_legend_handles_labels()
    patch = mpatches.Patch(color="black", label="Settlement")
    handles.extend([patch])
    plt.legend(handles=handles)

    # Count plot
    plt.figure()

    i = 0
    line_types = ["-", "--", "-."]
    for element, element_data in data.items():
        if element in PLOT_LIST and element != "Total":
            line_type = line_types[i % len(line_types)]
            plt.plot(
                element_data["times"], element_data["values"], line_type, label=element
            )
            i += 1

    for t in settlement_times:
        plt.plot([t, t], [0, 1.1 * max_count_value], "k", linewidth=0.5)

    minutes_tag = " (minutes)" if TIME_FORMAT == "relative" else ""

    plt.xlabel(f"Time{minutes_tag}")
    plt.ylabel("Object count")

    handles, _ = plt.gca().get_legend_handles_labels()
    patch = mpatches.Patch(color="black", label="Settlement")
    handles.extend([patch])
    plt.legend(handles=handles)

    plt.show()


if __name__ == "__main__":
    main()
