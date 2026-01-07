"""Timetable Agent - Class schedule and timetable queries.

Handles student and faculty schedule inquiries with memory persistence.
"""

from .agent import initiate_timetable_agent
from .schema import Configuration, State

# Create the default graph instance
graph = initiate_timetable_agent()

__all__ = [
    "graph",
    "initiate_timetable_agent",
    "Configuration",
    "State",
]
 