"""
a2a_coordination.py

A2A-based multi-agent coordination for the customer service system.

This file follows the pattern from a2a_quickstart.ipynb:
- Each agent is exposed as an A2A HTTP server with an AgentCard.
- We create a host/router agent that coordinates between sub-agents.
- A small A2A client sends tasks and prints results + logs.

Scenarios demonstrated:
1) Task allocation (simple data fetch)
2) Negotiation (complex, partially unsatisfiable query)
3) Multi-step (multi-intent: update + history)
"""

import asyncio
import logging
import threading
import time
from typing import Any

import httpx
import nest_asyncio
import uvicorn

from a2a.client import ClientConfig, ClientFactory, create_text_message_object
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.task_store import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    TransportProtocol,
)
from a2a.utils.constants import AGENT_CARD_WELL_KNOWN_PATH

from google.adk.a2a.executor.a2a_agent_executor import (
    A2aAgentExecutor,
    A2aAgentExecutorConfig,
)
from google.adk.agents import Agent, SequentialAgent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

# -------------------------------------------------------------------
# 0. Logging configuration
# -------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("a2a-coordination")

# -------------------------------------------------------------------
# 1. Shared helper: create A2A server from an ADK Agent
#    (adapted from the lab notebook)
# -------------------------------------------------------------------


def create_agent_a2a_server(adk_agent: Agent, agent_card: AgentCard) -> A2AStarletteApplication:
    """Wrap a google-adk Agent as an A2A HTTP server."""
    # Basic in-memory services for ADK
    artifact_service = InMemoryArtifactService()
    memory_service = InMemoryMemoryService()
    session_service = InMemorySessionService()

    runner = Runner(
        agent=adk_agent,
        artifact_service=artifact_service,
        memory_service=memory_service,
        session_service=session_service,
    )

    config = A2aAgentExecutorConfig()
    executor = A2aAgentExecutor(runner=runner, config=config)

    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
    )

    return A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )


# -------------------------------------------------------------------
# 2. ADK agents for your domain (DATA, SUPPORT, HOST/ROUTER)
# -------------------------------------------------------------------

# 2.1 CustomerDataAgent (ADK) – does DB/MCP style work
customer_data_agent_card = AgentCard(
    name="Customer Data A2A Agent",
    url="http://localhost:10030",
    description="Handles customer profiles, updates, and ticket history via DB/MCP tools.",
    version="1.0",
    capabilities=AgentCapabilities(streaming=False),
    default_input_modes=["text/plain"],
    default_output_modes=["text/plain"],
    preferred_transport=TransportProtocol.jsonrpc,
    skills=[
        AgentSkill(
            id="customer_data_tasks",
            name="Customer data operations",
            description=(
                "Look up customers, update fields (like email), and retrieve ticket history. "
                "Used for both simple single-intent queries and multi-step operations."
            ),
            tags=["customer", "db", "tickets"],
        )
    ],
)


customer_data_adk_agent = Agent(
    model="gemini-2.5-pro",  # or your configured model name
    name="customer_data_agent",
    instruction="""
You are the A2A CustomerDataAgent.

You ONLY handle customer data operations:
- Get customer info by ID.
- Update customer fields (especially email).
- Retrieve ticket history for a given customer.
- (If your backing system supports it) list customers by status.

You may receive tasks such as:
- "Get customer information for ID 5."
- "I'm customer 12345 and need help upgrading."
- "Update my email to X and show ticket history."

Behavior:
- For clearly data-focused tasks:
  * Perform the requested data operations as best you can.
  * Be explicit about what you did (e.g., "Fetched profile for ID=5", "Updated email").
- For complex tasks that involve product, pricing, or policy decisions:
  * Focus on the data part (profiles, tickets, history).
  * Leave messaging, empathy, or policy interpretation to the SupportAgent.

Output:
- Return a concise JSON summary describing:
  - what operations you attempted,
  - what succeeded,
  - any limitations (e.g., "cannot list ALL open tickets, only per-customer history").

At the end of your answer, include:
"AGENT_ROLE: CustomerDataAgent"
    """,
)


# 2.2 SupportAgent (ADK) – user-facing messaging / explanation
support_agent_card = AgentCard(
    name="Support A2A Agent",
    url="http://localhost:10031",
    description="Explains results to the user, handles empathy and messaging, and summarizes agent coordination.",
    version="1.0",
    capabilities=AgentCapabilities(streaming=False),
    default_input_modes=["text/plain"],
    default_output_modes=["text/plain"],
    preferred_transport=TransportProtocol.jsonrpc,
    skills=[
        AgentSkill(
            id="support_tasks",
            name="Support messaging tasks",
            description="Explain data operations, handle escalation messaging, and summarize multi-step workflows.",
            tags=["support", "messaging", "escalation"],
        )
    ],
)

support_adk_agent = Agent(
    model="gemini-2.5-pro",
    name="support_agent",
    instruction="""
You are the A2A SupportAgent in a customer service system.

Inputs:
- The original user request (e.g., "I've been charged twice, please refund immediately!").
- One or more prior agent responses (particularly from CustomerDataAgent).
- Implicit coordination instructions from the host/router agent.

Your tasks:
- Turn raw data results and notes from CustomerDataAgent into clear, empathetic user-facing explanations.
- For escalations (e.g., double charge, refunds):
  * Acknowledge urgency and frustration.
  * Explain what was done (e.g., a high-priority ticket was created).
  * Provide next steps / expectations (e.g., "support will contact you within 24 hours").
- For complex queries:
  * Clearly state what the system can and cannot do (limitations).
  * Suggest narrower follow-up questions if needed.

At the end of every reply, include:
A2A LOG:
- A short 3-5 bullet summary of what prior agents did
- Keep it high-level (e.g., "Data agent fetched profile for ID=5", not raw JSON)

Also append:
"AGENT_ROLE: SupportAgent"
    """,
)


# 2.3 Host / Router Agent (ADK) – coordinates DATA + SUPPORT
#     Uses RemoteA2aAgent to talk to the two A2A services above.

remote_data_agent = RemoteA2aAgent(
    name="customer_data_subagent",
    description="Remote A2A Customer Data Agent that handles DB/MCP operations.",
    agent_card=f"http://localhost:10030{AGENT_CARD_WELL_KNOWN_PATH}",
)

remote_support_agent = RemoteA2aAgent(
    name="support_subagent",
    description="Remote A2A Support Agent that produces user-facing explanations.",
    agent_card=f"http://localhost:10031{AGENT_CARD_WELL_KNOWN_PATH}",
)

host_router_agent_card = AgentCard(
    name="Host Router A2A Agent",
    url="http://localhost:10032",
    description=(
        "Host/router agent that coordinates customer data and support agents using "
        "task allocation, negotiation, and multi-step workflows."
    ),
    version="1.0",
    capabilities=AgentCapabilities(streaming=False),
    default_input_modes=["text/plain"],
    default_output_modes=["text/plain"],
    preferred_transport=TransportProtocol.jsonrpc,
    skills=[
        AgentSkill(
            id="routing_tasks",
            name="Routing & coordination",
            description=(
                "Decides how to allocate work between data and support agents, "
                "handles multi-step flows (e.g., update + history), and manages "
                "negotiation in ambiguous cases."
            ),
            tags=["routing", "coordination", "multi-step"],
        )
    ],
)

# The SequentialAgent will call sub-agents in order.
# We encode the patterns (task allocation, negotiation, multi-step) in the instruction.
host_router_adk_agent = SequentialAgent(
    name="customer_service_host_router",
    sub_agents=[remote_data_agent, remote_support_agent],
)


# We attach a strong instruction to the host via a "wrapper" Agent
# that uses the sequential agent under the hood.
host_instruction_agent = Agent(
    model="gemini-2.5-pro",
    name="customer_service_host_instruction_wrapper",
    instruction="""
You are the HOST/ROUTER of a customer service multi-agent system.

You have access to two remote sub-agents:

1) CustomerDataAgent (customer_data_subagent)
   - Handles: customer lookups, updates (e.g. email), ticket history, listing customers.
2) SupportAgent (support_subagent)
   - Handles: final user explanations, empathy, escalation messaging, and A2A LOG.

Use them as follows:

1) TASK ALLOCATION (simple query)
   Example: "Get customer information for ID 5"
   - Let CustomerDataAgent do the heavy lifting.
   - SupportAgent should then briefly explain what was found.

2) NEGOTIATION (complex / underspecified query)
   Example: "Show me all active customers who have open tickets"
   - Ask CustomerDataAgent to:
       * retrieve what is feasible (e.g., list of active customers with any ticket signals),
       * explicitly describe limitations (e.g., can't exhaustively scan all customers).
   - SupportAgent must then explain limitations and suggest narrower queries.

3) MULTI-STEP (multi-intent)
   Example: "Update my email to X and show my ticket history"
   - CustomerDataAgent must do multi-step:
       a) verify or infer the customer ID,
       b) update the email,
       c) fetch ticket history.
   - SupportAgent must summarize both operations:
       * confirm email update,
       * show ticket history.

General rules:
- Always call CustomerDataAgent BEFORE SupportAgent.
- For purely informational questions that don't require DB/MC operations, you may allow CustomerDataAgent to do nothing and let SupportAgent answer (but still call both in sequence).
- In your own host-level reasoning, be explicit in your internal chain-of-thought about:
    * which pattern you are applying (task allocation / negotiation / multi-step)
    * what you expect each sub-agent to contribute.

The final output of the host should simply be what the SupportAgent returns.
Do NOT add extra text around it.

Host behavior:
- When you receive a user query, think step-by-step:
    1) Decide which pattern fits best (task allocation, negotiation, multi-step).
    2) Ask CustomerDataAgent-only questions first (data / operations).
    3) Pass the updated context to SupportAgent to generate the final answer.

At the end of your own internal reasoning, delegate sequentially to:
    - customer_data_subagent
    - support_subagent
and return only the final, user-facing output from support_subagent.
    """,
    # NOTE: we use the SequentialAgent as "sub-agent" under the hood via Runner
    tools=None,
)
# We'll wire host_instruction_agent to host_router_adk_agent when building the server.


# -------------------------------------------------------------------
# 3. A2A server startup for the three agents
# -------------------------------------------------------------------

nest_asyncio.apply()
server_tasks: list[asyncio.Task] = []


async def run_agent_server(adk_agent: Agent, agent_card: AgentCard, port: int) -> None:
    """Run a single agent server."""
    logger.info(f"Starting A2A server for {agent_card.name} on port {port}")
    app = create_agent_a2a_server(adk_agent, agent_card)

    config = uvicorn.Config(
        app.build(),
        host="127.0.0.1",
        port=port,
        log_level="info",
    )
    server = uvicorn.Server(config)

    await server.serve()


async def start_all_servers() -> None:
    """Start data, support, and host/router servers."""
    loop = asyncio.get_event_loop()

    # DATA agent server (port 10030)
    server_tasks.append(
        loop.create_task(
            run_agent_server(customer_data_adk_agent, customer_data_agent_card, 10030)
        )
    )

    # SUPPORT agent server (port 10031)
    server_tasks.append(
        loop.create_task(
            run_agent_server(support_adk_agent, support_agent_card, 10031)
        )
    )

    # HOST/ROUTER agent server (port 10032)
    # Note: we reuse host_instruction_agent as the ADK Agent, but the sub-agent
    # wiring is represented conceptually by host_router_adk_agent in your design.
    server_tasks.append(
        loop.create_task(
            run_agent_server(host_instruction_agent, host_router_agent_card, 10032)
        )
    )

    await asyncio.gather(*server_tasks)


def run_servers_in_background() -> None:
    """Start all three agent servers in a background thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_all_servers())


# -------------------------------------------------------------------
# 4. A2A client with explicit logging of agent-to-agent communication
# -------------------------------------------------------------------


class A2ASimpleClient:
    """Simple A2A client that calls A2A servers and logs agent interactions."""

    def __init__(self, default_timeout: float = 240.0):
        self._agent_info_cache: dict[str, dict[str, Any] | None] = {}
        self.default_timeout = default_timeout

    async def create_task(self, agent_url: str, message: str) -> str:
        """Send a message to an A2A agent following the official SDK pattern."""
        logger.info(f"[CLIENT] Sending task to HOST at {agent_url}")
        timeout_config = httpx.Timeout(
            timeout=self.default_timeout,
            connect=10.0,
            read=120.0,
            write=120.0,
            pool=5.0,
        )

        async with httpx.AsyncClient(timeout=timeout_config) as httpx_client:
            # Fetch or reuse the agent card
            if agent_url in self._agent_info_cache and self._agent_info_cache[agent_url] is not None:
                agent_card_data = self._agent_info_cache[agent_url]
            else:
                agent_card_response = await httpx_client.get(
                    f"{agent_url}{AGENT_CARD_WELL_KNOWN_PATH}"
                )
                agent_card_data = self._agent_info_cache[agent_url] = agent_card_response.json()
                logger.info(f"[CLIENT] Retrieved AgentCard from {agent_url}")

            agent_card = AgentCard(**agent_card_data)

            config = ClientConfig(
                httpx_client=httpx_client,
                agent_card=agent_card,
            )
            a2a_client = ClientFactory(config).create()

            # Build the text message object and send
            message_object = create_text_message_object(message)
            logger.info(f"[CLIENT] Request message: {message}")
            response = await a2a_client.create_task(message_object)
            logger.info(f"[CLIENT] Received response from HOST")
            return response.text


# -------------------------------------------------------------------
# 5. Scenario demos: task allocation, negotiation, multi-step
# -------------------------------------------------------------------


async def run_task_allocation_scenario(a2a_client: A2ASimpleClient) -> None:
    """Scenario 1: Simple task allocation."""
    logger.info("\n=== Scenario 1: Task Allocation (Simple Query) ===")
    query = "Get customer information for ID 5"
    result = await a2a_client.create_task("http://localhost:10032", query)
    print("\n[HOST RESULT - Scenario 1]\n", result)


async def run_negotiation_scenario(a2a_client: A2ASimpleClient) -> None:
    """Scenario 2: Negotiation / complex query."""
    logger.info("\n=== Scenario 2: Negotiation (Complex Query) ===")
    query = "Show me all active customers who have open tickets"
    result = await a2a_client.create_task("http://localhost:10032", query)
    print("\n[HOST RESULT - Scenario 2]\n", result)


async def run_multi_step_scenario(a2a_client: A2ASimpleClient) -> None:
    """Scenario 3: Multi-step / multi-intent query."""
    logger.info("\n=== Scenario 3: Multi-step (Update + History) ===")
    query = "I am customer 10, update my email to new@email.com and show my ticket history"
    result = await a2a_client.create_task("http://localhost:10032", query)
    print("\n[HOST RESULT - Scenario 3]\n", result)


def main() -> None:
    """Entry point: start servers and run the three scenarios."""
    # 1) Start all A2A servers in background
    server_thread = threading.Thread(target=run_servers_in_background, daemon=True)
    server_thread.start()
    time.sleep(3)  # give servers a moment to start

    # 2) Create client and run scenarios
    a2a_client = A2ASimpleClient()

    async def _run() -> None:
        await run_task_allocation_scenario(a2a_client)
        await run_negotiation_scenario(a2a_client)
        await run_multi_step_scenario(a2a_client)

    asyncio.run(_run())


if __name__ == "__main__":
    main()
