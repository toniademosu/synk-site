# Personalized invite previews — activation runbook

`worker.js` makes synk.money invite links unfurl personalized in iMessage /
WhatsApp / Slack ("Toni invited you to split Rent — $1,199.93") instead of the
generic card. It requires the site's DNS to sit behind Cloudflare (free plan),
because GitHub Pages can't vary HTML per query string.

Until this runs, links still work and show the branded generic card
(`assets/og-card.png`) — this upgrade is additive, nothing breaks by waiting.

## One-time setup (~20 min + DNS propagation)

1. **Add the site to Cloudflare** (free plan): dash.cloudflare.com → Add a
   domain → `synk.money`. Cloudflare scans and imports existing DNS records.
   VERIFY the import kept: the four GitHub Pages A records
   (185.199.108.153 / 109 / 110 / 111), the `www` CNAME if present, and ALL
   Resend records (MX + TXT for DKIM/SPF on send subdomain) — email breaks if
   those are dropped.
2. **Switch nameservers at Porkbun**: Domain → Nameservers → replace with the
   two Cloudflare gives you. Propagation is usually minutes, up to 24h.
3. **Keep TLS sane**: Cloudflare SSL/TLS mode → **Full** (GitHub Pages serves
   a valid cert for synk.money). Leave the A records **proxied** (orange
   cloud) — the worker only runs on proxied traffic.
4. **Deploy the worker**: Workers & Pages → Create → paste `worker.js`
   (or `npx wrangler deploy edge/worker.js --name synk-invites`).
5. **Add routes** (Worker → Settings → Triggers → Routes):
   - `synk.money/join*`
   - `synk.money/bill-join*`
   Nothing else routes through the worker — the homepage, /reset, and
   `/.well-known/apple-app-site-association` (universal links) are untouched.

## Verify

```sh
# Generic (no params) — unchanged page
curl -s https://synk.money/join | grep og:title

# Personalized referral
curl -s "https://synk.money/join?ref=toni" | grep og:title
#   → <meta property="og:title" content="@toni invited you to Synk">

# Personalized bill (use a real token from a bill's share link)
curl -s "https://synk.money/bill-join?t=<token>" | grep og:title
#   → "Toni invited you to split Rent"
```

Then text yourself a link and watch the preview card. iMessage caches
previews per-URL — test with a fresh token if it looks stale.

## Notes

- The worker calls `get_bill_invite_public_preview` (migration
  `20260726_referral_reward_and_public_preview.sql`, applied) — anon-callable,
  token-gated, returns only title/total/organizer-first-name/count.
- The embedded key is the public anon client key; rotating it in the app means
  updating it here too.
- Universal links (AASA) are unaffected: recipients WITH the app still open
  straight into it and never see this page; the worker only improves the
  preview and the no-app landing.
