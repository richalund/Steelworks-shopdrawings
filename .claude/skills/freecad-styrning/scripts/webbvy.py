"""3D-vy i webbläsaren: en fristående HTML-fil med modellens glTF inbäddad (three.js från jsDelivr), lager per
delgrupp, klick på en del för positionsnummer, profil, material, längd och vikt, färdiga vyer (iso, plan, fram,
sida) och ljust/mörkt läge. Filen kan mailas till en kund eller läggas upp som en webbsida; den behöver bara nätet
för three.js. Används av `export.py --format html`; `python3 webbvy.py <modell.glb> <ut.html> [--titel ...]` gör
samma sak för en befintlig glb (utan delinfo).

Lager: delarna grupperas efter positionsnumrets bokstäver (b balkar, c pelare, pl plåtar, st stolpar, l liggare och
vinklar, sp spjälor, hl handledare, k konsolplåtar ...); referenskropparna (omgivningen) blir ett eget lager som
ritas genomskinligt.
"""
import os, sys, json, base64, argparse

GRUPPER = {"b": "Balkar", "c": "Pelare", "pl": "Plåtar", "p": "Plåtar", "st": "Stolpar och stubbar", "l": "Liggare och vinklar",
           "sp": "Spjälor", "hl": "Handledare", "k": "Konsolplåtar", "u": "UPE-balkar", "v": "Vangstycken", "s": "Steg",
           "r": "Rundstång", "g": "Glas", "gj": "Gångjärn"}

MALL = r"""<!doctype html>
<html lang="sv"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>__TITEL__</title>
<style>
:root { --bg:#eceff2; --panel:#f8fafb; --fg:#1a2027; --muted:#5a6573; --line:#cfd6de; --scene:#e3e8ed; --accent:#c4561b;
  --f:"Segoe UI",system-ui,-apple-system,sans-serif; --mono:ui-monospace,Menlo,Consolas,monospace; }
@media (prefers-color-scheme: dark) { :root { --bg:#11151a; --panel:#181e24; --fg:#e5e9ed; --muted:#95a1ae; --line:#2a333d;
  --scene:#161c22; --accent:#e57a3c; color-scheme:dark } }
html,body { height:100%; margin:0 }
[hidden] { display:none !important }
body { background:var(--bg); color:var(--fg); font:15px/1.45 var(--f) }
.wrap { padding:16px max(16px,env(safe-area-inset-right)) 24px max(16px,env(safe-area-inset-left)); max-width:1500px; margin:0 auto;
  display:flex; flex-direction:column; gap:14px }
h1 { font-size:clamp(20px,3vw,28px); margin:0 }
.sub { color:var(--muted); font-size:14px; margin:0 }
.main { display:grid; grid-template-columns:minmax(0,1fr) 290px; gap:14px; align-items:start }
@media (max-width:860px) { .main { grid-template-columns:minmax(0,1fr) } }
.viewer { position:relative; height:min(72vh,760px); min-height:360px; background:var(--scene); border:1px solid var(--line);
  border-radius:6px; overflow:hidden }
canvas { display:block; width:100%; height:100%; touch-action:none }
.views { position:absolute; top:10px; left:10px; display:flex; gap:6px; flex-wrap:wrap }
button { font:600 13px var(--f); color:var(--fg); background:var(--panel); border:1px solid var(--line); border-radius:4px;
  padding:5px 10px; cursor:pointer }
button[aria-pressed="true"] { border-color:var(--accent); color:var(--accent) }
button:focus-visible, input:focus-visible { outline:2px solid var(--accent); outline-offset:2px }
.hint { position:absolute; bottom:8px; left:10px; right:10px; font-size:12px; color:var(--muted); pointer-events:none }
.status { position:absolute; inset:0; display:grid; place-items:center; color:var(--muted); font:13px var(--mono) }
aside { display:flex; flex-direction:column; gap:14px; min-width:0 }
.box { background:var(--panel); border:1px solid var(--line); border-radius:6px; padding:12px 14px }
.box h2 { font-size:12px; letter-spacing:.08em; text-transform:uppercase; color:var(--muted); margin:0 0 8px }
.layer { display:grid; grid-template-columns:18px 14px 1fr auto; gap:8px; align-items:center; padding:3px 0; cursor:pointer }
.sw { width:14px; height:14px; border-radius:3px }
.layer em { font:12px var(--mono); color:var(--muted); font-style:normal }
dl { display:grid; grid-template-columns:auto 1fr; gap:3px 12px; margin:0 }
dt { color:var(--muted) } dd { margin:0; font:13px var(--mono); overflow-wrap:anywhere }
.pos { font-size:22px; font-weight:700; color:var(--accent); margin:0 0 6px }
.note { font-size:13px; color:var(--muted); margin:0 }
</style></head><body>
<div class="wrap">
  <h1>__TITEL__</h1>
  <p class="sub">__UNDER__</p>
  <div class="main">
    <div class="viewer" id="viewer"><canvas id="c" aria-label="3D-modell"></canvas>
      <div class="views"><button data-v="iso" aria-pressed="true">Iso</button><button data-v="plan">Plan</button>
        <button data-v="fram">Fram</button><button data-v="sida">Sida</button></div>
      <div class="status" id="status">Laddar modellen …</div>
      <div class="hint">Dra för att rotera · höger/två fingrar panorerar · scrolla/nyp för zoom · klicka på en del</div></div>
    <aside>
      <div class="box"><h2>Lager</h2><div id="layers"></div></div>
      <div class="box" id="info" aria-live="polite"><h2>Vald del</h2><p class="note">Klicka på en del.</p></div>
      <div class="box"><button id="alla">Visa allt</button> <button id="bara" disabled>Bara vald position</button></div>
      <p class="note">__NOT__</p>
    </aside>
  </div>
</div>
<script src="https://cdn.jsdelivr.net/npm/three@0.147.0/build/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.147.0/examples/js/controls/OrbitControls.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.147.0/examples/js/loaders/GLTFLoader.js"></script>
<script>
const GLB = "__GLB__";
const DELAR = __DELAR__, OMGIVNING = __OMG__, GRUPPER = __GRUPPER__;
const FARGER = ["#3f6e9e","#2f8a83","#b08a2e","#6f5aa0","#55606c","#c4561b","#4b8b3b","#a0436a","#3a7fb8","#8a6d3b"];
const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const san = n => THREE.PropertyBinding.sanitizeNodeName(n || "");
const info = {}; DELAR.forEach(d => info[san(d.namn)] = d);
const omg = new Set(OMGIVNING.map(san));
const wrap = document.getElementById("viewer"), canvas = document.getElementById("c");
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true }); renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
const scene = new THREE.Scene(), camera = new THREE.PerspectiveCamera(35, 1, 0.01, 5000);
const controls = new THREE.OrbitControls(camera, canvas); controls.enableDamping = true; controls.screenSpacePanning = true;
scene.add(new THREE.HemisphereLight(0xffffff, 0x8899aa, 0.9));
const sol = new THREE.DirectionalLight(0xffffff, 0.7); sol.position.set(-3, 6, 4); scene.add(sol);
const lager = {}, mats = {}, kanter = [];
const valMat = new THREE.MeshStandardMaterial({ color: css("--accent"), emissive: css("--accent"), emissiveIntensity: 0.35 });
function grupp(namn) {
  if (omg.has(namn)) return "omg";
  const d = info[namn]; const pos = d ? d.pos : namn;
  const m = /^([A-Za-zåäöÅÄÖ]+)/.exec(pos || ""); return m ? m[1].toLowerCase() : "övrigt";
}
function tema() { scene.background = new THREE.Color(css("--scene")); kanter.forEach(m => m.color.set(css("--fg")));
  valMat.color.set(css("--accent")); valMat.emissive.set(css("--accent")); }
matchMedia("(prefers-color-scheme: dark)").addEventListener("change", tema);
let mitt = new THREE.Vector3(), r = 5;
function vy(k) {
  document.querySelectorAll(".views button").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.v === k)));
  const R = r * 1.9; camera.up.set(0, 1, 0);
  if (k === "plan") camera.position.set(mitt.x, mitt.y + R * 1.2, mitt.z + 0.001);
  else if (k === "fram") camera.position.set(mitt.x, mitt.y + R * 0.15, mitt.z + R);
  else if (k === "sida") camera.position.set(mitt.x + R, mitt.y + R * 0.15, mitt.z);
  else camera.position.set(mitt.x + R * 0.6, mitt.y + R * 0.6, mitt.z + R * 0.75);
  controls.target.copy(mitt); controls.update();
}
document.querySelectorAll(".views button").forEach(b => b.addEventListener("click", () => vy(b.dataset.v)));
function storlek() { const w = wrap.clientWidth, h = wrap.clientHeight; renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix(); }
new ResizeObserver(storlek).observe(wrap);
let bara = null, vald = null;
function synlig() { Object.entries(lager).forEach(([g, L]) => L.forEach(o => o.visible = document.getElementById("lg-" + g).checked && (!bara || o.userData.pos === bara))); }
const infoEl = document.getElementById("info"), baraBtn = document.getElementById("bara");
const noder = {};
function valj(o) {
  if (vald) (noder[vald.userData.nod] || [vald]).forEach(m => m.material = m.userData.mat); vald = null; baraBtn.disabled = true;
  if (!o) { infoEl.innerHTML = '<h2>Vald del</h2><p class="note">Klicka på en del.</p>'; return; }
  vald = o; (noder[o.userData.nod] || [o]).forEach(m => m.material = valMat); baraBtn.disabled = false;
  const d = info[o.userData.namn] || { namn: o.userData.namn };
  const rad = (k, v) => v != null && v !== "" ? `<dt>${k}</dt><dd>${v}</dd>` : "";
  infoEl.innerHTML = `<h2>Vald del</h2><p class="pos">${d.pos || d.namn}</p><dl>${rad("Profil", d.profil)}${rad("Material", d.material)}
    ${rad("Längd", d.langd ? Math.round(d.langd) + " mm" : "")}${rad("Vikt", d.vikt != null ? d.vikt.toFixed(1).replace(".", ",") + " kg" : "")}</dl>`;
}
const ray = new THREE.Raycaster(), ptr = new THREE.Vector2(); let ner = null;
canvas.addEventListener("pointerdown", e => ner = [e.clientX, e.clientY]);
canvas.addEventListener("pointerup", e => {
  if (!ner || Math.hypot(e.clientX - ner[0], e.clientY - ner[1]) > 5) return;
  const b = canvas.getBoundingClientRect(); ptr.set((e.clientX - b.left) / b.width * 2 - 1, -(e.clientY - b.top) / b.height * 2 + 1);
  ray.setFromCamera(ptr, camera);
  const t = ray.intersectObjects(Object.entries(lager).filter(([g]) => g !== "omg").flatMap(([, L]) => L).filter(o => o.visible), false)[0];
  valj(t ? t.object : null);
});
baraBtn.addEventListener("click", () => { if (vald) { bara = vald.userData.pos; synlig(); } });
document.getElementById("alla").addEventListener("click", () => { bara = null; synlig(); vy("iso"); });
const bin = atob(GLB), buf = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) buf[i] = bin.charCodeAt(i);
new THREE.GLTFLoader().parse(buf.buffer, "", gltf => {
  const rot = gltf.scene; let fi = 0;
  rot.traverse(o => {
    if (!o.isMesh) return;
    // three.js gör nodnamnen unika (_1, _2) och delar en del i flera meshar: leta uppåt och skala av suffixen
    let n = o, namn = "", nod = o;
    while (n && !namn) { let k = n.name || ""; while (k && !namn) { if (info[k] || omg.has(k)) { namn = k; nod = n; } else if (/_\d+$/.test(k)) k = k.replace(/_\d+$/, ""); else k = ""; } n = n.parent; }
    if (!namn) { n = o; while (n && !n.name) n = n.parent; namn = n ? n.name : ""; nod = n || o; }
    const bas = k => (k || "").replace(/(_\d+)+$/, "");
    while (nod.parent && namn && bas(nod.parent.name) === bas(nod.name) && bas(nod.name)) nod = nod.parent;   // delens nod, inte en yta
    const nodnamn = nod.uuid;
    const g = grupp(namn);
    if (!mats[g]) mats[g] = g === "omg" ? new THREE.MeshStandardMaterial({ color: 0xb9c0c7, transparent: true, opacity: 0.35, depthWrite: false, side: THREE.DoubleSide })
      : new THREE.MeshStandardMaterial({ color: FARGER[fi++ % FARGER.length], metalness: 0.35, roughness: 0.55, side: THREE.DoubleSide });
    o.material = mats[g]; o.userData = { namn, nod: nodnamn, pos: (info[namn] || {}).pos || namn, mat: mats[g] };
    (lager[g] = lager[g] || []).push(o); (noder[nodnamn] = noder[nodnamn] || []).push(o);
    if (g !== "omg") { const km = new THREE.LineBasicMaterial({ color: css("--fg"), transparent: true, opacity: 0.18 }); kanter.push(km);
      o.add(new THREE.LineSegments(new THREE.EdgesGeometry(o.geometry, 35), km)); }
  });
  scene.add(rot);
  const box = new THREE.Box3().setFromObject(rot); box.getCenter(mitt); r = box.getSize(new THREE.Vector3()).length() / 2;
  camera.near = r / 500; camera.far = r * 40; camera.updateProjectionMatrix();
  const el = document.getElementById("layers");
  Object.keys(lager).sort((a, b) => (a === "omg") - (b === "omg") || a.localeCompare(b)).forEach(g => {
    const rad = document.createElement("label"); rad.className = "layer"; rad.htmlFor = "lg-" + g;
    const namn = g === "omg" ? "Omgivning" : (GRUPPER[g] ? GRUPPER[g] + " (" + g + ")" : g);
    rad.innerHTML = `<input type="checkbox" id="lg-${g}" checked><span class="sw" style="background:#${mats[g].color.getHexString()}"></span><span>${namn}</span><em>${g === "omg" ? "" : new Set(lager[g].map(o => o.userData.nod)).size}</em>`;
    rad.querySelector("input").addEventListener("change", synlig); el.appendChild(rad);
  });
  tema(); storlek(); vy("iso"); document.getElementById("status").hidden = true;
}, err => { document.getElementById("status").textContent = "Modellen kunde inte laddas."; console.error(err); });
tema(); storlek();
(function loop() { requestAnimationFrame(loop); controls.update(); renderer.render(scene, camera); })();
</script></body></html>
"""


def _esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def skriv(glb, html, titel="3D-modell", underrubrik="", delar=(), omgivning=(), not_=None):
    """Skriv den fristående HTML-filen. delar = [dict(namn=etikett i glb, pos, profil, material, langd, vikt)]."""
    data = base64.b64encode(open(glb, "rb").read()).decode("ascii")
    not_ = not_ or ("Modellen är exporterad ur FreeCAD med freecad-styrning. Mått och detaljer gäller enligt "
                    "ritningarna; 3D-vyn är bara en visualisering.")
    t = (MALL.replace("__TITEL__", _esc(titel)).replace("__UNDER__", _esc(underrubrik)).replace("__NOT__", _esc(not_))
         .replace("__DELAR__", json.dumps(list(delar), ensure_ascii=False)).replace("__OMG__", json.dumps(list(omgivning), ensure_ascii=False))
         .replace("__GRUPPER__", json.dumps(GRUPPER, ensure_ascii=False)).replace("__GLB__", data))
    with open(html, "w", encoding="utf-8") as f:
        f.write(t)
    return html


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("glb")
    ap.add_argument("html")
    ap.add_argument("--titel", default="3D-modell")
    a = ap.parse_args()
    print("HTML:", skriv(a.glb, a.html, a.titel))
