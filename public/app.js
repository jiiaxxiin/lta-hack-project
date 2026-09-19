'use strict';

const CACHE_KEY = 'commuter-companion:last-brief';

const state = {
  persona: 'rachel',
  replay: null,
  brief: null,
  map: null,
  layers: []
};

const $ = (id) => document.getElementById(id);

/* ---------------------------------------------------------------- clock */

function tickClock() {
  $('clock').textContent = new Date().toLocaleTimeString('en-SG', {
    hour: '2-digit', minute: '2-digit', hour12: false, timeZone: 'Asia/Singapore'
  });
}
tickClock();
setInterval(tickClock, 20000);

/* ------------------------------------------------------------- fetching */

async function loadBrief() {
  const params = new URLSearchParams({ persona: state.persona });
  if (state.replay) params.set('replay', state.replay);

  try {
    const res = await fetch(`/api/brief?${params}`);
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || 'Could not plan this journey.');
    state.brief = data;
    localStorage.setItem(CACHE_KEY, JSON.stringify({ at: Date.now(), data }));
    render(data, { stale: false });
  } catch (err) {
    // Underground, or the server is unreachable. Show the last plan and say so.
    const cached = readCache();
    if (cached) {
      render(cached.data, { stale: true, ageMinutes: Math.round((Date.now() - cached.at) / 60000) });
    } else {
      renderFailure(err.message);
    }
  }
}

function readCache() {
  try {
    const raw = localStorage.getItem(CACHE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

/* ------------------------------------------------------------ rendering */

function render(brief, { stale, ageMinutes }) {
  const v = brief.verdict;

  $('personaName').textContent = brief.persona.name;
  $('personaTrip').textContent = `${brief.persona.origin.label.split(', ').pop()} to ${brief.persona.destination.label.split(', ').pop()}`;

  const verdict = $('verdict');
  verdict.className = `verdict verdict-${v.level} verdict-change`;
  $('verdictLine').textContent = v.headline;

  $('verdictContext').textContent = stale
    ? `Last checked ${ageMinutes} min ago — no signal`
    : v.interrupt
      ? 'Today is not an ordinary day'
      : 'Nothing you need to act on';

  const timing = [];
  if (v.leaveBy) timing.push(`Leave by ${v.leaveBy}`);
  if (typeof v.leaveInMinutes === 'number') {
    timing.push(v.leaveInMinutes >= 0 ? `in ${v.leaveInMinutes} min` : `${Math.abs(v.leaveInMinutes)} min ago`);
  }
  timing.push(`to be there by ${v.arriveBy}`);
  $('verdictTiming').textContent = timing.join(' · ');

  // Labelling injected data is a scoring requirement, not a nicety.
  const flag = $('simulatedFlag');
  flag.hidden = !brief.simulated;
  if (brief.simulated) flag.textContent = `Simulated disruption — ${brief.scenario}. Not live data.`;

  const degraded = $('degradedFlag');
  degraded.hidden = !(brief.degraded && brief.degraded.length);
  if (!degraded.hidden) degraded.textContent = `Running on partial data: ${brief.degraded.join(' ')}`;

  renderStrip(brief);
  renderCompare(brief);
  renderBecause(brief);
  renderAdvisory(brief);
  renderMap(brief);
}

function renderFailure(message) {
  $('verdict').className = 'verdict verdict-severe';
  $('verdictContext').textContent = 'Cannot plan right now';
  $('verdictLine').textContent = message;
  $('verdictTiming').textContent = 'Start the server with a DataMall key, or pick a replay scenario below.';
}

/**
 * The run strip: every point of your journey as a bead on a coloured line,
 * with the dead section hatched in red. Borrowed from the diagram above the
 * train doors, because that is the picture commuters already read fluently.
 */
function renderStrip(brief) {
  const journey = brief.actual || brief.baseline;
  const cut = new Set(brief.disruption ? brief.disruption.stations : []);
  const inner = document.createElement('div');
  inner.className = 'strip-inner';

  const beads = [];
  for (const leg of journey.legs) {
    if (leg.mode === 'walk') {
  beads.push({
    name: leg.from.replace(/ station$/, ''),
    note: `walk ${Math.round(leg.metres)} m`,
    kind: 'walk',
    icon: beads.length === 0 ? 'home' : null
  });
}
     else if (leg.mode === 'rail') {
      beads.push({
        name: leg.from, note: `${leg.lineName} · ${leg.stops} stop${leg.stops === 1 ? '' : 's'}`,
        colour: leg.colour, code: leg.fromCode
      });
    } else if (leg.mode === 'transfer') {
      beads.push({ name: leg.from, note: 'change here', kind: 'interchange' });
    }
  }
  const last = journey.legs[journey.legs.length - 1];
 beads.push({
  name: last.to.replace(/ station$/, ''),
  note: 'arrive',
  kind: 'end',
  icon: 'office'
});

  for (const bead of beads) {
    const el = document.createElement('div');
    const crowd = bead.code ? brief.crowd[bead.code] : null;
    el.className = [
      'bead',
      bead.kind === 'walk' ? 'bead-walk' : '',
      bead.kind === 'interchange' ? 'bead-interchange' : '',
      bead.code && cut.has(bead.code) ? 'bead-cut' : '',
      crowd ? `bead-crowd-${crowd}` : ''
    ].filter(Boolean).join(' ');
    if (bead.colour) el.style.setProperty('--bead-colour', bead.colour);

    const crowdWord = crowd === 'h' ? 'crowded' : crowd === 'm' ? 'filling up' : null;
    const icon =
  bead.icon === 'home'
    ? `<span class="bead-icon" aria-label="Home">
         <svg viewBox="0 0 24 24" aria-hidden="true">
           <path d="M3 11.5L12 4l9 7.5v8a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/>
         </svg>
       </span>`
    : bead.icon === 'office'
      ? `<span class="bead-icon" aria-label="Office">
           <svg viewBox="0 0 24 24" aria-hidden="true">
             <path d="M5 21V4h10v5h4v12h-5v-4h-4v4zm3-14h2V5H8zm4 0h2V5h-2zM8 11h2V9H8zm4 0h2V9h-2zm-4 4h2v-2H8zm4 0h2v-2h-2zm4-2h1v-2h-1zm0 4h1v-2h-1z"/>
           </svg>
         </span>`
      : '';

el.innerHTML = `
  ${icon}
  <span class="bead-name"></span>
  <span class="bead-note"></span>
`;
    el.querySelector('.bead-name').textContent = bead.name;
    el.querySelector('.bead-note').textContent = crowdWord ? `${bead.note} · ${crowdWord}` : bead.note;
    inner.appendChild(el);
  }

  const strip = $('strip');
  strip.replaceChildren(inner);
}

function renderCompare(brief) {
  const box = $('compare');

  // If today's route could not be calculated because of a
  // disruption, do not pretend the normal journey is still valid.
  if (!brief.actual) {
    box.hidden = false;

    box.innerHTML = `
      <div class="compare-cell">
        <span>Your usual</span>
        <b>${brief.baseline.minutes} min</b>
      </div>

      <div class="compare-delta compare-delta-severe">
        affected
      </div>

      <div class="compare-cell">
        <span>Today</span>
        <b>Route unavailable</b>
        <div class="compare-cell-range">
          Use disruption transport
        </div>
      </div>
    `;

    return;
  }

  box.hidden = false;

  const delta = brief.verdict.deltaMinutes;

  const deltaClass =
    delta <= 0
      ? 'compare-delta-none'
      : delta >= 10
        ? 'compare-delta-severe'
        : '';

  const deltaText =
    delta <= 0
      ? 'same'
      : `+${delta} min`;

  box.innerHTML = `
    <div class="compare-cell">
      <span>Your usual</span>
      <b>${brief.baseline.minutes} min</b>
    </div>

    <div class="compare-delta ${deltaClass}">
      ${deltaText}
    </div>

    <div class="compare-cell">
      <span>
        ${brief.routeChanged ? 'Today, rerouted' : 'Today'}
      </span>

      <b>${brief.actual.minutes} min</b>

      <div class="compare-cell-range">
        likely ${brief.actual.lowMinutes}–${brief.actual.highMinutes} min
      </div>
    </div>
  `;
}

function renderBecause(brief) {
  const list = $('because');
  const reasons = brief.verdict.because.length
    ? brief.verdict.because
    : ['No disruption, no lift closures and no crowding on your line right now.'];

  list.replaceChildren(...reasons.map((text) => {
    const li = document.createElement('li');
    li.textContent = text;
    if (/no service|out of service/i.test(text)) li.className = 'is-cause';
    else if (/crowd|busy/i.test(text)) li.className = 'is-crowd';
    else if (/rain|shower|thunder/i.test(text)) li.className = 'is-weather';
    else if (/free bus|shuttle/i.test(text)) li.className = 'is-help';
    return li;
  }));
}

function renderAdvisory(brief) {
  const box = $('advisoryBox');
  if (!brief.advisory) { box.hidden = true; return; }
  box.hidden = false;
  $('advisoryText').textContent = brief.advisory.Content;
  $('advisoryTime').textContent = `Published ${brief.advisory.CreatedDate}`;
}

/* ----------------------------------------------------------------- map */

function renderMap(brief) {
  if (!state.map) {
    state.map = L.map('map', { zoomControl: false, attributionControl: false });
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18,
      crossOrigin: true
    }).addTo(state.map);
    L.control.zoom({ position: 'bottomright' }).addTo(state.map);
  }

  for (const layer of state.layers) state.map.removeLayer(layer);
  state.layers = [];

  const add = (layer) => { layer.addTo(state.map); state.layers.push(layer); };

  // The usual route, greyed and dashed, so the trade-off is visible.
  if (brief.routeChanged) {

  const baselineGeometry =
    brief.baseline.railGeometry &&
    brief.baseline.railGeometry.length >= 2
      ? brief.baseline.railGeometry
      : brief.baseline.geometry;

  add(L.polyline(baselineGeometry, {
      color: '#8C9AA5', weight: 5, opacity: 0.85, dashArray: '2 9', lineCap: 'round'
    }));
  }


  // Use the new rail-only geometry when available.
  // Fall back to the old geometry so the map never disappears.
  const today = brief.actual || brief.baseline;
const usingDTL =
  today.linesUsed &&
  today.linesUsed.some(line => line.id === 'DTL');
const todayGeometry =
  today.railGeometry && today.railGeometry.length >= 2
    ? today.railGeometry
    : today.geometry;

// Only draw today's blue rail route if a usable
// disrupted-day route actually exists.
if (brief.actual) {

  const routeColour =
    today.linesUsed &&
    today.linesUsed.some(line => line.id === 'DTL')
      ? '#005EC4'
      : '#009645';

  add(L.polyline(todayGeometry, {
    color: routeColour,
    weight: 7,
    opacity: 0.95,
    lineCap: 'round',
    lineJoin: 'round'
  }));
}
// Walking connections:
// Home -> first MRT station
// Last MRT station -> Office

if (today.railGeometry && today.railGeometry.length >= 2) {
  
  const origin = [
    brief.persona.origin.lat,
    brief.persona.origin.lon
  ];

  const destination = [
    brief.persona.destination.lat,
    brief.persona.destination.lon
  ];

  const firstStation = today.railGeometry[0];

  const lastStation =
    today.railGeometry[today.railGeometry.length - 1];


  // Home -> Tampines MRT

  const accessGeometry =
    today.accessGeometry &&
    today.accessGeometry.length >= 2
      ? today.accessGeometry
      : [origin, firstStation];

  add(L.polyline(
    accessGeometry,
    {
      color: '#FF5FAA',
      weight: 4,
      opacity: 0.95,
      dashArray: '4 8',
      lineCap: 'round'
    }
  ));



  // Raffles Place MRT -> Office

  if (
  usingDTL &&
  accessGeometry &&
  accessGeometry.length >= 2 &&
  firstStation
) {
  const stationEntrance =
    accessGeometry[accessGeometry.length - 1];

  add(L.polyline(
    [stationEntrance, firstStation],
    {
      color: '#FF5FAA',
      weight: 4,
      opacity: 0.95,
      dashArray: '2 6',
      lineCap: 'round'
    }
  ));
}
let egressGeometry;

if (
  usingDTL &&
  today.chinatownEgressGeometry &&
  today.chinatownEgressGeometry.length >= 2
) {
  // Disruption route:
  // Chinatown DTL -> Office
  egressGeometry = today.chinatownEgressGeometry;

} else if (
  !usingDTL &&
  today.egressGeometry &&
  today.egressGeometry.length >= 2
) {
  // Normal route:
  // Raffles Place MRT -> Office
  egressGeometry = today.egressGeometry;

} else {
  // Safe fallback
  egressGeometry = [lastStation, destination];
}

  add(L.polyline(
    egressGeometry,
    {
      color: '#FF5FAA',
      weight: 4,
      opacity: 0.95,
      dashArray: '4 8',
      lineCap: 'round'
    }
  ));

}
// Mark the boarding and alighting MRT stations.

if (today.railGeometry && today.railGeometry.length >= 2) {

  const firstStation = today.railGeometry[0];

  const lastStation =
    today.railGeometry[today.railGeometry.length - 1];

  add(L.circleMarker(firstStation, {
    radius: 7,
    color: '#FFFFFF',
    weight: 3,
    fillColor: '#0B57D0',
    fillOpacity: 1
  }).bindTooltip('Tampines MRT'));

  add(L.circleMarker(lastStation, {
    radius: 7,
    color: '#FFFFFF',
    weight: 3,
    fillColor: '#0B57D0',
    fillOpacity: 1
  }).bindTooltip(
  usingDTL ? 'Chinatown MRT' : 'Raffles Place MRT'
));
}
  // The dead section of the baseline, drawn over it in red.
  // Disrupted railway section.
// Follow the actual OSM railway geometry instead of
// drawing a straight line between stations.

if (
  brief.disruption &&
  brief.baseline.railGeometry &&
  brief.baseline.railGeometry.length >= 2
) {

  add(L.polyline(
    brief.baseline.railGeometry,
    {
      color: '#D42E12',
      weight: 7,
      opacity: 0.9,
      dashArray: '10 8',
      lineCap: 'round',
      lineJoin: 'round'
    }
  ));
}

  const ends = [
    { point: brief.persona.origin, label: brief.persona.origin.label },
    { point: brief.persona.destination, label: brief.persona.destination.label }
  ];
  for (const end of ends) {
    add(L.circleMarker([end.point.lat, end.point.lon], {
      radius: 7, color: '#0E1418', weight: 3, fillColor: '#fff', fillOpacity: 1
    }).bindTooltip(end.label));
  }

  state.map.fitBounds(L.latLngBounds(today.geometry), { padding: [28, 28] });
  renderLegend(brief);
}

/** Look up a station's coordinates from the geometry we were given. */
const stationCoords = new Map();
function stationPoint(journey, code) {
  if (stationCoords.has(code)) return stationCoords.get(code);
  return null;
}

async function primeStations() {
  try {
    const res = await fetch('/api/stations');
    const { stations } = await res.json();
    for (const s of stations) stationCoords.set(s.code, [s.lat, s.lon]);
  } catch {
    /* map still draws the route lines without the cut overlay */
  }
}

function renderLegend(brief) {
  const wrap = document.querySelector('.map-wrap');
  let legend = wrap.querySelector('.map-legend');
  if (!legend) {
    legend = document.createElement('p');
    legend.className = 'map-legend';
    wrap.insertBefore(legend, wrap.querySelector('.attribution'));
  }
  const parts = [`<span>${brief.routeChanged ? 'Alternative route' : "Today's route"}</span>`];
  if (brief.routeChanged) parts.unshift(`<span class="legend-usual"><i></i>Your usual route</span>`);
  if (brief.disruption) parts.push(`<span class="legend-cut"><i></i>No train service</span>`);
  legend.innerHTML = parts.join('');
}

/* ------------------------------------------------------------- controls */

async function primePersonas() {
  const res = await fetch('/api/personas');
  const { personas } = await res.json();
  const menu = $('personaMenu');

  menu.replaceChildren(...personas.map((p) => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.setAttribute('role', 'option');
    btn.setAttribute('aria-selected', String(p.id === state.persona));
    btn.innerHTML = `${p.name}${p.complete ? '' : ' (partial)'}<span></span>`;
    btn.querySelector('span').textContent = p.summary;
    btn.addEventListener('click', () => {
      state.persona = p.id;
      menu.hidden = true;
      $('personaButton').setAttribute('aria-expanded', 'false');
      for (const other of menu.querySelectorAll('button')) {
        other.setAttribute('aria-selected', String(other === btn));
      }
      loadBrief();
    });
    return btn;
  }));

  $('personaButton').addEventListener('click', () => {
    const open = menu.hidden;
    menu.hidden = !open;
    $('personaButton').setAttribute('aria-expanded', String(open));
  });
}

async function primeScenarios() {
  const res = await fetch('/api/scenarios');
  const { scenarios } = await res.json();
  const wrap = $('scenarioButtons');

  const buttons = [{ id: null, scenario: 'Live feed' }, ...scenarios];
  wrap.replaceChildren(...buttons.map((s) => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.textContent = s.id ? shortLabel(s.scenario) : 'Live feed';
    btn.title = s.note || s.scenario;
    btn.setAttribute('aria-pressed', String(s.id === state.replay));
    btn.addEventListener('click', () => {
      state.replay = s.id;
      for (const other of wrap.querySelectorAll('button')) {
        other.setAttribute('aria-pressed', String(other === btn));
      }
      loadBrief();
    });
    return btn;
  }));
}

function shortLabel(scenario) {
  return scenario.split(',')[0];
}

/* ----------------------------------------------------------------- boot */

(async function start() {
  await primeStations();
  await primePersonas();
  await primeScenarios();
  await loadBrief();
  setInterval(loadBrief, 60000);
})();
