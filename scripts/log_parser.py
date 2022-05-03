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

"""Parser and plotter for profiling logs. Pyqt5 might be required in some systems in order for the script to work: pip install PyQt5"""
import datetime
import json
import os
import random
import re
from enum import Enum
from typing import Dict, List, Optional

from matplotlib import pyplot as plt  # type: ignore


LOG_FILE_DIR_BASE = "/tmp/oracle_logs"  # nosec


class TimeFormat(Enum):
    """Time formats"""

    RELATIVE = "relative"
    ABSOLUTE = "absolute"


class LineStyle(Enum):
    """Line styles"""

    SOLID = "-"
    DASHED = "--"
    DOTTED = ":"
    DASH_DOTTED = "-."


class LineColor(Enum):
    """Line colors"""

    BLACK = "k"
    RED = "r"
    GREEN = "g"
    BLUE = "b"
    YELLOW = "y"
    CYAN = "c"
    MAGENTA = "m"


def get_latest_log_by_agent_index(agent_index: Optional[int] = 0):
    """Retrieve the last log for the specified agent in the log directory"""
    most_recent_logs_dir = sorted(os.listdir(LOG_FILE_DIR_BASE))[-1]
    log_file_path = f"{LOG_FILE_DIR_BASE}/{most_recent_logs_dir}/abci{agent_index}.log"
    return log_file_path


class LogParser:
    """A class to parse and plot information from agent logs"""

    def __init__(
        self,
        log_file_path: Optional[str] = None,
        agent_index: Optional[int] = 0,
        time_format: Optional[TimeFormat] = TimeFormat.RELATIVE,
    ) -> None:
        """Log parser"""
        self.log_file_path = (
            log_file_path
            if log_file_path
            else get_latest_log_by_agent_index(agent_index)
        )
        self.agent_index = agent_index
        self.time_format = time_format
        self.default_x_label = (
            "Time [min]" if self.time_format == TimeFormat.RELATIVE else "Time"
        )
        self.time_origin: Optional[datetime.datetime] = None
        self.line_trackers: Dict[str, Dict] = {}
        self.figures: List = []

    def add_tracker(
        self,
        tracker_name: str,
        regex: str,
        tracker_type: str = "line",
        figure_names: Optional[List[str]] = None,
        line_styles: Optional[dict] = None,
    ) -> None:
        """Add a line of interest in the log to track"""

        # Read all the variables in the regex and initialize them
        var_name_regex = r"\(\?P<(?P<var_name>.*?)>"
        var_names = re.findall(var_name_regex, regex)
        if tracker_type == "event":
            var_names = ["event"]
        var_data: Dict[str, Dict] = {
            var_name: {"times": [], "values": [], "line": {}} for var_name in var_names
        }

        for var_name in var_names:
            line_style = (
                line_styles[var_name]["style"]
                if line_styles and var_name in line_styles
                else random.choice([e.value for e in LineColor])  # nosec
            )
            line_color = (
                line_styles[var_name]["color"]
                if line_styles and var_name in line_styles
                else random.choice([e.value for e in LineStyle])  # nosec
            )
            var_data[var_name]["line_style"] = f"{line_color}{line_style}"
            var_data[var_name]["line_width"] = (
                line_styles[var_name]["width"]
                if line_styles and var_name in line_styles
                else 1
            )

        self.line_trackers[tracker_name] = {
            "regex": regex,
            "type": tracker_type,
            "figure_names": figure_names if figure_names else [tracker_name],
            "var_data": var_data,
        }

    def process(self) -> None:
        """Process the log"""
        with open(self.log_file_path, "r") as log_file:
            content = log_file.readlines()

            # Guess log type
            LOG_TYPE = ""
            try:
                json.loads(content[0])
            except json.JSONDecodeError:
                LOG_TYPE = "text"
            else:
                LOG_TYPE = "json"

            for line in content:

                line_time: Optional[datetime.datetime] = None
                line_data: str = line

                # Handle json logs
                if LOG_TYPE == "json":
                    line_json = json.loads(line)
                    line_time = datetime.datetime.strptime(
                        line_json["time"][:-4], "%Y-%m-%dT%H:%M:%S.%f"
                    )
                    line_data = line_json["log"]
                    if not self.time_origin:
                        self.time_origin = line_time

                # Add line data to corresponding plots
                for tracker_name, tracker_data in self.line_trackers.items():
                    match = re.match(tracker_data["regex"], line_data)
                    if match:
                        if tracker_data["type"] == "event":
                            self.line_trackers[tracker_name]["var_data"]["event"][
                                "times"
                            ].append(line_time)
                            continue

                        for var_name, var_value in match.groupdict().items():
                            self.line_trackers[tracker_name]["var_data"][var_name][
                                "times"
                            ].append(line_time)
                            self.line_trackers[tracker_name]["var_data"][var_name][
                                "values"
                            ].append(float(var_value))
                        continue

            if self.time_format == TimeFormat.RELATIVE:
                self.convert_times_to_relative()

    def convert_times_to_relative(self):
        """Convert time variables to time from the first time in the log"""
        for tracker_name, tracker_data in self.line_trackers.items():
            for var_name in tracker_data["var_data"]:
                self.line_trackers[tracker_name]["var_data"][var_name]["times"] = [
                    (t - self.time_origin).seconds / 60
                    for t in self.line_trackers[tracker_name]["var_data"][var_name][
                        "times"
                    ]
                ]

    def add_figure(
        self,
        fig_name: str,
        fig_title: Optional[str] = None,
        x_label: Optional[str] = None,
        y_label: Optional[str] = None,
    ) -> None:
        """Add a new figure to plot"""
        self.figures.append(plt.figure(fig_name))
        plt.figure(fig_name)
        file_name = self.log_file_path.split("/")[-2]
        plt.title(
            f"{fig_title} [{file_name}] [Agent {self.agent_index}]"
            if fig_title
            else f"{fig_name} [{file_name}] [Agent {self.agent_index}]"
        )

        x_label = x_label if x_label else self.default_x_label
        plt.xlabel(x_label)

        if y_label:
            plt.ylabel(y_label)

    def plot(self) -> None:
        """Plot a figure"""

        # Max y values (needed for events)
        max_values: Dict[str, float] = {}
        for tracker_data in [
            v for v in self.line_trackers.values() if v["type"] != "event"
        ]:
            for figure_name in tracker_data["figure_names"]:
                for var_data in tracker_data["var_data"].values():
                    if var_data["values"]:
                        max_var = max(var_data["values"])
                        if figure_name not in max_values:
                            max_values[figure_name] = max_var
                        else:
                            if max_var > max_values[figure_name]:
                                max_values[figure_name] = max_var

        # Plot
        for tracker_name, tracker_data in self.line_trackers.items():
            for figure_name in tracker_data["figure_names"]:
                plt.figure(figure_name)
                for var_name, var_data in tracker_data["var_data"].items():

                    if tracker_data["type"] == "event" and var_data["times"]:
                        t0 = var_data["times"][0]
                        plt.plot(
                            [t0, t0],
                            [0, 1.05 * max_values[figure_name]],
                            var_data["line_style"],
                            linewidth=var_data["line_width"],
                            label=f"{tracker_name}",
                        )
                        for t in var_data["times"][1:]:
                            plt.plot(
                                [t, t],
                                [0, 1.05 * max_values[figure_name]],
                                var_data["line_style"],
                                linewidth=var_data["line_width"],
                            )
                        plt.legend()
                        continue

                    if not var_data["values"]:
                        print(
                            f"[Figure {figure_name}] Data for {tracker_name}::{var_name} not found in the log!"
                        )
                        continue

                    if not var_data["times"] or None in var_data["times"]:
                        plt.plot(
                            var_data["values"],
                            var_data["line"],
                            linewidth=var_data["line_width"],
                            label=f"{tracker_name}::{var_name}",
                        )
                    else:
                        plt.plot(
                            var_data["times"],
                            var_data["values"],
                            var_data["line_style"],
                            linewidth=var_data["line_width"],
                            label=f"{tracker_name}::{var_name}",
                        )
                    plt.legend()
        plt.show()


def extract_gc_objects_set(log_file_path):
    """Extract a set of all objects that appeared in the garbage collector count section"""
    objs = set()
    with open(log_file_path, "r") as log:
        for line in log.readlines():
            match = re.match(r".*\* (?P<name>.*) \(gc\):  (?P<value>\d+).*", line)
            if match:
                objs.add(match.groupdict()["name"])
    return sorted(objs)


def add_count_trackers(
    parser: LogParser,
    tracker_names: List[str],
    figure_names: List[str],
    tracker_name_appendix: str = "",
):
    """Basic trackers for counters"""
    for tracker_name in tracker_names:
        parser.add_tracker(
            tracker_name=f"{tracker_name}{tracker_name_appendix}",
            regex=r".*\* "
            + re.escape(f"{tracker_name}{tracker_name_appendix}")
            + r":  (?P<count>\d+).*",
            figure_names=figure_names,
        )


def main():
    """Main function"""
    log_parser = LogParser(
        agent_index=0, time_format=TimeFormat.RELATIVE
    )  # uses the most recent log by default

    # Add figures
    log_parser.add_figure(fig_name="Memory", y_label="Memory [MB]")
    log_parser.add_figure(fig_name="Object count (present)", y_label="Count")
    log_parser.add_figure(fig_name="Object count (created)", y_label="Count")
    log_parser.add_figure(fig_name="Object count (gc)", y_label="Count")

    # Memory
    log_parser.add_tracker(
        tracker_name="Memory",
        regex=r"Memory: (?P<current_memory>\d+\.\d+).*Peak (?P<peak_memory>\d+\.\d+).*",
        figure_names=["Memory"],
        tracker_type="line",
        line_styles={
            "current_memory": {
                "style": LineStyle.SOLID.value,
                "color": LineColor.GREEN.value,
                "width": 2,
            },
            "peak_memory": {
                "style": LineStyle.SOLID.value,
                "color": LineColor.RED.value,
                "width": 2,
            },
        },
    )

    # Settlement events
    log_parser.add_tracker(
        tracker_name="Settlement",
        regex=r".*Finalized with transaction hash: .*",  # validation message
        figure_names=[
            "Memory",
            "Object count (present)",
            "Object count (created)",
            "Object count (gc)",
        ],
        tracker_type="event",
        line_styles={
            "event": {
                "style": LineStyle.SOLID.value,
                "color": LineColor.BLACK.value,
                "width": 1.5,
            },
        },
    )

    # Tendermint reset events
    log_parser.add_tracker(
        tracker_name="Tendermint reset",
        regex=r".*Resetting tendermint node successful!.*",
        figure_names=[
            "Memory",
            "Object count (present)",
            "Object count (created)",
            "Object count (gc)",
        ],
        tracker_type="event",
        line_styles={
            "event": {
                "style": LineStyle.DASHED.value,
                "color": LineColor.RED.value,
                "width": 1.5,
            },
        },
    )

    # Tracked objects
    tracked_objects = [
        "Message",
        "Dialogue",
        "DialogueLabel",
        "Handler",
        "Model",
        "Behaviour",
        "Skill",
        "Connection",
        "Contract",
        "Protocol",
    ]

    # Present tracked objects
    add_count_trackers(
        parser=log_parser,
        tracker_names=tracked_objects,
        figure_names=["Object count (present)"],
        tracker_name_appendix=" (present)",
    )
    # Created tracked objects
    add_count_trackers(
        parser=log_parser,
        tracker_names=tracked_objects,
        figure_names=["Object count (created)"],
        tracker_name_appendix=" (created)",
    )
    # Present common objects in the garbage collector
    tracked_objects_in_gc = extract_gc_objects_set(log_parser.log_file_path)

    add_count_trackers(
        parser=log_parser,
        tracker_names=tracked_objects_in_gc,
        figure_names=["Object count (gc)"],
        tracker_name_appendix=" (gc)",
    )

    # Process and plot
    log_parser.process()
    log_parser.plot()


if __name__ == "__main__":
    main()
