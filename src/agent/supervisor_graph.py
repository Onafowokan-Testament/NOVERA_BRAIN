from typing import Dict, List, Union

from langchain_core.messages import HumanMessage
from langgraph.config import get_config
from langgraph.graph import START, StateGraph
from langgraph.graph.message import AnyMessage, BaseMessage
from langgraph.types import Command
from langgraph.utils.config import get_store
from langgraph_supervisor import create_supervisor
from loguru import logger

from agent.configuration import NoveraConfig
from agent.meta_state import AgentState
from agent.prompt import SYSTEM_PROMPT
from agent.tools import TOOLS, store_user_profile, user_profile_builder
from agent.utils import load_chat_model

supervisor_name = "NOVERA_SUPERVISOR"
supervisor_agent_name = "NOVERA_AGENT_ORCHESTRATOR"


async def query_preprocessor_hook(
    state: AgentState,
) -> Union[Dict[str, List[BaseMessage]], Command]:
    if state.get("messages") or state["messages"] is None:
        logger.error("No message in state")

    try:
        msg = state["messages"][-1]

    except (IndexError, ValueError):
        logger.error("Exception found: No message in message_list")
        return {"llm_inp_message": state.get("messages", [])}

    if msg.name and msg.name.startswith("transfer_to"):
        Command(goto="__end__", graph=Command.PARENT)

    query = msg.content()

    store = get_store()
    configuration = NoveraConfig.from_context()

    memories = store.asearch(
        ("memories", configuration.user_id),
        query=query,
        limit=3,
    )

    if (len(memories) == 0) or not memories:
        return {"llm_inp_message": state.get("messages", [])}

    logger.info(f"Memories extracted: {memories}")

    context_content = [
        f"<li><value> {memory.value} </value> <score>{memory.score}</score> </li>"
        for memory in memories
        if memory.score >= 0.5
    ]

    for m in memories:
        logger.info(f"Score: {m.score} \n\nMessage: {m.value}")

    if len(context_content) == 0:
        return {"llm_inp_message": state.get("messages", [])}

    new_query = "{query} \n\n <context> <ul> {context_content} </ul> </context>"

    context_content = "\n".join(context_content).strip()

    new_query = new_query.format(query=query, context=context_content)

    return {
        "llm_inp_message": [*state["messages"][:-1], HumanMessage(content=new_query)]
    }


async def post_processor_hook(state: AgentState) -> Dict[str, AnyMessage]:
    """Processor used after LLM generates result"""
    human_message_indices = map(
        lambda x: state["messages"].index(x) if isinstance(x, HumanMessage) else -1,
        state["messages"],
    )

    max_index = max(human_message_indices)
    content = state["messages"][max_index].content[0]

    if not isinstance(content, str):
        content = content["text"]
        print("=" * 10 + "\n")
        print(content)
        print("=" * 10 + "\n")

    if "<context>" not in content and "</context>" not in content:
        return {"messages": state["messages"]}

    content = content.split("\n\n<context>")[0]

    state["messages"][max_index].content = content

    return {"messages": state["messages"]}


async def summarization_node(state: AgentState):
    model = load_chat_model(NoveraConfig.model, temperature=0).bind_tools(
        [user_profile_builder]
    )

    sys = """You are a text summarizer with a simple task:

Analyze all previous conversations between the user and different AI(s), and extract specific insights into user behavior patterns.
All extracted insights MUST be concise and actionable for building a comprehensive user profile."""

    msg = model.invoke(state["messages"] + HumanMessage(content=sys))

    logger.info("Summarization message: ", msg)

    if not msg.tool_calls:
        return state

    response = await store_user_profile(message=msg, config=get_config())

    logger.info(f"respose:{ response}")
    return state


async def structured_ouput_node(state: AgentState):
    pass


def instantiate_novera_orchestrator():

    graph_name = "Novera_graph"
    agents = []

    model = load_chat_model(NoveraConfig.model)
    prompt = SYSTEM_PROMPT

    supervisor_agent = create_supervisor(
        agents=agents,
        tools=TOOLS,
        model=model,
        prompt=prompt,
        pre_model_hook=query_preprocessor_hook,
        post_model_hook=post_processor_hook,
        parallel_tool_calls=True,
        state_schema=AgentState,
        config_schema=NoveraConfig,
        supervisor_name=supervisor_name,
        add_handoff_messages=True,
        add_handoff_back_messages=True,
        output_mode="last_message",
        handoff_tool_prefix="delegate_to",
    )

    supervisor_agent = supervisor_agent.compile(name=supervisor_agent_name)

    final_graph = StateGraph(AgentState, config_schema=NoveraConfig)

    final_graph.add_node("supervisor_agent_node", supervisor_agent)
    final_graph.add_node("summarization_node", summarization_node)
    final_graph.add_node("structured_output_node", structured_ouput_node)

    final_graph.add_edge(START, "supervisor_agent_node")
    final_graph.add_edge("supervisor_agent_node", "summarization_node")
    final_graph.add_edge("summarization_node", "structured_output_node")
    final_graph.add_edge("structured_ouput_node", "END")

    return final_graph.compile(name=graph_name)
