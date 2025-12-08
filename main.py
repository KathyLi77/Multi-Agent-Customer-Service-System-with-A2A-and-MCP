import asyncio
from client.mcp_client import MCPDatabaseClient
from agents.router_agent import RouterAgent
from agents.data_agent import DataAgent
from agents.support_agent import SupportAgent


async def main():
    async with MCPDatabaseClient() as client:
        router = RouterAgent()
        data_agent = DataAgent(client)
        support_agent = SupportAgent(client)

        queries = [
            "Get customer information for ID 5",
            "Show my ticket history as customer 1",
            "I need support for customer ID 3"
        ]

        for q in queries:
            agent = router.route(q)
            if agent == "data_agent":
                res = await data_agent.handle(q)
            else:
                res = await support_agent.handle(q)
            print("\nUser:", q)
            print("Agent response:", res)


if __name__ == "__main__":
    asyncio.run(main())

