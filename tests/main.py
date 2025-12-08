# tests/main.py
from agents.router_agent import RouterAgent


def print_log(state):
    print("\n=== A2A LOG ===")

    if not state:
        print("(no state returned)")
        print("=================\n")
        return

    messages = state.get("messages", [])

    if not messages:
        print("(no agent-to-agent messages)")
    else:
        for m in messages:
            sender = m.get("from", "Unknown")
            receiver = m.get("to", "Unknown")
            content = m.get("content", "")
            print(f"[{sender} → {receiver}] {content}")

    print("==============\n")


def run(router, query):
    print("\n==============================")
    print(f"QUERY: {query}")
    print("==============================")

    # Execute RouterAgent
    result = router.route(query)

    # Safely extract fields
    answer = result.get("answer", "(no answer)")
    state = result.get("state", {})

    print("\nANSWER:")
    print(answer)

    # Print A2A message log
    print_log(state)


def main():
    router = RouterAgent()

    scenarios = [
        "Get customer information for ID 5",
        "I'm customer 12 and need help upgrade my account",
        "I've been charged twice, please cancel my subscription. My ID is 7",
        "Show me all active customers who have open tickets",
        "I am customer 10, update my email to new@email.com and show my ticket history"
    ]

    for query in scenarios:
        run(router, query)


if __name__ == "__main__":
    main()
