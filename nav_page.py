import glob, heapq, math, os, re
import xml.etree.ElementTree as ET
from collections import defaultdict
import folium, streamlit as st
from streamlit_folium import st_folium
from streamlit_geolocation import streamlit_geolocation

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gpx")
STEP, LINK, CLUSTER, PASS, MPS = 3.0, 12.0, 25.0, 20.0, 1.3

def hav(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (*a, *b))
    h = math.sin((la2-la1)/2)**2 + math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2
    return 12742000*math.asin(math.sqrt(h))

def pts_of(path):
    r = ET.parse(path).getroot()
    for k in ("trkpt", "rtept"):
        p = [(float(e.get("lat")), float(e.get("lon"))) for e in r.iter() if e.tag.endswith(k)]
        if len(p) > 1: return p
    return []

def thin(p):
    o = [p[0]]
    for x in p[1:-1]:
        if hav(o[-1], x) >= STEP: o.append(x)
    return o + [p[-1]]

def names(stem):
    s = re.sub(r"[\s_]+", " ", stem).strip()
    m = re.split(r"\s+to\s+", s, maxsplit=1, flags=re.I)
    if len(m) != 2: return None
    a, b = re.sub(r"\s+between$", "", m[0], flags=re.I).strip(), m[1].strip()
    return (a, b) if a and b else None

@st.cache_resource(show_spinner="Loading campus paths...")
def graph():
    nodes, fid, tracks, ends = [], [], [], []
    adj = defaultdict(list)
    for fi, f in enumerate(sorted(glob.glob(os.path.join(D, "*.gpx")))):
        try: p = pts_of(f)
        except ET.ParseError: continue
        if len(p) < 2: continue
        p = thin(p); b = len(nodes)
        nodes += p; fid += [fi]*len(p); tracks.append(p)
        for i in range(len(p)-1):
            w = max(hav(p[i], p[i+1]), .01)
            adj[b+i].append((b+i+1, w)); adj[b+i+1].append((b+i, w))
        n = names(os.path.splitext(os.path.basename(f))[0])
        if n: ends += [(n[0], b), (n[1], b+len(p)-1)]
    if not nodes: return None
    cl = LINK/111320
    co = cl/max(math.cos(math.radians(sum(n[0] for n in nodes)/len(nodes))), .01)
    grid = defaultdict(list)
    for i, (la, lo) in enumerate(nodes):
        grid[(math.floor(la/cl), math.floor(lo/co))].append(i)
    for i, (la, lo) in enumerate(nodes):
        gx, gy = math.floor(la/cl), math.floor(lo/co)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for j in grid.get((gx+dx, gy+dy), ()):
                    if j > i and fid[j] != fid[i]:
                        d = hav(nodes[i], nodes[j])
                        if d <= LINK:
                            w = max(d, .01)
                            adj[i].append((j, w)); adj[j].append((i, w))
    places = []
    for lab, nd in ends:
        k = lab.lower().replace(" ", "")
        for pl in places:
            if hav(pl["pos"], nodes[nd]) <= CLUSTER:
                pl["n"].setdefault(k, lab); break
        else:
            places.append({"pos": nodes[nd], "node": nd, "n": {k: lab}})
    used = set()
    for pl in places:
        base = " / ".join(sorted(pl["n"].values(), key=str.lower)); nm, k = base, 2
        while nm in used: nm = f"{base} ({k})"; k += 1
        used.add(nm); pl["name"] = nm
    places.sort(key=lambda p: p["name"].lower())
    return nodes, adj, tracks, places

@st.cache_resource
def buildings():
    fs = glob.glob(os.path.join(D, "*.osm"))
    if not fs: return []
    r = ET.parse(fs[0]).getroot()
    pt = {n.get("id"): (float(n.get("lat")), float(n.get("lon"))) for n in r.iter("node") if n.get("lat")}
    out = []
    for w in r.iter("way"):
        t = {x.get("k"): x.get("v") for x in w.iter("tag")}
        if "building" in t:
            c = [pt[n.get("ref")] for n in w.iter("nd") if n.get("ref") in pt]
            if len(c) > 2: out.append((c, t.get("name", "")))
    return out

def shortest(adj, s, t):
    dist, prev, q = {s: 0.0}, {}, [(0.0, s)]
    while q:
        d, u = heapq.heappop(q)
        if u == t: break
        if d > dist.get(u, 1e18): continue
        for v, w in adj.get(u, ()):
            if d + w < dist.get(v, 1e18):
                dist[v] = d + w; prev[v] = u; heapq.heappush(q, (d + w, v))
    if t not in dist: return None, 0
    p = [t]
    while p[-1] != s: p.append(prev[p[-1]])
    return p[::-1], dist[t]

def render():
    g = graph()
    if not g: st.error("No .gpx files found in the gpx/ folder"); return
    nodes, adj, tracks, places = g
    nm = [p["name"] for p in places]; by = {p["name"]: p for p in places}
    st.subheader("🧭 Campus Map")

    with st.expander("📍 Use my location"):
        loc = streamlit_geolocation()
    user = (loc["latitude"], loc["longitude"]) if loc and loc.get("latitude") else None
    gps = bool(user) and st.toggle("Start from my location", True)
    start = None if gps else st.selectbox("Start", nm, 0)
    dest = st.selectbox("Destination", nm, min(1, len(nm)-1))

    if gps:
        src = min(range(len(nodes)), key=lambda i: hav(user, nodes[i]))
        off = hav(user, nodes[src])
    else:
        src, off = by[start]["node"], 0
    path, dist = shortest(adj, src, by[dest]["node"])
    route = [nodes[i] for i in path] if path else []

    if not path: st.warning("No walking route found between these places.")
    else:
        tot = dist + off
        a, b = st.columns(2)
        a.metric("Distance", f"{tot:.0f} m")
        b.metric("Walking time", f"~{max(1, round(tot/MPS/60))} min")
        via = [pl["name"] for pl in places if pl["name"] not in (start, dest)
               and any(hav(p, pl["pos"]) <= PASS for p in route)]
        if via: st.caption("Passes near: " + " → ".join(via))

    c = route[len(route)//2] if route else user or nodes[0]
    m = folium.Map(location=c, zoom_start=17, max_zoom=21, tiles=None)
    folium.TileLayer("OpenStreetMap", max_zoom=21, max_native_zoom=19).add_to(m)
    for pts, n in buildings():
        folium.Polygon(pts, color="#8b5e3c", weight=1, fill=True, fill_opacity=.35, tooltip=n or None).add_to(m)
    for t in tracks: folium.PolyLine(t, color="#888", weight=3, opacity=.5).add_to(m)
    for pl in places:
        folium.CircleMarker(pl["pos"], radius=5, color="#444", fill=True,
                            fill_color="#ffd54f", fill_opacity=1, tooltip=pl["name"]).add_to(m)
    if route:
        folium.PolyLine(route, color="#1a73e8", weight=7).add_to(m)
        folium.Marker(route[0], tooltip="Start", icon=folium.Icon(color="green")).add_to(m)
        folium.Marker(route[-1], tooltip=dest, icon=folium.Icon(color="red")).add_to(m)
        m.fit_bounds([[min(p[0] for p in route), min(p[1] for p in route)],
                      [max(p[0] for p in route), max(p[1] for p in route)]], padding=(30, 30))
    if user:
        folium.CircleMarker(user, radius=8, color="white", fill=True,
                            fill_color="#1a73e8", fill_opacity=1, tooltip="You").add_to(m)
    st_folium(m, height=420, use_container_width=True, returned_objects=[])