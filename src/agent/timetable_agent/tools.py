"""Timetable Agent - Tool Definitions.

Tool definitions for timetable agent including SQL agent and memory management.
Uses AWADOC pattern with @tool decorator and ToolRuntime[Context].
"""

import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain.tools import ToolRuntime, tool
from langchain_openai import ChatOpenAI

from agent.core.context import Context
from settings.logger_config import logger
from .schema import Configuration


@tool
async def save_timetable_memory(
    content: str,
    memory_id: Optional[str] = None,
    runtime: ToolRuntime[Context] = None,
) -> str:
    """Store or update a memory about the user's timetable preferences.

    Args:
        content: The main information to remember
        memory_id: Optional ID to update existing memory
        runtime: Tool runtime with access to user context and store

    Returns:
        Confirmation message with memory ID
    """
    if not runtime or not runtime.store:
        return "No store available for memory saving"
        
    mem_id = memory_id or str(uuid.uuid4())
    user_id = runtime.context.user_id
    
    await runtime.store.aput(
        (user_id, "timetable", mem_id),
        value={"content": content, "timestamp": datetime.now().isoformat()},
        namespace="timetable",
    )
    return f"Stored timetable memory {mem_id}"


@tool
async def talk_with_timetable(
    query: str,
    runtime: ToolRuntime[Context] = None,
) -> str:
    """Query the timetable database for course schedules and room availability.
    
    The timetable database contains a table with these columns:
    - day: Day of the week (MONDAY, TUESDAY, etc.)
    - building: Building name (CEDS, CHAPEL, CHE, CLDS/CMS)
    - room_hall_lab: Room/hall/lab name (e.g., "MKT LAB", "300LH", "C401")
    - Time slot columns: "8am_9am", "9am_10am", "10am_11am", "11am_12noon",
      "12noon_1pm", "1pm_2pm", "2pm_3pm", "3pm_4pm", "4pm_5pm",
      "5pm_6pm", "6pm_7pm", "7pm_8pm"

    Each time slot cell contains either:
    - A course code (e.g., "CSC416", "CHE334", "MKT214")
    - "BREAK TIME" or empty string = room is free
    - Multiple courses separated by "/" (e.g., "TMC111/COV-TMC111")

    Use this tool for queries like:
    - "When is CSC416?" → Search all time columns for the course code
    - "Which rooms are free at 10am on Monday?" → Check "10am_11am" column
    - "Where is CHE334 held?" → Find the row with CHE334
    - "What's in MKT LAB at 2pm?" → Check "2pm_3pm" for MKT LAB row

    Args:
        query: Natural language question about the timetable
        runtime: Tool runtime with access to user context and store

    Returns:
        Detailed answer with day, time, building, and room information
    """
    # Get current date/time context
    current_time = datetime.now()
    current_day = current_time.strftime("%A").upper()
    current_hour = current_time.strftime("%I:%M %p")

    # Map hour to time slot for "right now" queries
    hour = current_time.hour
    time_slot_map = {
        8: "8am-9am",
        9: "9am-10am",
        10: "10am-11am",
        11: "11am-12noon",
        12: "12noon-1pm",
        13: "1pm-2pm",
        14: "2pm-3pm",
        15: "3pm-4pm",
        16: "4pm-5pm",
        17: "5pm-6pm",
        18: "6pm-7pm",
        19: "7pm-8pm",
    }
    current_slot = time_slot_map.get(hour, "Outside class hours")

    # Enhanced query with context
    enhanced_query = f"""{query}

Current Context:
- Day: {current_day}
- Time: {current_time.strftime("%I:%M %p")}
- Current time slot column: "{current_slot}"

Database Schema:
Table: timetable
Columns:
  - day (TEXT): MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY
  - building (TEXT): CEDS, CHAPEL, CHE, CLDS/CMS
  - room_hall_lab (TEXT): Room names like "MKT LAB", "300LH", "C401"
  - "8am_9am", "9am_10am", "10am_11am", "11am_12noon", "12noon_1pm",
    "1pm_2pm", "2pm_3pm", "3pm_4pm", "4pm_5pm", "5pm_6pm", 
    "6pm_7pm", "7pm_8pm" (TEXT): Course codes or empty/BREAK TIME"""

    try:
        db_path = Path(__file__).resolve().parents[3] / "timetable.db"

        if not db_path.exists():
            logger.error(f"Timetable database not found: {db_path}")
            return "Timetable database is currently unavailable."
            
        try:
            with sqlite3.connect(db_path) as conn:
                cur = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='timetable';"
                )
                if cur.fetchone() is None:
                    logger.error(f"'timetable' table not found in {db_path}")
                    return "Timetable table not found in database."
        except Exception as e:
            logger.error(f"Failed to inspect sqlite DB {db_path}: {e}", exc_info=True)
            return "Error accessing timetable database."

        # Initialize SQL Database
        db = SQLDatabase.from_uri(
            f"sqlite:///{db_path.as_posix()}",
            sample_rows_in_table_info=3,
        )

        # Create LLM
        llm = ChatOpenAI(temperature=0, model="gpt-4o")

        # Create SQL agent
        agent_executor = create_sql_agent(
            llm=llm,
            db=db,
            agent_type="tool-calling",
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=10,
            max_execution_time=30,
        )

        # Execute the query
        result = await agent_executor.ainvoke({"input": enhanced_query})
        answer = result.get("output", "I couldn't find an answer to that question.")

        logger.info(f"SQL Timetable Query: {query} | Answer: {answer}")
        return answer

    except Exception as e:
        logger.error(f"SQL timetable query failed: {str(e)}", exc_info=True)
        return (
            "Sorry, I encountered an error accessing the timetable database. "
            "Please try rephrasing your question."
        )


# Export tools for LangGraph
TOOLS = [talk_with_timetable, save_timetable_memory]
