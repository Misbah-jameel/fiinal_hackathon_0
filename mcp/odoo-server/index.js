#!/usr/bin/env node
/**
 * Odoo MCP Server — AI Employee Gold Tier
 * ----------------------------------------
 * Integrates with Odoo Community (self-hosted) via JSON-RPC API.
 * Provides tools for:
 *   - odoo_get_invoices    — list/filter invoices
 *   - odoo_create_invoice  — draft a new invoice
 *   - odoo_get_customers   — list customers/partners
 *   - odoo_get_balance     — accounting summary
 *   - odoo_list_payments   — recent payments
 *   - odoo_get_revenue     — revenue report for a period
 *
 * Setup:
 *   1. Install Odoo Community (https://www.odoo.com/documentation/17.0/administration/install.html)
 *   2. Set env vars: ODOO_URL, ODOO_DB, ODOO_USER, ODOO_PASSWORD
 *   3. Registered in .claude/settings.json as "odoo" MCP server
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import fetch from "node-fetch";

const ODOO_URL = process.env.ODOO_URL || "http://localhost:8069";
const ODOO_DB = process.env.ODOO_DB || "ai_employee";
const ODOO_USER = process.env.ODOO_USER || "admin";
const ODOO_PASSWORD = process.env.ODOO_PASSWORD || "admin";

let sessionId = null;
let uid = null;

// ─── JSON-RPC Helper ───────────────────────────────────────────────────────────

async function jsonRpc(endpoint, method, params) {
  const body = {
    jsonrpc: "2.0",
    method: "call",
    id: Date.now(),
    params: { ...params },
  };

  try {
    const res = await fetch(`${ODOO_URL}${endpoint}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(sessionId ? { Cookie: `session_id=${sessionId}` } : {}),
      },
      body: JSON.stringify(body),
    });

    const setCookie = res.headers.get("set-cookie");
    if (setCookie) {
      const match = setCookie.match(/session_id=([^;]+)/);
      if (match) sessionId = match[1];
    }

    const data = await res.json();
    if (data.error) throw new Error(JSON.stringify(data.error));
    return data.result;
  } catch (err) {
    throw new Error(`Odoo RPC error: ${err.message}`);
  }
}

async function ensureAuth() {
  if (uid) return uid;
  const result = await jsonRpc("/web/session/authenticate", "call", {
    db: ODOO_DB,
    login: ODOO_USER,
    password: ODOO_PASSWORD,
  });
  if (!result || !result.uid) throw new Error("Odoo authentication failed");
  uid = result.uid;
  return uid;
}

async function searchRead(model, domain, fields, limit = 20) {
  await ensureAuth();
  return jsonRpc("/web/dataset/call_kw", "call", {
    model,
    method: "search_read",
    args: [domain],
    kwargs: { fields, limit, order: "id desc" },
  });
}

async function callMethod(model, method, args = [], kwargs = {}) {
  await ensureAuth();
  return jsonRpc("/web/dataset/call_kw", "call", {
    model,
    method,
    args,
    kwargs,
  });
}

// ─── Tools ────────────────────────────────────────────────────────────────────

const TOOLS = [
  {
    name: "odoo_get_invoices",
    description: "List invoices from Odoo. Filter by state (draft/posted/paid/cancel), customer, or date range.",
    inputSchema: {
      type: "object",
      properties: {
        state: { type: "string", enum: ["draft", "posted", "paid", "cancel", "all"], description: "Invoice state" },
        limit: { type: "number", description: "Max results (default 10)" },
        customer_name: { type: "string", description: "Filter by customer name (partial match)" },
      },
    },
  },
  {
    name: "odoo_create_invoice",
    description: "Create a draft invoice in Odoo for a customer. Requires human approval before posting.",
    inputSchema: {
      type: "object",
      required: ["customer_name", "amount", "description"],
      properties: {
        customer_name: { type: "string", description: "Customer name (must exist in Odoo)" },
        amount: { type: "number", description: "Invoice amount (before tax)" },
        description: { type: "string", description: "Line item description" },
        currency: { type: "string", description: "Currency code (default: USD)" },
      },
    },
  },
  {
    name: "odoo_get_customers",
    description: "List customers/partners from Odoo.",
    inputSchema: {
      type: "object",
      properties: {
        search: { type: "string", description: "Search by name or email" },
        limit: { type: "number", description: "Max results (default 20)" },
      },
    },
  },
  {
    name: "odoo_get_balance",
    description: "Get accounting summary: total receivables, payables, and bank balance.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "odoo_list_payments",
    description: "List recent payments received.",
    inputSchema: {
      type: "object",
      properties: {
        limit: { type: "number", description: "Max results (default 10)" },
      },
    },
  },
  {
    name: "odoo_get_revenue",
    description: "Get revenue report for current month or a date range.",
    inputSchema: {
      type: "object",
      properties: {
        date_from: { type: "string", description: "Start date YYYY-MM-DD (default: first of current month)" },
        date_to: { type: "string", description: "End date YYYY-MM-DD (default: today)" },
      },
    },
  },
];

// ─── Tool Handlers ─────────────────────────────────────────────────────────────

async function handleGetInvoices({ state = "all", limit = 10, customer_name }) {
  let domain = [["move_type", "=", "out_invoice"]];
  if (state !== "all") domain.push(["payment_state", "=", state]);
  if (customer_name) domain.push(["partner_id.name", "ilike", customer_name]);

  const invoices = await searchRead(
    "account.move",
    domain,
    ["name", "partner_id", "amount_total", "amount_residual", "invoice_date", "payment_state", "state"],
    limit
  );

  if (!invoices.length) return { content: [{ type: "text", text: "No invoices found." }] };

  const rows = invoices.map(inv =>
    `- **${inv.name}** | Customer: ${inv.partner_id[1]} | Total: ${inv.amount_total} | Due: ${inv.amount_residual} | Status: ${inv.payment_state} | Date: ${inv.invoice_date}`
  ).join("\n");

  return { content: [{ type: "text", text: `## Invoices (${invoices.length})\n\n${rows}` }] };
}

async function handleCreateInvoice({ customer_name, amount, description, currency = "USD" }) {
  // Find customer
  const partners = await searchRead("res.partner", [["name", "ilike", customer_name]], ["id", "name"], 1);
  if (!partners.length) {
    return { content: [{ type: "text", text: `ERROR: Customer "${customer_name}" not found in Odoo. Please create them first.` }] };
  }
  const partner = partners[0];

  // Create draft invoice
  const invoiceId = await callMethod("account.move", "create", [[{
    move_type: "out_invoice",
    partner_id: partner.id,
    invoice_line_ids: [[0, 0, {
      name: description,
      quantity: 1,
      price_unit: amount,
    }]],
  }]]);

  return {
    content: [{
      type: "text",
      text: `✅ Draft invoice created (ID: ${invoiceId}) for ${partner.name} — Amount: ${amount} ${currency}\n\n⚠️ DRAFT ONLY — requires human approval in /Pending_Approval before posting.`
    }]
  };
}

async function handleGetCustomers({ search, limit = 20 }) {
  let domain = [["customer_rank", ">", 0]];
  if (search) domain.push("|", ["name", "ilike", search], ["email", "ilike", search]);

  const partners = await searchRead("res.partner", domain, ["id", "name", "email", "phone", "customer_rank"], limit);
  if (!partners.length) return { content: [{ type: "text", text: "No customers found." }] };

  const rows = partners.map(p => `- **${p.name}** | Email: ${p.email || "—"} | Phone: ${p.phone || "—"}`).join("\n");
  return { content: [{ type: "text", text: `## Customers (${partners.length})\n\n${rows}` }] };
}

async function handleGetBalance() {
  // Receivables (accounts receivable = type receivable)
  const receivables = await searchRead(
    "account.move.line",
    [["account_id.account_type", "=", "asset_receivable"], ["reconciled", "=", false]],
    ["amount_residual"],
    1000
  );
  const totalReceivable = receivables.reduce((s, l) => s + (l.amount_residual || 0), 0);

  // Payables
  const payables = await searchRead(
    "account.move.line",
    [["account_id.account_type", "=", "liability_payable"], ["reconciled", "=", false]],
    ["amount_residual"],
    1000
  );
  const totalPayable = payables.reduce((s, l) => s + Math.abs(l.amount_residual || 0), 0);

  const summary = `## Accounting Balance

| Metric | Amount |
|--------|--------|
| Total Receivables (owed to us) | $${totalReceivable.toFixed(2)} |
| Total Payables (we owe) | $${totalPayable.toFixed(2)} |
| Net Position | $${(totalReceivable - totalPayable).toFixed(2)} |`;

  return { content: [{ type: "text", text: summary }] };
}

async function handleListPayments({ limit = 10 }) {
  const payments = await searchRead(
    "account.payment",
    [["payment_type", "=", "inbound"], ["state", "=", "posted"]],
    ["name", "partner_id", "amount", "date", "currency_id"],
    limit
  );

  if (!payments.length) return { content: [{ type: "text", text: "No recent payments found." }] };

  const rows = payments.map(p =>
    `- **${p.name}** | From: ${p.partner_id ? p.partner_id[1] : "—"} | Amount: ${p.amount} | Date: ${p.date}`
  ).join("\n");

  return { content: [{ type: "text", text: `## Recent Payments (${payments.length})\n\n${rows}` }] };
}

async function handleGetRevenue({ date_from, date_to }) {
  const now = new Date();
  const firstOfMonth = new Date(now.getFullYear(), now.getMonth(), 1).toISOString().split("T")[0];
  const today = now.toISOString().split("T")[0];

  const from = date_from || firstOfMonth;
  const to = date_to || today;

  const lines = await searchRead(
    "account.move.line",
    [
      ["account_id.account_type", "in", ["income", "income_other"]],
      ["date", ">=", from],
      ["date", "<=", to],
      ["move_id.state", "=", "posted"],
    ],
    ["name", "credit", "date", "partner_id"],
    500
  );

  const total = lines.reduce((s, l) => s + (l.credit || 0), 0);

  const summary = `## Revenue Report: ${from} → ${to}

**Total Revenue:** $${total.toFixed(2)}
**Transactions:** ${lines.length}

### Top Transactions
${lines.slice(0, 5).map(l => `- ${l.date} | ${l.partner_id ? l.partner_id[1] : "—"} | $${l.credit.toFixed(2)} | ${l.name}`).join("\n")}`;

  return { content: [{ type: "text", text: summary }] };
}

// ─── MCP Server ───────────────────────────────────────────────────────────────

const server = new Server(
  { name: "odoo-server", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools: TOOLS }));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case "odoo_get_invoices": return await handleGetInvoices(args || {});
      case "odoo_create_invoice": return await handleCreateInvoice(args || {});
      case "odoo_get_customers": return await handleGetCustomers(args || {});
      case "odoo_get_balance": return await handleGetBalance();
      case "odoo_list_payments": return await handleListPayments(args || {});
      case "odoo_get_revenue": return await handleGetRevenue(args || {});
      default:
        return { content: [{ type: "text", text: `Unknown tool: ${name}` }], isError: true };
    }
  } catch (err) {
    return {
      content: [{ type: "text", text: `Error: ${err.message}\n\nMake sure Odoo is running at ${ODOO_URL} and credentials are correct in .env` }],
      isError: true,
    };
  }
});

const transport = new StdioServerTransport();
await server.connect(transport);
