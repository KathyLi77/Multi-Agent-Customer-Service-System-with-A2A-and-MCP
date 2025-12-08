# Multi-Agent Customer Service System (A2A + MCP)

This project implements a multi-agent customer service system where agents coordinate through **Agent-to-Agent (A2A)** communication and interact with a SQLite database via a **Model Context Protocol (MCP)** server.

The system includes:
- **RouterAgent** – orchestrates tasks and routes queries
- **CustomerDataAgent** – interacts with database tools through MCP
- **SupportAgent** – generates final customer-facing responses

---

## 1. System Architecture

The following diagram shows how the agents and MCP server communicate:

                     ┌────────────────────┐
                     │      User Query    │
                     └───────────┬────────┘
                                 │
                      (intent detection)
                                 │
                     ┌───────────▼───────────┐
                     │     Router Agent      │
                     └───────┬────────┬──────┘
                             │        │
            customer data    │        │ support request
                             │        │
            ┌────────────────▼ ┐   ┌──▼─────────────────┐
            │ CustomerDataAgent│   │    SupportAgent    │
            └──────────┬───────┘   └─────────┬──────────┘
                       │ MCP Tools           │ builds final answer
                       │                     │
            ┌──────────▼─────────────────────▼───────────┐
            │                 MCP Server                 │
            │   SQLite DB + customers + tickets tables   │
            └────────────────────────────────────────────┘


---

## 2. MCP Tools

The MCP server exposes the following operations:

- `get_customer(customer_id)`
- `list_customers(status, limit)`
- `update_customer(customer_id, fields)`
- `create_ticket(customer_id, issue, priority)`
- `get_customer_history(customer_id)`

These tools manage the **customers** and **tickets** tables defined in `database_setup.py`.

---

## 3. Installation

```bash
git clone https://github.com/KathyLi77/Multi-Agent-Customer-Service-System-with-A2A-and-MCP
cd Multi-Agent-Customer-Service-System-with-A2A-and-MCP

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

# Initialize database
python database_setup.py
```

## 4. Running Tests
```
python -m tests.main
```
This runs all main scenarios:

Simple customer lookup

Account upgrade assistance

Billing escalation

List active customers

Multi-intent (update + ticket history)






