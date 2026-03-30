/**
 * auth.js — Gmail OAuth2 helper for the Email MCP server.
 *
 * Loads credentials + token from disk and returns an authenticated
 * google.auth.OAuth2 client ready to use with googleapis.
 *
 * Token is refreshed automatically by the googleapis library.
 */

const fs = require("fs");
const { google } = require("googleapis");

/**
 * Load OAuth2 credentials and token from disk.
 * @param {string} credentialsPath  Path to credentials.json (OAuth client secret)
 * @param {string} tokenPath        Path to token.json (saved user token)
 * @returns {google.auth.OAuth2}    Authenticated OAuth2 client
 */
function loadAuth(credentialsPath, tokenPath) {
  if (!fs.existsSync(credentialsPath)) {
    throw new Error(
      `credentials.json not found at: ${credentialsPath}\n` +
      "Download it from Google Cloud Console → APIs & Services → Credentials → OAuth 2.0 Client IDs"
    );
  }

  const raw = JSON.parse(fs.readFileSync(credentialsPath, "utf8"));
  const { client_id, client_secret, redirect_uris } =
    raw.installed || raw.web || raw;

  const oAuth2Client = new google.auth.OAuth2(
    client_id,
    client_secret,
    (redirect_uris || ["urn:ietf:wg:oauth:2.0:oob"])[0]
  );

  if (!fs.existsSync(tokenPath)) {
    throw new Error(
      `token.json not found at: ${tokenPath}\n` +
      "Run Gmail auth first:\n" +
      "  python watchers/gmail_watcher.py --vault ./AI_Employee_Vault --auth"
    );
  }

  const token = JSON.parse(fs.readFileSync(tokenPath, "utf8"));
  oAuth2Client.setCredentials(token);

  // Auto-save refreshed tokens
  oAuth2Client.on("tokens", (newTokens) => {
    if (newTokens.refresh_token) {
      token.refresh_token = newTokens.refresh_token;
    }
    token.access_token = newTokens.access_token;
    token.expiry_date = newTokens.expiry_date;
    fs.writeFileSync(tokenPath, JSON.stringify(token, null, 2));
  });

  return oAuth2Client;
}

/**
 * Build a raw RFC 2822 email message, base64url-encoded for Gmail API.
 */
function buildRawMessage({ to, subject, body, from }) {
  const boundary = `boundary_${Date.now()}`;
  const lines = [
    `From: ${from || "me"}`,
    `To: ${to}`,
    `Subject: ${subject}`,
    `MIME-Version: 1.0`,
    `Content-Type: multipart/alternative; boundary="${boundary}"`,
    ``,
    `--${boundary}`,
    `Content-Type: text/plain; charset="UTF-8"`,
    ``,
    body,
    ``,
    `--${boundary}--`,
  ];
  const message = lines.join("\r\n");
  return Buffer.from(message)
    .toString("base64")
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
}

module.exports = { loadAuth, buildRawMessage };
