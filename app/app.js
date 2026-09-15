// StreamRights demo app.
//
// This implements the PRD in sources/prd-entitlement-playback.md and NOTHING
// ELSE. The licence window fields and the adSupportedOnly flag exist in
// catalogue.json and are deliberately never read here. Tests designed from
// sources/rights-schedule-2026.md are expected to fail against this build.
// See CONFLICTS.md.
//
// The presentation below (posters, hero, player transport) is cosmetic. It must
// never consult windowStart, windowEnd or adSupportedOnly -- a "Coming soon"
// badge would silently repair the very gap this repo exists to expose.

const TIER_ORDER = { Free: 0, Standard: 1, Premium: 2 };

let catalogue = [];
let current = null;

const el = (id) => document.getElementById(id);
const territory = () => el("territory").value;
const tier = () => el("tier").value;

// Deep-link support: ?territory=GB&tier=Premium preselects the controls so a
// test can open a known viewer state directly. Presentation only -- the select
// values remain the single source of truth for every rule below.
function applyDeepLink() {
  const params = new URLSearchParams(window.location.search);
  const setIfValid = (id, value) => {
    if (!value) return;
    const select = el(id);
    const match = [...select.options].find(
      (o) => o.value.toLowerCase() === String(value).toLowerCase()
    );
    if (match) select.value = match.value;
  };
  setIfValid("territory", params.get("territory"));
  setIfValid("tier", params.get("tier"));
}

async function load() {
  const res = await fetch("catalogue.json");
  const data = await res.json();
  catalogue = data.titles;
  applyDeepLink();
  renderBrowse();
}

// R1: only titles licensed for the current territory are listed.
// Note: no window check. That is the point.
function licensedHere(title) {
  return title.territories.includes(territory());
}

// ---------------------------------------------------------------- cosmetics

// Deterministic poster art from the title id, so a title always looks the same
// without shipping any image assets.
function artFor(title) {
  let hash = 0;
  for (const ch of title.id) hash = (hash * 131 + ch.charCodeAt(0)) >>> 0;
  const h = ((hash % 12) * 31 + 12) % 360;   // spread hues across the wheel
  const b = (h + 42) % 360;
  return `linear-gradient(145deg, hsl(${h} 56% 34%), hsl(${b} 50% 15%))`;
}

function initials(name) {
  return name
    .replace(/^The\s+/i, "")
    .split(/\s+/)
    .map((w) => w[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

function synopsisFor(title) {
  return (
    `${title.name} is available to StreamRights viewers in ` +
    `${title.territories.join(", ")} on the ${title.minTier} plan and above.`
  );
}

function paintArt(node, title) {
  node.style.background = artFor(title);
  node.innerHTML = `<span class="glyph">${initials(title.name)}</span>`;
}

function renderHero(visible) {
  const hero = el("hero");
  if (visible.length === 0) {
    hero.hidden = true;
    return;
  }
  const feature = visible[0];
  paintArt(el("hero-art"), feature);
  el("hero-territory").textContent = territory();
  el("hero-name").textContent = feature.name;
  el("hero-rating").textContent = feature.rating;
  el("hero-tier").textContent = `${feature.minTier} plan`;
  el("hero-play").onclick = () => openDetail(feature.id);
  hero.hidden = false;
}

// ------------------------------------------------------------------- views

function renderBrowse() {
  const list = el("catalogue");
  list.innerHTML = "";
  const visible = catalogue.filter(licensedHere);

  visible.forEach((title) => {
    const li = document.createElement("li");
    const button = document.createElement("button");
    button.className = "card";
    button.setAttribute("data-title-id", title.id);

    // The card's accessible name must be exactly the title. The poster glyph and
    // the badges are decoration -- left exposed they make the button announce
    // "HL Harbour Lights 15 STANDARD", which is harder to address by name.
    button.setAttribute("aria-label", title.name);
    // Stable hooks so an agent addresses controls by id rather than by guessing
    // at text or pixels. Presentation only -- no rule below reads them.
    button.setAttribute("data-testid", `title-card-${title.id}`);
    button.setAttribute("data-title-name", title.name);

    const poster = document.createElement("div");
    poster.className = "poster";
    poster.setAttribute("aria-hidden", "true");
    poster.style.background = artFor(title);
    poster.innerHTML = `<span class="glyph">${initials(title.name)}</span>`;

    const body = document.createElement("div");
    body.className = "card-body";

    // The accessible name of the card stays exactly the title name, which is
    // what the designed tests locate by.
    const name = document.createElement("div");
    name.className = "card-name";
    name.textContent = title.name;

    const meta = document.createElement("div");
    meta.className = "card-meta";
    meta.setAttribute("aria-hidden", "true");
    const rating = document.createElement("span");
    rating.className = "pill";
    rating.textContent = title.rating;
    const plan = document.createElement("span");
    plan.className = "pill ghost";
    plan.textContent = title.minTier;
    meta.append(rating, plan);

    body.append(name, meta);
    button.append(poster, body);
    button.addEventListener("click", () => openDetail(title.id));
    li.appendChild(button);
    list.appendChild(li);
  });

  renderHero(visible);
  el("empty-state").hidden = visible.length > 0;
  show("browse-view");
}

// R2: detail page shows name, rating and whether it is playable.
function openDetail(id) {
  current = catalogue.find((t) => t.id === id);
  el("detail-name").textContent = current.name;
  el("detail-rating").textContent = current.rating;
  el("detail-synopsis").textContent = synopsisFor(current);
  paintArt(el("detail-art"), current);

  const verdict = evaluate(current);
  el("detail-availability").textContent = verdict.allowed
    ? "Playable"
    : "Not playable";

  el("block-reason").hidden = true;
  el("upgrade-button").hidden = true;
  show("detail-view");
}

// R3, R4, R5: territory and tier only.
function evaluate(title) {
  if (!title.territories.includes(territory())) {
    return {
      allowed: false,
      ground: "territory",
      message: "This title is not available in your region.",
    };
  }
  if (TIER_ORDER[tier()] < TIER_ORDER[title.minTier]) {
    return {
      allowed: false,
      ground: "tier",
      message: `This title requires the ${title.minTier} plan.`,
      upgradeTo: title.minTier,
    };
  }
  return { allowed: true };
}

function play() {
  const verdict = evaluate(current);
  if (verdict.allowed) {
    el("now-playing").textContent = `Now playing: ${current.name}`;
    paintArt(el("player-art"), current);
    el("player-art").innerHTML = "";
    show("player-view");
    return;
  }
  const reason = el("block-reason");
  reason.textContent = verdict.message;
  reason.hidden = false;

  const upgrade = el("upgrade-button");
  if (verdict.upgradeTo) {
    upgrade.textContent = `Upgrade to ${verdict.upgradeTo}`;
    upgrade.hidden = false;
  }
}

function show(viewId) {
  ["browse-view", "detail-view", "player-view"].forEach((id) => {
    el(id).hidden = id !== viewId;
  });
}

el("play-button").addEventListener("click", play);
el("back-to-browse").addEventListener("click", renderBrowse);
el("stop-button").addEventListener("click", () => openDetail(current.id));

// R6: territory change re-evaluates browse, no sign-in required.
el("territory").addEventListener("change", renderBrowse);
el("tier").addEventListener("change", renderBrowse);

load();
