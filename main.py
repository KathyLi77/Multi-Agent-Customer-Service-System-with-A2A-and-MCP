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

'''
(.venv) (base) jiaqili@Jiaqis-MacBook-Pro Multi-Agent-Customer-Service-System-with-A2A-and-MCP % python -m tests.main


==============================
QUERY: Get customer information for ID 5
------------------------------
Processing request of type CallToolRequest
Processing request of type ListToolsRequest

ANSWER:
{'id': 5, 'name': 'Charlie Brown', 'email': 'charlie.brown@email.com', 'phone': '+1-555-0105', 'status': 'active', 'created_at': '2025-12-02 11:00:52', 'updated_at': '2025-12-02 11:00:52'}

=== A2A LOG ===
[RouterAgent → CustomerDataAgent] Get customer 5
==============


==============================
QUERY: I'm customer 12 and need help upgrade my account
------------------------------
Processing request of type CallToolRequest
Processing request of type ListToolsRequest

ANSWER:
Hello Julia Roberts! Your account is active. I can help upgrade your plan immediately.

=== A2A LOG ===
[RouterAgent → CustomerDataAgent] Requesting customer info
[RouterAgent → CustomerDataAgent] Get customer 12
[RouterAgent → SupportAgent] Forwarding upgrade task
==============


==============================
QUERY: I've been charged twice, please cancel my subscription. My ID is 7
------------------------------
Processing request of type CallToolRequest
Processing request of type ListToolsRequest
Processing request of type CallToolRequest
Processing request of type ListToolsRequest
Processing request of type CallToolRequest
Processing request of type ListToolsRequest

ANSWER:
Billing team already has 5 active issues for you. I have escalated to high priority.

=== A2A LOG ===
[RouterAgent → CustomerDataAgent] Get customer 7
[RouterAgent → CustomerDataAgent] Get ticket history for 7
[RouterAgent → CustomerDataAgent] Creating escalation ticket
[RouterAgent → CustomerDataAgent] Create ticket: Billing problem during cancellation (high)
==============


==============================
QUERY: What's the status of all high-priority tickets for premium customers?
------------------------------
Processing request of type CallToolRequest
Processing request of type ListToolsRequest
Processing request of type CallToolRequest
Processing request of type ListToolsRequest
Processing request of type CallToolRequest
Processing request of type ListToolsRequest
Processing request of type CallToolRequest
Processing request of type ListToolsRequest
Processing request of type CallToolRequest
Processing request of type ListToolsRequest
Processing request of type CallToolRequest
Processing request of type ListToolsRequest
Processing request of type CallToolRequest
Processing request of type ListToolsRequest
Processing request of type CallToolRequest
Processing request of type ListToolsRequest
Processing request of type CallToolRequest
Processing request of type ListToolsRequest
Processing request of type CallToolRequest
Processing request of type ListToolsRequest
Processing request of type CallToolRequest
Processing request of type ListToolsRequest
Processing request of type CallToolRequest
Processing request of type ListToolsRequest
Processing request of type CallToolRequest
Processing request of type ListToolsRequest

ANSWER:
John Doe: Ticket 1 — Cannot login to account [open]
Alice Williams: Ticket 2 — Database connection timeout errors [in_progress]
Edward Norton: Ticket 30 — Billing problem during cancellation [open]
Edward Norton: Ticket 29 — Billing problem during cancellation [open]
Edward Norton: Ticket 28 — Billing problem during cancellation [open]
Edward Norton: Ticket 27 — Billing problem during cancellation [open]
Edward Norton: Ticket 26 — Billing problem during cancellation [open]
Edward Norton: Ticket 3 — Payment processing failing for all transactions [open]
Hannah Lee: Ticket 4 — Critical security vulnerability found [in_progress]
Laura Martinez: Ticket 5 — Website completely down [resolved]

=== A2A LOG ===
[RouterAgent → CustomerDataAgent] List active customers
[RouterAgent → CustomerDataAgent] Get ticket history for 1
[RouterAgent → CustomerDataAgent] Get ticket history for 2
[RouterAgent → CustomerDataAgent] Get ticket history for 4
[RouterAgent → CustomerDataAgent] Get ticket history for 5
[RouterAgent → CustomerDataAgent] Get ticket history for 6
[RouterAgent → CustomerDataAgent] Get ticket history for 7
[RouterAgent → CustomerDataAgent] Get ticket history for 9
[RouterAgent → CustomerDataAgent] Get ticket history for 10
[RouterAgent → CustomerDataAgent] Get ticket history for 11
[RouterAgent → CustomerDataAgent] Get ticket history for 12
[RouterAgent → CustomerDataAgent] Get ticket history for 14
[RouterAgent → CustomerDataAgent] Get ticket history for 15
==============


==============================
QUERY: I am customer 12, update my email to new@email.com and show my ticket history
------------------------------
Processing request of type CallToolRequest
Processing request of type ListToolsRequest
Processing request of type CallToolRequest
Processing request of type ListToolsRequest
Processing request of type CallToolRequest
Processing request of type ListToolsRequest

ANSWER:
Success! I've updated the email for customer 12 (Julia Roberts) to new@email.com.

Here is your ticket history:
 - Ticket 12: Search functionality returning wrong results [in_progress]
 - Ticket 21: Color scheme suggestion for better contrast [open]

=== A2A LOG ===
[RouterAgent → CustomerDataAgent] Fetching customer info for 12
[RouterAgent → CustomerDataAgent] Get customer 12
[RouterAgent → CustomerDataAgent] Updating email to new@email.com
[RouterAgent → CustomerDataAgent] Update customer 12: {'email': 'new@email.com'}
[RouterAgent → CustomerDataAgent] Fetching ticket history
[RouterAgent → CustomerDataAgent] Get ticket history for 12
[RouterAgent → SupportAgent] Summarizing multi-intent response
==============

(.venv) (base) jiaqili@Jiaqis-MacBook-Pro Multi-Agent-Customer-Service-System-with-A2A-and-MCP % 
'''