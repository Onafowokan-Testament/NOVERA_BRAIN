"""Timetable Agent - Handles timetable and class schedule queries."""

from .graph import initiate_timetable_agent

# Create the default graph instance
graph = initiate_timetable_agent()

__all__ = ["graph", "initiate_timetable_agent"]
 