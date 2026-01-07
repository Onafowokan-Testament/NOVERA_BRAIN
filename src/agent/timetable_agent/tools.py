"""Timetable Agent - Tool Definitions.

Tool definitions for timetable agent including SQL agent and memory management.
"""

import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any, Callable, Dict, Optional

from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg, tool
from langchain_openai import ChatOpenAI
from langgraph.store.base import BaseStore
from settings.logger_config import logger

from .schema import Configuration


@tool
async def upsert_memory(
    content: str,
    context: str,
    *,
    memory_id: Optional[str] = None,
    config: Annotated[RunnableConfig, InjectedToolArg] = None,
    store: Annotated[BaseStore, InjectedToolArg] = None,
) -> str:
    """Store or update a memory about the user's preferences or important information.

    Args:
        content: The main information to remember
        context: Additional background information
        memory_id: Optional ID to update existing memory
    """
    mem_id = memory_id or str(uuid.uuid4())
    user_id = Configuration.from_runnable_config(config).user_id
    await store.aput(
        ("directions", user_id, "memories"),
        key=mem_id,
        value={"content": content, "context": context},
    )
    return f"Stored memory {mem_id}"


@tool
async def talk_with_timetable(
    query: str,
    config: Annotated[RunnableConfig, InjectedToolArg] = None,
    store: Annotated[BaseStore, InjectedToolArg] = None,
) -> str:
    """The timetable database contains a table with these columns:.
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
    - "Which rooms are free at 10am on Monday?" → Check "10am_11am" column for empty/"BREAK TIME"
    - "Where is CHE334 held?" → Find the row with CHE334, return building + room
    - "What's in MKT LAB at 2pm?" → Check "2pm_3pm" for MKT LAB row

    Important notes:
    - Course codes are UPPERCASE with NO SPACES (e.g., CSC416, not csc 416)
    - Days are UPPERCASE (MONDAY, TUESDAY, etc.)
    - Empty cells or "BREAK TIME" mean the room is free

    Args:
        query: Natural language question about the timetable

    Returns:
        Detailed answer with day, time, building, and room information
    """
    # Get current date/time context
    current_time = datetime.now()
    current_day = current_time.strftime("%A")
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
    "6pm_7pm", "7pm_8pm" (TEXT): Course codes or empty/BREAK TIME

SQL Query Guidelines:

1. To find WHEN a course is scheduled (e.g., "When is CSC416?"):
```sql
SELECT 
    day,
    building,
    room_hall_lab,
    CASE 
        WHEN "8am_9am" LIKE '%CSC416%' THEN '8am-9am'
        WHEN "9am_10am" LIKE '%CSC416%' THEN '9am-10am'
        WHEN "10am_11am" LIKE '%CSC416%' THEN '10am-11am'
        WHEN "11am_12noon" LIKE '%CSC416%' THEN '11am-12noon'
        WHEN "12noon_1pm" LIKE '%CSC416%' THEN '12noon-1pm'
        WHEN "1pm_2pm" LIKE '%CSC416%' THEN '1pm-2pm'
        WHEN "2pm_3pm" LIKE '%CSC416%' THEN '2pm-3pm'
        WHEN "3pm_4pm" LIKE '%CSC416%' THEN '3pm-4pm'
        WHEN "4pm_5pm" LIKE '%CSC416%' THEN '4pm-5pm'
        WHEN "5pm_6pm" LIKE '%CSC416%' THEN '5pm-6pm'
        WHEN "6pm_7pm" LIKE '%CSC416%' THEN '6pm-7pm'
        WHEN "7pm_8pm" LIKE '%CSC416%' THEN '7pm-8pm'
    END as time_slot
FROM timetable
WHERE "8am_9am" LIKE '%CSC416%'
   OR "9am_10am" LIKE '%CSC416%'
   OR "10am_11am" LIKE '%CSC416%'
   OR "11am_12noon" LIKE '%CSC416%'
   OR "12noon_1pm" LIKE '%CSC416%'
   OR "1pm_2pm" LIKE '%CSC416%'
   OR "2pm_3pm" LIKE '%CSC416%'
   OR "3pm_4pm" LIKE '%CSC416%'
   OR "4pm_5pm" LIKE '%CSC416%'
   OR "5pm_6pm" LIKE '%CSC416%'
   OR "6pm_7pm" LIKE '%CSC416%'
   OR "7pm_8pm" LIKE '%CSC416%';
```

2. To find FREE ROOMS at a specific time (e.g., "Which rooms are free at 10am on Monday?"):
```sql
SELECT 
    building,
    room_hall_lab
FROM timetable
WHERE day = 'MONDAY'
  AND ("10am_11am" IS NULL OR "10am_11am" = '' OR "10am_11am" = 'BREAK TIME')
ORDER BY building, room_hall_lab;
```

3. To find WHERE a course is held (e.g., "Where is CHE334?"):
```sql
SELECT 
    building,
    room_hall_lab
FROM timetable
WHERE "8am_9am" LIKE '%CHE334%'
   OR "9am_10am" LIKE '%CHE334%'
   OR "10am_11am" LIKE '%CHE334%'
   OR "11am_12noon" LIKE '%CHE334%'
   OR "12noon_1pm" LIKE '%CHE334%'
   OR "1pm_2pm" LIKE '%CHE334%'
   OR "2pm_3pm" LIKE '%CHE334%'
   OR "3pm_4pm" LIKE '%CHE334%'
   OR "4pm_5pm" LIKE '%CHE334%'
   OR "5pm_6pm" LIKE '%CHE334%'
   OR "6pm_7pm" LIKE '%CHE334%'
   OR "7pm_8pm" LIKE '%CHE334%'
LIMIT 1;
```

4. To find WHAT'S in a specific room at a time (e.g., "What's in MKT LAB at 2pm?"):
```sql
SELECT 
    day,
    "2pm_3pm" as course
FROM timetable
WHERE room_hall_lab = 'MKT LAB'
  AND "2pm_3pm" IS NOT NULL
  AND "2pm_3pm" != ''
  AND "2pm_3pm" != 'BREAK TIME';
```

Important:
- Use LIKE with '%' wildcards for course code searches
- Course codes are case-sensitive (use UPPERCASE)
- Days are UPPERCASE (MONDAY, not Monday)
- Empty string '', NULL, or 'BREAK TIME' means room is free
- Always return: day, time slot, building, and room in your answer

Format your final answer clearly with all relevant details.
"""

    # Initialize SQL Database connection
    try:

        db_path = Path(__file__).resolve().parents[2] / "timetable.db"

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
                    return "Timetable table not found in database. Please regenerate the DB (run clean_timetable.py)."
        except Exception as e:
            logger.error(f"Failed to inspect sqlite DB {db_path}: {e}", exc_info=True)
            return "Error accessing timetable database."

        # Initialize SQL Database
        db = SQLDatabase.from_uri(
            f"sqlite:///{db_path.as_posiz()}",
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


async def process_tool_call(tool_call, config: RunnableConfig, *, store: BaseStore):
    print(tool_call)

    function_name = tool_call["name"]
    args = tool_call["args"]
    function = TOOLS_MAP[function_name]

    try:
        result = await function(**args, config=config, store=store)
    except Exception as e:
        print(e)
        result = await function(**args)
    # print(result)

    logger.info(f"Upserting for {function_name} ...")

    return result


# Export tools for LangGraph
TOOLS = [talk_with_timetable, upsert_memory]
TOOLS_MAP: Dict[str, Callable[..., Any]] = {
    (t.name if hasattr(t, "name") else t.__name__): (
        t.coroutine if hasattr(t, "coroutine") else t
    )
    for t in TOOLS
}
