"""Timetable Agent - Class schedule and timetable queries.

Handles student and faculty schedule inquiries with memory persistence.
"""

from .agent import initiate_timetable_agent
from .schema import Configuration, State

__all__ = [
    "initiate_timetable_agent",
    "Configuration",
    "State",
]
 