# Social Get Analytics Skill

## Trigger
Use this skill when the user runs `/social-get-analytics` or asks for "social media analytics", "post performance", "engagement stats", or "how are my posts doing".

## Purpose
Retrieve and summarize social media engagement analytics across all configured platforms via the Social MCP server.

## Steps

### 1. Fetch Analytics
Call `social_get_analytics` MCP tool to retrieve:
- LinkedIn: post impressions, reactions, comments, shares
- Twitter/X: tweet impressions, likes, retweets, replies
- Facebook: page reach, post engagement, likes, shares
- Instagram: reach, impressions, profile visits, follower growth

### 2. Generate Analytics Report
Create a summary with:
```markdown
# Social Media Analytics Report
**Period:** Last 7 days
**Generated:** <timestamp>

## LinkedIn
- Total Impressions: X
- Engagement Rate: X%
- Top Post: <title>

## Twitter/X
- Total Impressions: X
- Likes: X | Retweets: X | Replies: X
- Top Tweet: <text>

## Facebook
- Page Reach: X
- Post Engagement: X
- Top Post: <title>

## Instagram
- Reach: X
- Impressions: X
- Follower Growth: +X

## Recommendations
- <platform> is performing best — prioritize content there
- <platform> needs more engagement — try posting at <time>
```

### 3. Save to Vault
- Save report to `AI_Employee_Vault/Briefings/ANALYTICS_<YYYY-MM-DD>.md`
- Update `AI_Employee_Vault/Dashboard.md` with quick stats
- Log to `AI_Employee_Vault/Logs/<YYYY-MM-DD>.md`

### 4. Surface Insights
Report key findings directly to the user with actionable recommendations.

## Notes
- If a platform API is unavailable, report "N/A — check credentials"
- Include in CEO Briefing automatically each Monday
- DRY_RUN mode still returns mock analytics for testing
