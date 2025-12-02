# Multi-Agent Customer Service System with A2A + MCP

This project implements a full multi-agent customer service system where three specialized agents communicate using Agent-to-Agent (A2A) coordination and retrieve customer data through a Model Context Protocol (MCP) server.
It fulfills all assignment requirements, including:

## 🤖 Agents

Router Agent – orchestrates, routes, coordinates multi-step tasks

Customer Data Agent – retrieves/updates DB records through MCP tools

Support Agent – handles support actions, escalations, multi-intent responses

## 💻 MCP Server Tools

get_customer(customer_id)

list_customers(status, limit)

update_customer(customer_id, data)

create_ticket(customer_id, issue, priority)

get_customer_history(customer_id)

## ✅ Scenarios Implemented

1. Task allocation

2. Negotiation / escalation

3. Multi-step coordination

4. Multi-intent
   Example: “update my email and show my ticket history”

✅ End-to-End Tests

Running tests/main.py executes 4 scenarios and prints:

Final response

All A2A communication logs

All MCP tool calls (printed by the server)

## Project Structure

```
.
├── agents
│   ├── data_agent.py
│   ├── router_agent.py
│   └── support_agent.py
│
├── client
│   └── mcp_client.py
│
├── mcp_server
│   ├── database_setup.py
│   ├── db_access.py
│   ├── db_utils.py
│   ├── server.py
│   └── support.db
│
├── tests
│   └── main.py
│
├── README.md
└── requirements.txt
```


## Installation

1. Create and activate virtual environment
   ```
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies
   ```
   pip install -r requirements.txt
   ```
5. Initialize database
   ```
   python mcp_server/database_setup.py
   ```
   
## How to Run the System

▶️ Run All Test Scenarios

This script calls the router, triggers A2A flows, and interacts with the MCP server:
```
python -m tests.main
```

You will see:

  MCP tool calls (Processing request of type CallToolRequest…)

  Agent-to-agent logs ([RouterAgent → CustomerDataAgent] …)

  Final answers for each scenario

Scenarios executed:

  Simple lookup

  Upgrade support

  Billing escalation

  Multi-step high-priority ticket report

  Multi-intent email update + ticket history

## How MCP Works Here

The MCP server (mcp_server/server.py) exposes 5 tools.
Each tool directly interacts with the SQLite database through db_access.py.

The client (client/mcp_client.py) communicates through stdio:

  Starts MCP subprocess (python -m mcp_server.server)

  Sends JSON-RPC requests

  Returns Python dictionaries to the agents

The system supports both:

  normal Python execution

  VSCode/Jupyter environments (event-loop safe)


## How A2A Coordination Works

Agents exchange structured messages stored in:

  state["messages"]

Example log line:

  [RouterAgent → CustomerDataAgent] Requesting customer info

## Multi-Intent Scenario Implemented

Example query:

“I am customer 12, update my email to new@email.com
 and show my ticket history”

Flow:

  Router extracts ID & email

  Router → Data Agent: fetch customer info

  Router → Data Agent: update email

  Router → Data Agent: retrieve ticket history

  Router → Support Agent: summarize

  Return combined result + detailed A2A log
