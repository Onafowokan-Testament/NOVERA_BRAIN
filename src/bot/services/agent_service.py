"""Agent service - Business logic for agent interactions."""

from typing import Any

from langchain_core.messages import HumanMessage

from agent.supervisor_graph import instantiate_novera_orchestrator
from settings.logger_config import logger


class AgentService:
    """Service for agent-related operations."""

    def __init__(self) -> None:
        """Initialize agent service with lazy-loaded agent instance."""
        self._agent = None

    def get_agent(self) -> Any:
        """Get or create agent instance.

        Returns:
            The orchestrator agent instance
        """
        if self._agent is None:
            logger.info("Initializing agent")
            self._agent = instantiate_novera_orchestrator()
        return self._agent

    async def process_message(
        self, message: str, telegram_id: str, config: dict[str, Any] = None
    ) -> dict[str, Any]:
        """Process a message through the agent.

        Args:
            message: User message
            telegram_id: Telegram user ID for thread identification
            config: Optional additional config (defaults to using telegram_id for both thread and user)

        Returns:
            Agent result dict

        Raises:
            Exception: If agent processing fails
        """
        try:
            input_data = {"messages": [HumanMessage(content=message)]}

            if config is None:
                config = {
                    "configurable": {"thread_id": telegram_id, "user_id": telegram_id}
                }

            logger.info(
                f"Processing message for user {telegram_id} with config: {config}"
            )

            agent = self.get_agent()
            result = await agent.ainvoke(input_data, config=config)

            logger.info(f"Agent result type: {type(result)}")
            return result

        except TypeError as te:
            logger.error(f"TypeError in agent invocation: {str(te)}")
            raise
        except Exception as e:
            logger.error(f"Error processing message through agent: {str(e)}")
            raise

    def extract_response_content(self, result: dict[str, Any]) -> str:
        """Extract response content from agent result.

        Args:
            result: Agent result dict

        Returns:
            Response content string

        Raises:
            ValueError: If response cannot be extracted
        """
        try:
            if not result:
                raise ValueError("Empty result from agent")

            if isinstance(result, dict) and "messages" in result:
                messages = result.get("messages", [])
                if messages and hasattr(messages[-1], "content"):
                    content = str(messages[-1].content).strip()
                    return content
                else:
                    raise ValueError("No content in response messages")
            else:
                return str(result)

        except Exception as e:
            logger.error(f"Error extracting response: {str(e)}")
            raise
