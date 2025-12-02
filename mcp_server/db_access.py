from typing import Any, Dict, List, Optional
from datetime import datetime
from mcp_server.db_utils import get_connection, row_to_dict, rows_to_list

# ------------------------
# Customer Operations
# ------------------------

def get_customer(customer_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
    row = cur.fetchone()
    conn.close()
    return row_to_dict(row) if row else None


def list_customers(status: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()

    if status:
        cur.execute("""
            SELECT * FROM customers
            WHERE status = ?
            ORDER BY id
            LIMIT ?
        """, (status, limit))
    else:
        cur.execute("""
            SELECT * FROM customers
            ORDER BY id
            LIMIT ?
        """, (limit,))

    rows = cur.fetchall()
    conn.close()
    return rows_to_list(rows)


def update_customer(customer_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    allowed = {"name", "email", "phone", "status"}

    fields = []
    values = []

    for k, v in data.items():
        if k in allowed:
            fields.append(f"{k} = ?")
            values.append(v)

    if not fields:
        raise ValueError("No valid update fields.")

    values.append(customer_id)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(f"""
        UPDATE customers
        SET {', '.join(fields)}
        WHERE id = ?
    """, tuple(values))

    conn.commit()

    cur.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        raise ValueError("Customer not found.")

    return row_to_dict(row)

# ------------------------
# Ticket Operations
# ------------------------

def create_ticket(customer_id: int, issue: str, priority: str) -> Dict[str, Any]:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO tickets (customer_id, issue, status, priority)
        VALUES (?, ?, 'open', ?)
    """, (customer_id, issue, priority))

    ticket_id = cur.lastrowid
    conn.commit()

    cur.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
    row = cur.fetchone()
    conn.close()
    return row_to_dict(row)


def get_customer_history(customer_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT *
        FROM tickets
        WHERE customer_id = ?
        ORDER BY created_at DESC
    """, (customer_id,))
    rows = cur.fetchall()
    conn.close()
    return rows_to_list(rows)
