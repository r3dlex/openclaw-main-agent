# Instagram hourly monitoring protocol (Geralt)

## Lists

### List A (Influencers)
- ankes_insta
- stuttgart_blog
- stuttgartmitkind

### List B (Important)
- laurabemsilva
- soubemsilva

### List C (Friends)
- edsonluizvalmorbida
- bernardorachadel
- renan.t.inacio
- joyceandrade
- amaey_or_may_not

## Dynamic updates
- If the user instructs: `add [username] to friends` → append to List C.

## Core operations (hourly)
- Scan profiles and DMs for all users in Lists A/B/C once every hour.

### Influencer protocols (List A)
- Like every new post.
- Historic scan: like older posts if not already liked.
- If a comment on these posts is sent to the user: like the comment.
- Reposting: if high-value content from `stuttgart_blog` or `stuttgartmitkind`, flag for reposting.
- If uncertain about repost value: ask the user.

### Important protocols (List B)
- Prioritize DM checks.
- If a user from List B sends a message: notify user immediately.

### Universal engagement rules (all lists)
- Like any new post.
- If a user sends a DM containing their own post: like the post.
- For every new post or relevant comment: analyze text + visual context; generate concise explanation; draft a friendly reply.
- **Stop sequence:** do not send replies; present explanation + draft; ask for confirmation.

## Output format

Update Found

Source: [Username] ([List Category])

Action Taken: [e.g., Liked Post, Liked Comment]

Summary: [Brief explanation of what the post/message is about]

Proposed Reply: [Drafted text]

Status: Awaiting your approval to send.

## Browser / tabs
- Always use the user’s **regular Google Chrome** logged in as `redlexgilgamesh@gmail.com`.
- Use the OpenClaw **Browser Relay** extension (profile `chrome`).
- Prefer reusing already-open tabs; keep work tabs open.
- **Attach tabs only when needed** (do not require permanent attachment).
