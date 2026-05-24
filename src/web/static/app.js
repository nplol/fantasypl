// NPLOL stats dashboard — vanilla JS, no build step.

// Base URL prefix when served behind a reverse proxy (e.g. /nplol via Caddy).
// Empty string when hit directly on :5000.
const BASE = window.__BASE || "";
const apiUrl = (path) => `${BASE}${path}`;

const $ = (sel) => document.querySelector(sel);

const state = {
  seasons: [],
  season: null,
  leagueId: null,
  teamTags: {},
  siblingGwKeys: {},
};

const TEAM_NAME_KEYS = new Set(["name", "user_name", "team_name"]);
const PILL_CLASS = { YouTube: "pill-youtube", AI: "pill-ai" };

function el(tag, props = {}, children = []) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (k === "class") node.className = v;
    else if (k === "html") node.innerHTML = v;
    else if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
    else node.setAttribute(k, v);
  }
  for (const c of [].concat(children)) {
    if (c == null) continue;
    if (typeof c === "string") node.appendChild(document.createTextNode(c));
    else node.appendChild(c);
  }
  return node;
}

function formatCell(value) {
  if (value == null) return "";
  if (typeof value === "number") {
    if (Number.isInteger(value)) return value.toLocaleString("no-NO");
    return value.toFixed(2);
  }
  if (Array.isArray(value)) {
    return value.length > 12 ? `${value.length} stk` : value.join(", ");
  }
  if (typeof value === "object") {
    if (value.web_name) return value.web_name;
    if (value.name) return value.name;
    return JSON.stringify(value);
  }
  return String(value);
}

function isNumericKey(rows, key) {
  for (const r of rows) {
    const v = r?.[key];
    if (v == null) continue;
    return typeof v === "number";
  }
  return false;
}

function teamTagFor(row) {
  const uid = row?.user_id || row?.id;
  if (!uid) return null;
  return state.teamTags[uid] || null;
}

function renderTeamCell(name, tag) {
  const wrap = el("div", { class: "team-cell" });
  if (tag?.place) {
    wrap.appendChild(el("span", { class: "place-chip" }, `P${tag.place}`));
  }
  wrap.appendChild(el("span", { class: "team-name" }, name == null ? "" : String(name)));
  if (tag?.pills?.length) {
    for (const p of tag.pills) {
      wrap.appendChild(el("span", { class: `pill ${PILL_CLASS[p] || ""}` }, p));
    }
  }
  return wrap;
}

function renderSquad(squad) {
  const wrap = el("div", { class: "squad" });
  if (!Array.isArray(squad) || squad.length === 0) {
    wrap.appendChild(el("span", { class: "text-slate-500 italic text-xs" }, "—"));
    return wrap;
  }
  for (const group of squad) {
    const row = el("div", { class: `squad-row squad-${group.pos.toLowerCase()}` });
    row.appendChild(el("span", { class: "squad-pos" }, group.pos));
    const list = el("span", { class: "squad-players" });
    for (const p of group.players) {
      const tag = el("span", { class: "squad-player" });
      tag.appendChild(el("span", { class: "squad-name" }, p.name));
      if (p.captain) {
        tag.appendChild(el("span", { class: "squad-cap" }, p.captain));
      }
      tag.appendChild(el("span", { class: "squad-points" }, ` ${p.points}`));
      list.appendChild(tag);
    }
    row.appendChild(list);
    wrap.appendChild(row);
  }
  return wrap;
}

function slugFor(section) {
  return (section.method || section.title)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function renderSection(section) {
  const card = el("section", { class: "card", id: slugFor(section) });
  const header = el("div", { class: "card-header" }, [
    el("div", { class: "card-title" }, section.title),
    el("div", { class: "card-subtitle" }, section.subtitle),
  ]);
  if (section.error) {
    header.appendChild(el("span", { class: "error-pill" }, section.error));
  }
  card.appendChild(header);

  const body = el("div", { class: "card-body" });

  if (!section.rows || section.rows.length === 0 || section.columns.length === 0) {
    body.appendChild(el("div", { class: "text-slate-500 text-xs italic px-3 py-4" }, "(ingen data)"));
    card.appendChild(body);
    return card;
  }

  const table = el("table", { class: "stat-table" });
  const thead = el("thead");
  const headerRow = el("tr");
  for (const col of section.columns) {
    const numeric = isNumericKey(section.rows, col.key);
    headerRow.appendChild(el("th", { class: numeric ? "num" : "" }, col.label));
  }
  thead.appendChild(headerRow);
  table.appendChild(thead);

  const tbody = el("tbody");
  for (let i = 0; i < section.rows.length; i++) {
    const row = section.rows[i];
    const tr = el("tr", { class: i === 0 ? "winner" : "" });
    for (const col of section.columns) {
      const val = row[col.key];
      if (col.key === "squad") {
        const td = el("td", { class: "squad-cell" });
        td.appendChild(renderSquad(val));
        tr.appendChild(td);
        continue;
      }
      if (TEAM_NAME_KEYS.has(col.key)) {
        const td = el("td", { class: "team-cell-td" });
        td.appendChild(renderTeamCell(val, teamTagFor(row)));
        tr.appendChild(td);
        continue;
      }
      const gwKey = state.siblingGwKeys[col.key];
      const gwVal = gwKey ? row[gwKey] : null;
      if (gwVal != null) {
        const numeric = typeof val === "number";
        const td = el("td", { class: numeric ? "num gw-paired" : "gw-paired" });
        td.appendChild(el("span", {}, formatCell(val)));
        td.appendChild(el("span", { class: "gw-badge" }, `GW${gwVal}`));
        tr.appendChild(td);
        continue;
      }
      const numeric = typeof val === "number";
      const isLong = typeof val === "string" && val.length > 40;
      tr.appendChild(
        el("td", { class: [numeric ? "num" : "", isLong ? "multiline" : ""].join(" ").trim() }, formatCell(val))
      );
    }
    tbody.appendChild(tr);
  }
  table.appendChild(tbody);
  body.appendChild(table);
  card.appendChild(body);
  return card;
}

async function loadStats() {
  if (!state.season || !state.leagueId) return;
  $("#loading").classList.remove("hidden");
  $("#error").classList.add("hidden");
  $("#sections").innerHTML = "";

  try {
    const res = await fetch(apiUrl(`/api/stats/${state.season}/${state.leagueId}`));
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`${res.status}: ${text.slice(0, 200)}`);
    }
    const data = await res.json();
    state.teamTags = data.meta.team_tags || {};
    state.siblingGwKeys = data.meta.sibling_gw_keys || {};
    $("#meta").textContent =
      `${data.meta.league_name} · ${data.meta.season} · GW ${data.meta.latest_gameweek}` +
      (data.meta.latest_gameweek_finished ? " (ferdig)" : " (pågående)");
    $("#footer-counts").textContent = `${data.sections.length} statistikker`;

    const root = $("#sections");
    for (const section of data.sections) {
      root.appendChild(renderSection(section));
    }
    renderTOC(data.sections);
  } catch (e) {
    $("#error").classList.remove("hidden");
    $("#error").textContent = `Klarte ikke å laste statistikk: ${e.message}`;
  } finally {
    $("#loading").classList.add("hidden");
  }
}

function setJumpOpen(open) {
  const root = $("#jump-root");
  const toggle = $("#jump-toggle");
  root.classList.toggle("is-open", open);
  toggle.setAttribute("aria-expanded", String(open));
}

function renderTOC(sections) {
  const tocList = $("#toc-list");
  const jumpList = $("#jump-list");
  tocList.innerHTML = "";
  jumpList.innerHTML = "";
  for (const section of sections) {
    const slug = slugFor(section);
    const onJump = (e) => {
      e.preventDefault();
      const target = document.getElementById(slug);
      if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
      history.replaceState(null, "", `#${slug}`);
      setJumpOpen(false);
    };
    tocList.appendChild(
      el("li", {}, [el("a", { href: `#${slug}`, onclick: onJump }, section.title)])
    );
    jumpList.appendChild(
      el("li", {}, [el("a", { href: `#${slug}`, onclick: onJump }, section.title)])
    );
  }
  $("#toc").classList.remove("hidden");
  $("#jump-root").classList.remove("hidden");

  // If the URL had a hash on load, jump there now that sections exist.
  if (location.hash) {
    const target = document.getElementById(location.hash.slice(1));
    if (target) target.scrollIntoView({ behavior: "instant", block: "start" });
  }
}

function wireJumpMenu() {
  const root = $("#jump-root");
  const toggle = $("#jump-toggle");
  const closeBtn = $("#jump-close");

  toggle.addEventListener("click", (e) => {
    e.stopPropagation();
    setJumpOpen(!root.classList.contains("is-open"));
  });

  closeBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    setJumpOpen(false);
  });

  // Click anywhere outside the jump root → close.
  document.addEventListener("click", (e) => {
    if (!root.classList.contains("is-open")) return;
    if (!root.contains(e.target)) setJumpOpen(false);
  });

  // Escape → close.
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") setJumpOpen(false);
  });
}

function populateLeaguePicker() {
  const seasonEntry = state.seasons.find((s) => s.season === state.season);
  const picker = $("#league-picker");
  picker.innerHTML = "";
  if (!seasonEntry) return;
  for (const lg of seasonEntry.leagues) {
    const opt = el("option", { value: lg.league_id }, `${lg.name} (${lg.league_id})`);
    picker.appendChild(opt);
  }
  state.leagueId = seasonEntry.leagues[0].league_id;
  picker.value = state.leagueId;
}

async function init() {
  const res = await fetch(apiUrl("/api/seasons"));
  state.seasons = await res.json();
  if (state.seasons.length === 0) {
    $("#loading").classList.add("hidden");
    $("#error").classList.remove("hidden");
    $("#error").textContent = "Ingen data funnet i src/data/. Kjør fetch_league.py først.";
    return;
  }

  const picker = $("#season-picker");
  for (const s of state.seasons) {
    picker.appendChild(el("option", { value: s.season }, s.season));
  }
  // Default to the most recent season.
  state.season = state.seasons[state.seasons.length - 1].season;
  picker.value = state.season;
  populateLeaguePicker();

  picker.addEventListener("change", () => {
    state.season = picker.value;
    populateLeaguePicker();
    loadStats();
  });
  $("#league-picker").addEventListener("change", (e) => {
    state.leagueId = Number(e.target.value);
    loadStats();
  });

  wireJumpMenu();
  await loadStats();
}

init();
