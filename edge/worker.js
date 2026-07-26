// Cloudflare Worker: personalized link previews for synk.money invite links.
//
// WHY: /join and /bill-join are static GitHub Pages — humans get JS
// personalization, but iMessage/WhatsApp/Slack link crawlers don't run JS, so
// every share unfurled as the same generic card. This worker sits ONLY on the
// invite routes (see README for the route config), fetches the static page
// from Pages, and rewrites the <title>/OG tags per-link before it reaches the
// crawler. Humans get the identical page (plus accurate tags).
//
// A text that unfurls as "Toni invited you to split Rent — $1,199.93" is the
// whole growth loop working; that's all this file does.
//
// Same-zone subrequests bypass the worker route (Cloudflare guarantees this),
// so fetch(request) below hits GitHub Pages directly — no loop.

const SUPA = 'https://gswskgvhkfntpyjcdjtd.supabase.co';
// Public client (anon) key — safe to embed by design; the RPC is token-gated.
const ANON = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imdzd3NrZ3Zoa2ZudHB5amNkanRkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzkzMDQ4NjMsImV4cCI6MjA5NDg4MDg2M30.sPE4jFIhd60-KhkdWV8bDdP5I4QkCSOYtE5KENx9fNI';

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const origin = await fetch(request); // same-zone → GitHub Pages, no loop

    let meta = null;
    if (url.pathname.startsWith('/join')) {
      const ref = (url.searchParams.get('ref') || '').trim();
      // Same conservative charset the app validates usernames against.
      if (/^[a-zA-Z0-9_.]{2,30}$/.test(ref)) {
        meta = {
          title: `@${ref} invited you to Synk`,
          desc: `Join @${ref} on Synk — split bills, pool money, and you both get a month of Synk Pro free.`,
        };
      }
    } else if (url.pathname.startsWith('/bill-join')) {
      const t = (url.searchParams.get('t') || '').trim();
      if (/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(t)) {
        meta = await billMeta(t); // null on unknown/deleted bill → generic card
      }
    }
    if (!meta) return origin;

    // HTMLRewriter escapes attribute values — user-titled bills are safe here.
    return new HTMLRewriter()
      .on('title', { element(e) { e.setInnerContent(meta.title); } })
      .on('meta[property="og:title"]', { element(e) { e.setAttribute('content', meta.title); } })
      .on('meta[property="og:description"]', { element(e) { e.setAttribute('content', meta.desc); } })
      .on('meta[name="description"]', { element(e) { e.setAttribute('content', meta.desc); } })
      .transform(origin);
  },
};

async function billMeta(token) {
  try {
    const r = await fetch(`${SUPA}/rest/v1/rpc/get_bill_invite_public_preview`, {
      method: 'POST',
      headers: { apikey: ANON, Authorization: `Bearer ${ANON}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ p_token: token }),
      // Cache identical previews briefly at the edge; bills change rarely.
      cf: { cacheTtl: 300 },
    });
    if (!r.ok) return null;
    const b = await r.json();
    if (!b || !b.title) return null;
    let money = '';
    try {
      money = new Intl.NumberFormat('en-US', { style: 'currency', currency: b.currency || 'USD' })
        .format(Number(b.total || 0));
    } catch { money = `$${Number(b.total || 0).toFixed(2)}`; }
    const who = b.organizerFirst ? `${b.organizerFirst} invited you` : "You're invited";
    return {
      title: `${who} to split ${b.title}`,
      desc: `${b.title} · ${money} · ${b.participantCount || 1} ${b.participantCount === 1 ? 'person' : 'people'} on it — tap to see your share.`,
    };
  } catch {
    return null;
  }
}
