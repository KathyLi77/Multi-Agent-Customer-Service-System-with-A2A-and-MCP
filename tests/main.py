from agents.router_agent import RouterAgent


def print_log(state):
    print("\n=== A2A LOG ===")
    messages = state.get("messages", [])
    if not messages:
        print("(no agent-to-agent messages)")
    else:
        for m in messages:
            print(f"[{m['from']} → {m['to']}] {m['content']}")
    print("==============\n")


def run(router, query):
    print("\n==============================")
    print("QUERY:", query)
    print("-" * 30)

    result = router.route(query)

    print("\nANSWER:")
    print(result["answer"])
    print_log(result["state"])


def main():
    router = RouterAgent()

    # Scenario 1: Simple lookup
    run(router, "Get customer information for ID 5")

    # Scenario 2: Task allocation
    run(router, "I'm customer 12 and need help upgrade my account")

    # Scenario 3: Escalation / negotiation
    run(router, "I've been charged twice, please cancel my subscription. My ID is 7")

    # Scenario 4: Multi-step reasoning
    run(router, "What's the status of all high-priority tickets for premium customers?")

    # Scenario 5: Multi-intent (update + history)
    run(router, "I am customer 12, update my email to new@email.com and show my ticket history")


if __name__ == "__main__":
    main()


'''
(.venv) (base) jiaqili@Jiaqis-MacBook-Pro Multi-Agent-Customer-Service-System-with-A2A-and-MCP % python -m tests.main


==============================
QUERY: Get customer information for ID 5
Processing request of type CallToolRequest
Processing request of type ListToolsRequest

ANSWER:
{'id': 5, 'name': 'Charlie Brown', 'email': 'charlie.brown@email.com', 'phone': '+1-555-0105', 'status': 'active', 'created_at': '2025-12-02 11:00:52', 'updated_at': '2025-12-02 11:00:52'}

=== A2A LOG ===
==============


==============================
QUERY: I'm customer 12 and need help upgrade my account
Processing request of type CallToolRequest
Processing request of type ListToolsRequest

ANSWER:
Hello Julia Roberts! Your account is active. I can help upgrade your plan immediately.

=== A2A LOG ===
[RouterAgent → CustomerDataAgent] Requesting customer info
[RouterAgent → SupportAgent] Forwarding upgrade task
[SupportAgent → RouterAgent] Generated upgrade response
==============


==============================
QUERY: I've been charged twice, please cancel my subscription. My ID is 7
Processing request of type CallToolRequest
Processing request of type ListToolsRequest
Processing request of type CallToolRequest
Processing request of type ListToolsRequest
Processing request of type CallToolRequest
Processing request of type ListToolsRequest

ANSWER:
Billing team already has 1 active issues for you. I have escalated to high priority.

=== A2A LOG ===
[CustomerDataAgent → RouterAgent] Get ticket history for 7
[RouterAgent → CustomerDataAgent] Creating escalation ticket
[CustomerDataAgent → RouterAgent] Create ticket: Billing problem during cancellation (priority=high)
[SupportAgent → RouterAgent] Generated billing escalation response
==============


==============================
QUERY: What's the status of all high-priority tickets for premium customers?
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
Customer 1 (John Doe): Ticket 1 — Cannot login to account [open]
Customer 4 (Alice Williams): Ticket 2 — Database connection timeout errors [in_progress]
Customer 7 (Edward Norton): Ticket 26 — Billing problem during cancellation [open]
Customer 7 (Edward Norton): Ticket 3 — Payment processing failing for all transactions [open]
Customer 10 (Hannah Lee): Ticket 4 — Critical security vulnerability found [in_progress]
Customer 14 (Laura Martinez): Ticket 5 — Website completely down [resolved]

=== A2A LOG ===
[CustomerDataAgent → RouterAgent] List active customers
[CustomerDataAgent → RouterAgent] Get ticket history for 1
[CustomerDataAgent → RouterAgent] Get ticket history for 2
[CustomerDataAgent → RouterAgent] Get ticket history for 4
[CustomerDataAgent → RouterAgent] Get ticket history for 5
[CustomerDataAgent → RouterAgent] Get ticket history for 6
[CustomerDataAgent → RouterAgent] Get ticket history for 7
[CustomerDataAgent → RouterAgent] Get ticket history for 9
[CustomerDataAgent → RouterAgent] Get ticket history for 10
[CustomerDataAgent → RouterAgent] Get ticket history for 11
[CustomerDataAgent → RouterAgent] Get ticket history for 12
[CustomerDataAgent → RouterAgent] Get ticket history for 14
[CustomerDataAgent → RouterAgent] Get ticket history for 15
[SupportAgent → RouterAgent] Summarized high-priority tickets
==============

(.venv) (base) jiaqili@Jiaqis-MacBook-Pro Multi-Agent-Customer-Service-System-with-A2A-and-MCP % 
'''