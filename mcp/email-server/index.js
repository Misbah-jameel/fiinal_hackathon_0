/**
 * email-server/index.js
 *
 * Simple Email MCP Server for AI Employee (Silver Tier).
 * Exposes Gmail send/draft/search tools via the Model Context Protocol.
 *
 * Tools exposed:
 *   email_send   - Send an email (requires DRY_RUN=false)
 *   email_draft  - Save a draft to Gmail
 *   email_search - Search Gmail inbox
 *   email_get    - Get a specific email by ID
 *
 * Usage:
 *   node mcp/email-server/index.js
 *
 * MCP registration (~/.config/claude-code/mcp.json):
 *   {
 *     "name": "email",
 *     "command": "node",
 *     "args": ["./mcp/email-server/index.js"],
 *     "env": {
 *       "GMAIL_CREDENTIALS": "./credentials.json",
 *       "GMAIL_TOKEN": "./token.json",
 *       "DRY_RUN": "true"
 *     }
 *   }
 */

const readline = require("readline");
const fs = require("fs");
const path = require("path");
const { google } = require("googleapis");
const { loadAuth, buildRawMessage } = require("./auth");

const DRY_RUN = (process.env.DRY_RUN || "true").toLowerCase() === "true";
const CREDENTIALS_PATH = process.env.GMAIL_CREDENTIALS || "./credentials.json";
const TOKEN_PATH = process.env.GMAIL_TOKEN || "./token.json";

// Lazy-loaded Gmail API client
let _gmail = null;
function getGmail() {
  if (!_gmail) {
    const auth = loadAuth(CREDENTIALS_PATH, TOKEN_PATH);
    _gmail = google.gmail({ version: "v1", auth });
  }
  return _gmail;
}

const MAX_EMAILS_PER_HOUR = 10;
let emailsSentThisHour = 0;
let hourWindowStart = Date.now();

// ---------------------------------------------------------------------------
// MCP Protocol helpers
// ---------------------------------------------------------------------------

function sendResponse(id, result) {
  const msg = JSON.stringify({ jsonrpc: "2.0", id, result });
  process.stdout.write(msg + "\n");
}

function sendError(id, code, message) {
  const msg = JSON.stringify({
    jsonrpc: "2.0",
    id,
    error: { code, message },
  });
  process.stdout.write(msg + "\n");
}

function log(msg) {
  process.stderr.write(`[EmailMCP] ${msg}\n`);
}

// ---------------------------------------------------------------------------
// Rate limiting
// ---------------------------------------------------------------------------

function checkRateLimit() {
  const now = Date.now();
  if (now - hourWindowStart > 3600000) {
    emailsSentThisHour = 0;
    hourWindowStart = now;
  }
  if (emailsSentThisHour >= MAX_EMAILS_PER_HOUR) {
    throw new Error(`Rate limit reached: max ${MAX_EMAILS_PER_HOUR} emails/hour`);
  }
}

// ---------------------------------------------------------------------------
// Tool implementations (stub — wire to real Gmail API in production)
// ---------------------------------------------------------------------------

async function email_send({ to, subject, body, attachment }) {
  checkRateLimit();

  if (DRY_RUN) {
    log(`[DRY RUN] Would send email: to=${to} subject="${subject}"`);
    return {
      success: true,
      dry_run: true,
      message: `[DRY RUN] Email to ${to} — "${subject}" would be sent.`,
    };
  }

  const gmail = getGmail();
  const raw = buildRawMessage({ to, subject, body });

  const res = await gmail.users.messages.send({
    userId: "me",
    requestBody: { raw },
  });

  emailsSentThisHour++;
  log(`Email sent to ${to}: "${subject}" — id=${res.data.id}`);

  return {
    success: true,
    to,
    subject,
    timestamp: new Date().toISOString(),
    message_id: res.data.id,
    thread_id: res.data.threadId,
  };
}

async function email_draft({ to, subject, body }) {
  if (DRY_RUN) {
    log(`[DRY RUN] Would save draft: to=${to} subject="${subject}"`);
    return { success: true, dry_run: true, message: "Draft would be saved." };
  }

  const gmail = getGmail();
  const raw = buildRawMessage({ to, subject, body });

  const res = await gmail.users.drafts.create({
    userId: "me",
    requestBody: { message: { raw } },
  });

  log(`Draft saved: to=${to} subject="${subject}" — draft_id=${res.data.id}`);
  return { success: true, draft_id: res.data.id, to, subject };
}

async function email_search({ query, max_results = 10 }) {
  log(`Search: "${query}" (max ${max_results})`);

  if (DRY_RUN) {
    return {
      success: true,
      dry_run: true,
      results: [],
      message: "[DRY RUN] No real search performed.",
    };
  }

  const gmail = getGmail();
  const listRes = await gmail.users.messages.list({
    userId: "me",
    q: query,
    maxResults: max_results,
  });

  const messages = listRes.data.messages || [];
  const results = await Promise.all(
    messages.map(async (m) => {
      const msg = await gmail.users.messages.get({
        userId: "me",
        id: m.id,
        format: "metadata",
        metadataHeaders: ["Subject", "From", "Date"],
      });
      const headers = {};
      (msg.data.payload.headers || []).forEach((h) => {
        headers[h.name] = h.value;
      });
      return {
        id: m.id,
        subject: headers["Subject"] || "(no subject)",
        from: headers["From"] || "(unknown)",
        date: headers["Date"] || "",
        snippet: msg.data.snippet || "",
      };
    })
  );

  return { success: true, query, count: results.length, results };
}

async function email_get({ message_id }) {
  log(`Get email: ${message_id}`);

  if (DRY_RUN) {
    return { success: true, dry_run: true, message: "[DRY RUN] No real fetch." };
  }

  const gmail = getGmail();
  const res = await gmail.users.messages.get({
    userId: "me",
    id: message_id,
    format: "full",
  });

  const headers = {};
  (res.data.payload.headers || []).forEach((h) => {
    headers[h.name] = h.value;
  });

  // Extract plain-text body
  let body = "(no body)";
  const parts = res.data.payload.parts || [];
  const textPart = parts.find((p) => p.mimeType === "text/plain");
  if (textPart && textPart.body && textPart.body.data) {
    body = Buffer.from(textPart.body.data, "base64").toString("utf8");
  } else if (res.data.payload.body && res.data.payload.body.data) {
    body = Buffer.from(res.data.payload.body.data, "base64").toString("utf8");
  }

  return {
    success: true,
    message_id,
    subject: headers["Subject"] || "(no subject)",
    from: headers["From"] || "(unknown)",
    to: headers["To"] || "",
    date: headers["Date"] || "",
    snippet: res.data.snippet || "",
    body,
  };
}

// ---------------------------------------------------------------------------
// MCP tool registry
// ---------------------------------------------------------------------------

const TOOLS = {
  email_send: {
    description: "Send an email via Gmail. Requires DRY_RUN=false for real sends.",
    inputSchema: {
      type: "object",
      properties: {
        to: { type: "string", description: "Recipient email address" },
        subject: { type: "string", description: "Email subject line" },
        body: { type: "string", description: "Email body (plain text or HTML)" },
        attachment: { type: "string", description: "Optional file path to attach" },
      },
      required: ["to", "subject", "body"],
    },
    handler: email_send,
  },
  email_draft: {
    description: "Save an email as a Gmail draft without sending.",
    inputSchema: {
      type: "object",
      properties: {
        to: { type: "string" },
        subject: { type: "string" },
        body: { type: "string" },
      },
      required: ["to", "subject", "body"],
    },
    handler: email_draft,
  },
  email_search: {
    description: "Search Gmail inbox using Gmail query syntax.",
    inputSchema: {
      type: "object",
      properties: {
        query: { type: "string", description: "Gmail search query, e.g. 'is:unread from:client@example.com'" },
        max_results: { type: "number", description: "Max emails to return (default 10)" },
      },
      required: ["query"],
    },
    handler: email_search,
  },
  email_get: {
    description: "Fetch a specific email by Gmail message ID.",
    inputSchema: {
      type: "object",
      properties: {
        message_id: { type: "string", description: "Gmail message ID" },
      },
      required: ["message_id"],
    },
    handler: email_get,
  },
};

// ---------------------------------------------------------------------------
// MCP request handler
// ---------------------------------------------------------------------------

async function handleRequest(request) {
  const { id, method, params } = request;

  if (method === "initialize") {
    return sendResponse(id, {
      protocolVersion: "2024-11-05",
      capabilities: { tools: {} },
      serverInfo: { name: "email-mcp", version: "1.0.0" },
    });
  }

  if (method === "tools/list") {
    const tools = Object.entries(TOOLS).map(([name, tool]) => ({
      name,
      description: tool.description,
      inputSchema: tool.inputSchema,
    }));
    return sendResponse(id, { tools });
  }

  if (method === "tools/call") {
    const { name, arguments: args } = params;
    const tool = TOOLS[name];

    if (!tool) {
      return sendError(id, -32601, `Unknown tool: ${name}`);
    }

    try {
      const result = await tool.handler(args || {});
      return sendResponse(id, {
        content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
      });
    } catch (err) {
      log(`Tool error (${name}): ${err.message}`);
      return sendError(id, -32000, err.message);
    }
  }

  if (method === "notifications/initialized") {
    return; // No response needed
  }

  sendError(id, -32601, `Method not found: ${method}`);
}

// ---------------------------------------------------------------------------
// STDIO transport (MCP standard)
// ---------------------------------------------------------------------------

log(`Starting (DRY_RUN=${DRY_RUN})`);

const rl = readline.createInterface({ input: process.stdin });

rl.on("line", async (line) => {
  if (!line.trim()) return;
  try {
    const request = JSON.parse(line);
    await handleRequest(request);
  } catch (err) {
    log(`Parse error: ${err.message}`);
  }
});

rl.on("close", () => {
  log("MCP server shutting down.");
  process.exit(0);
});
