#!/usr/bin/env node
/**
 * Social Media MCP Server — AI Employee Gold Tier
 * -------------------------------------------------
 * Unified MCP server for posting to:
 *   - Facebook Page (via Graph API)
 *   - Instagram Business (via Graph API)
 *
 * Tools:
 *   - social_post_facebook     — post to Facebook Page
 *   - social_post_instagram    — post to Instagram (image required)
 *   - social_get_analytics     — get engagement stats
 *   - social_get_facebook_comments — get Facebook post comments
 *   - social_get_facebook_insights — get Facebook Page insights
 *   - social_delete_facebook_post  — delete a Facebook post
 *
 * All posts go through /Pending_Approval first (dry-run mode by default).
 * Set DRY_RUN=false in .env to post live.
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import fetch from "node-fetch";
import fs from "fs";
import path from "path";

const DRY_RUN = process.env.DRY_RUN !== "false";
const VAULT = process.env.VAULT_PATH || "D:/fiinal_hackathon_0/AI_Employee_Vault";
const PENDING = path.join(VAULT, "Pending_Approval");
const LOGS = path.join(VAULT, "Logs");

// Facebook / Instagram
const FB_TOKEN = process.env.FACEBOOK_ACCESS_TOKEN || "";
const FB_PAGE_ID = process.env.FACEBOOK_PAGE_ID || "";
const IG_TOKEN = process.env.INSTAGRAM_ACCESS_TOKEN || "";
const IG_USER_ID = process.env.INSTAGRAM_USER_ID || "";

const GRAPH_API = "https://graph.facebook.com/v19.0";

// ─── Helpers ──────────────────────────────────────────────────────────────────

function log(message) {
  const today = new Date().toISOString().split("T")[0];
  const logFile = path.join(LOGS, `${today}.md`);
  const ts = new Date().toISOString().replace("T", " ").slice(0, 19);
  const entry = `- [${ts}] [SocialMCP] ${message}\n`;
  try {
    fs.mkdirSync(LOGS, { recursive: true });
    fs.appendFileSync(logFile, entry);
  } catch {}
}

function createApprovalFile(platform, action, content, metadata = {}) {
  const today = new Date().toISOString().split("T")[0];
  const ts = Date.now();
  const filename = `APPROVAL_${platform.toUpperCase()}_POST_${today}_${ts}.md`;
  const filepath = path.join(PENDING, filename);

  const body = `---
type: social_post
platform: ${platform}
action: ${action}
created: ${new Date().toISOString()}
status: pending_approval
---

# ${platform.toUpperCase()} Post — Awaiting Approval

**Action:** ${action}
**Platform:** ${platform}

## Content to Post

\`\`\`
${content}
\`\`\`

## Metadata
${Object.entries(metadata).map(([k, v]) => `- **${k}:** ${v}`).join("\n")}

## Instructions

- Move this file to /Approved/ to post
- Move to /Rejected/ to cancel
- The HITL skill will execute the post once approved
`;

  fs.mkdirSync(PENDING, { recursive: true });
  fs.writeFileSync(filepath, body);
  return filename;
}

async function facebookPost(message) {
  if (DRY_RUN) {
    const filename = createApprovalFile("facebook", "page_post", message);
    return { success: true, dry_run: true, approval_file: filename, message: `[DRY RUN] Facebook post queued → ${filename}` };
  }

  if (!FB_TOKEN || !FB_PAGE_ID) throw new Error("FACEBOOK_ACCESS_TOKEN or FACEBOOK_PAGE_ID not set");

  const res = await fetch(`${GRAPH_API}/${FB_PAGE_ID}/feed`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, access_token: FB_TOKEN }),
  });
  const data = await res.json();
  if (data.error) throw new Error(JSON.stringify(data.error));

  log(`Facebook post: ${data.id}`);
  return { success: true, post_id: data.id };
}

async function instagramPost(caption, image_url) {
  if (!image_url) {
    return { success: false, error: "Instagram requires an image URL. Use social_post_facebook for text-only posts." };
  }

  if (DRY_RUN) {
    const filename = createApprovalFile("instagram", "post", caption, { image_url });
    return { success: true, dry_run: true, approval_file: filename, message: `[DRY RUN] Instagram post queued → ${filename}` };
  }

  if (!IG_TOKEN || !IG_USER_ID) throw new Error("INSTAGRAM_ACCESS_TOKEN or INSTAGRAM_USER_ID not set");

  // Step 1: Create media container
  const createRes = await fetch(`${GRAPH_API}/${IG_USER_ID}/media`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ image_url, caption, access_token: IG_TOKEN }),
  });
  const createData = await createRes.json();
  if (createData.error) throw new Error(JSON.stringify(createData.error));

  // Step 2: Publish
  const publishRes = await fetch(`${GRAPH_API}/${IG_USER_ID}/media_publish`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ creation_id: createData.id, access_token: IG_TOKEN }),
  });
  const publishData = await publishRes.json();
  if (publishData.error) throw new Error(JSON.stringify(publishData.error));

  log(`Instagram post: ${publishData.id}`);
  return { success: true, post_id: publishData.id };
}

async function getFacebookComments(postId, limit = 10) {
  if (!FB_TOKEN || !FB_PAGE_ID) throw new Error("FACEBOOK_ACCESS_TOKEN or FACEBOOK_PAGE_ID not set");

  const res = await fetch(
    `${GRAPH_API}/${postId}/comments?limit=${limit}&access_token=${FB_TOKEN}&fields=from,message,created_time,like_count`,
    { method: "GET" }
  );
  const data = await res.json();
  if (data.error) throw new Error(JSON.stringify(data.error));

  return {
    success: true,
    post_id: postId,
    comment_count: data.data?.length || 0,
    comments: data.data || []
  };
}

async function getFacebookInsights(metricNames = ["page_fan_count", "page_posts_engagement", "page_impressions"]) {
  if (!FB_TOKEN || !FB_PAGE_ID) throw new Error("FACEBOOK_ACCESS_TOKEN or FACEBOOK_PAGE_ID not set");

  const metrics = metricNames.join(",");
  const res = await fetch(
    `${GRAPH_API}/${FB_PAGE_ID}/insights?metric=${metrics}&access_token=${FB_TOKEN}`,
    { method: "GET" }
  );
  const data = await res.json();
  if (data.error) throw new Error(JSON.stringify(data.error));

  const insights = {};
  for (const item of data.data || []) {
    insights[item.name] = {
      value: item.values?.[0]?.value || 0,
      description: item.title
    };
  }

  return {
    success: true,
    page_id: FB_PAGE_ID,
    insights
  };
}

async function deleteFacebookPost(postId) {
  if (!FB_TOKEN || !FB_PAGE_ID) throw new Error("FACEBOOK_ACCESS_TOKEN or FACEBOOK_PAGE_ID not set");

  if (DRY_RUN) {
    const filename = createApprovalFile("facebook", "delete_post", `Delete post ID: ${postId}`, { post_id: postId });
    return { success: true, dry_run: true, approval_file: filename, message: `[DRY RUN] Facebook post deletion queued → ${filename}` };
  }

  const res = await fetch(`${GRAPH_API}/${postId}`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ access_token: FB_TOKEN }),
  });

  // Delete returns empty response on success
  if (res.status !== 200) {
    const data = await res.json();
    if (data.error) throw new Error(JSON.stringify(data.error));
  }

  log(`Facebook post deleted: ${postId}`);
  return { success: true, post_id: postId, deleted: true };
}

// ─── Tools ────────────────────────────────────────────────────────────────────

const TOOLS = [
  {
    name: "social_post_facebook",
    description: "Post a text update to Facebook Page.",
    inputSchema: {
      type: "object",
      required: ["message"],
      properties: {
        message: { type: "string", description: "Post content" },
      },
    },
  },
  {
    name: "social_post_instagram",
    description: "Post an image + caption to Instagram Business account.",
    inputSchema: {
      type: "object",
      required: ["caption", "image_url"],
      properties: {
        caption: { type: "string", description: "Post caption" },
        image_url: { type: "string", description: "Public URL of the image to post" },
      },
    },
  },
  {
    name: "social_get_analytics",
    description: "Get basic engagement analytics for Facebook and Instagram.",
    inputSchema: {
      type: "object",
      properties: {
        platform: { type: "string", enum: ["facebook", "instagram", "all"] },
        limit: { type: "number", description: "Number of recent posts (default 5)" },
      },
    },
  },
  {
    name: "social_get_facebook_comments",
    description: "Get comments for a specific Facebook post.",
    inputSchema: {
      type: "object",
      required: ["post_id"],
      properties: {
        post_id: { type: "string", description: "Facebook post ID" },
        limit: { type: "number", description: "Max comments to retrieve (default 10)" },
      },
    },
  },
  {
    name: "social_get_facebook_insights",
    description: "Get Facebook Page insights and analytics.",
    inputSchema: {
      type: "object",
      properties: {
        metrics: {
          type: "array",
          items: { type: "string", enum: ["page_fan_count", "page_posts_engagement", "page_impressions", "page_reach"] },
          description: "Metrics to retrieve (default: all)"
        },
      },
    },
  },
  {
    name: "social_delete_facebook_post",
    description: "Delete a Facebook post (requires approval).",
    inputSchema: {
      type: "object",
      required: ["post_id"],
      properties: {
        post_id: { type: "string", description: "Facebook post ID to delete" },
      },
    },
  },
];

// ─── Tool Handlers ─────────────────────────────────────────────────────────────

async function handlePostFacebook({ message }) {
  const result = await facebookPost(message);
  return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
}

async function handlePostInstagram({ caption, image_url }) {
  const result = await instagramPost(caption, image_url);
  return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
}

async function handleGetAnalytics({ platform = "all", limit = 5 }) {
  const results = [];

  if ((platform === "facebook" || platform === "all") && FB_TOKEN && FB_PAGE_ID) {
    try {
      const res = await fetch(
        `${GRAPH_API}/${FB_PAGE_ID}?fields=fan_count,talking_about_count&access_token=${FB_TOKEN}`
      );
      const data = await res.json();
      results.push(`**Facebook:** ${data.fan_count || 0} fans | ${data.talking_about_count || 0} talking`);
    } catch (e) {
      results.push(`**Facebook:** Error fetching analytics`);
    }
  }

  if ((platform === "instagram" || platform === "all") && IG_TOKEN && IG_USER_ID) {
    try {
      const res = await fetch(
        `${GRAPH_API}/${IG_USER_ID}?fields=followers_count,media_count&access_token=${IG_TOKEN}`
      );
      const data = await res.json();
      results.push(`**Instagram:** ${data.followers_count || 0} followers | ${data.media_count || 0} posts`);
    } catch (e) {
      results.push(`**Instagram:** Error fetching analytics`);
    }
  }

  return { content: [{ type: "text", text: `## Social Analytics\n\n${results.join("\n") || "No data available — check credentials in .env"}` }] };
}

async function handleGetFacebookComments({ post_id, limit = 10 }) {
  try {
    const result = await getFacebookComments(post_id, limit);
    const formatted = result.comments.map(c =>
      `- **${c.from?.name || 'Unknown'}**: ${c.message || '(no text)'} (${c.like_count || 0} likes)`
    ).join("\n");

    return {
      content: [{
        type: "text",
        text: `## Facebook Post Comments\n\n**Post:** ${post_id}\n**Comments:** ${result.comment_count}\n\n${formatted || "No comments yet"}`
      }]
    };
  } catch (e) {
    return { content: [{ type: "text", text: `Error: ${e.message}` }], isError: true };
  }
}

async function handleGetFacebookInsights({ metrics = ["page_fan_count", "page_posts_engagement", "page_impressions"] }) {
  try {
    const result = await getFacebookInsights(metrics);
    const formatted = Object.entries(result.insights)
      .map(([name, data]) => `- **${name}**: ${data.value} (${data.description})`)
      .join("\n");

    return {
      content: [{
        type: "text",
        text: `## Facebook Page Insights\n\n**Page ID:** ${result.page_id}\n\n${formatted}`
      }]
    };
  } catch (e) {
    return { content: [{ type: "text", text: `Error: ${e.message}` }], isError: true };
  }
}

async function handleDeleteFacebookPost({ post_id }) {
  try {
    const result = await deleteFacebookPost(post_id);
    return { content: [{ type: "text", text: `✅ Facebook post deleted successfully\n\n${JSON.stringify(result, null, 2)}` }] };
  } catch (e) {
    return { content: [{ type: "text", text: `Error: ${e.message}` }], isError: true };
  }
}

// ─── MCP Server ───────────────────────────────────────────────────────────────

const server = new Server(
  { name: "social-server", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools: TOOLS }));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  try {
    switch (name) {
      case "social_post_facebook": return await handlePostFacebook(args || {});
      case "social_post_instagram": return await handlePostInstagram(args || {});
      case "social_get_analytics": return await handleGetAnalytics(args || {});
      case "social_get_facebook_comments": return await handleGetFacebookComments(args || {});
      case "social_get_facebook_insights": return await handleGetFacebookInsights(args || {});
      case "social_delete_facebook_post": return await handleDeleteFacebookPost(args || {});
      default:
        return { content: [{ type: "text", text: `Unknown tool: ${name}` }], isError: true };
    }
  } catch (err) {
    return { content: [{ type: "text", text: `Error: ${err.message}` }], isError: true };
  }
});

const transport = new StdioServerTransport();
await server.connect(transport);
