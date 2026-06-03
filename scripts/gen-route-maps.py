#!/usr/bin/env python3
"""
gen-route-maps.py — Sinh ảnh bản đồ tuyến (route map) cho từng cung.
Method: Leaflet (CartoDB light tiles) + Catmull-Rom spline + declutter marker,
        render qua Chrome headless --screenshot (giống map-proto/cung-a-map).
Nguồn route + điểm dừng: kml/cung-chi-tiet/{slug}.kml
Output: assets/img/maps/{slug}.png  (2000x1520)

Dùng:
  python3 scripts/gen-route-maps.py                 # tất cả slug thiếu
  python3 scripts/gen-route-maps.py theo-dong-ai-nang   # 1 tuyến
"""
import sys, re, json, subprocess, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KML_DIR = ROOT / "kml" / "cung-chi-tiet"
OUT_DIR = ROOT / "assets" / "img" / "maps"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
SCALE = 2          # 1000x760 -> 2000x1520
W, H = 1000, 760
LUNCH_KW = ("trưa", "Trưa", "Lunch", "lunch", "Bữa", "bữa")

def parse_kml(path: Path):
    txt = path.read_text(encoding="utf-8")
    # route: LineString coordinates -> [[lat,lon],...]
    route = []
    m = re.search(r"<LineString>.*?<coordinates>(.*?)</coordinates>", txt, re.S)
    if m:
        for tok in m.group(1).split():
            parts = tok.split(",")
            if len(parts) >= 2:
                lon, lat = float(parts[0]), float(parts[1])
                route.append([lat, lon])
    # marks: Placemark có <Point>
    marks = []
    for pm in re.findall(r"<Placemark>(.*?)</Placemark>", txt, re.S):
        if "<Point>" not in pm:
            continue
        nm = re.search(r"<name>(.*?)</name>", pm, re.S)
        cm = re.search(r"<Point>.*?<coordinates>(.*?)</coordinates>", pm, re.S)
        if not cm:
            continue
        name = (nm.group(1).strip() if nm else "")
        name = re.sub(r"&amp;", "&", name)
        name = re.sub(r"^\s*\d+\.\s*", "", name)  # bỏ "N. "
        parts = cm.group(1).strip().split(",")
        lon, lat = float(parts[0]), float(parts[1])
        marks.append({"ll": [lat, lon], "nm": name})
    return route, marks

HTML_TMPL = r"""<!DOCTYPE html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
 html,body{margin:0;padding:0}
 #map{width:%(W)dpx;height:%(H)dpx;background:#FBF7EE}
 .num{background:#0A6A2F;color:#fff;border:2px solid #fff;border-radius:50%%;width:26px;height:26px;
   display:flex;align-items:center;justify-content:center;font:700 13px/1 Arial;box-shadow:0 1px 4px rgba(0,0,0,.35)}
 .num.key{background:#C9912F}
 .leaflet-tile{filter:saturate(.45) brightness(1.07) contrast(.96)}
</style></head><body>
<div id="map"></div>
<script>
 var DATA=%(DATA)s;
 var KEY=%(KEY)d;
 function smooth(pts,seg){seg=seg||18; if(pts.length<3) return pts;
   var P=pts.slice(); P.unshift(pts[0]); P.push(pts[pts.length-1]); var out=[];
   for(var i=1;i<P.length-2;i++){var p0=P[i-1],p1=P[i],p2=P[i+1],p3=P[i+2];
     for(var t=0;t<seg;t++){var u=t/seg,u2=u*u,u3=u2*u;
       var lat=0.5*((2*p1[0])+(-p0[0]+p2[0])*u+(2*p0[0]-5*p1[0]+4*p2[0]-p3[0])*u2+(-p0[0]+3*p1[0]-3*p2[0]+p3[0])*u3);
       var lon=0.5*((2*p1[1])+(-p0[1]+p2[1])*u+(2*p0[1]-5*p1[1]+4*p2[1]-p3[1])*u2+(-p0[1]+3*p1[1]-3*p2[1]+p3[1])*u3);
       out.push([lat,lon]);}}
   out.push(pts[pts.length-1]); return out;}
 function declutter(map,marks,minPx){minPx=minPx||36;
   var pos=marks.map(function(m){return map.latLngToLayerPoint(L.latLng(m.ll));});
   for(var it=0;it<60;it++){var moved=false;
     for(var i=0;i<pos.length;i++)for(var j=i+1;j<pos.length;j++){
       var dx=pos[j].x-pos[i].x,dy=pos[j].y-pos[i].y,d=Math.sqrt(dx*dx+dy*dy)||0.01;
       if(d<minPx){var p=(minPx-d)/2,ux=dx/d,uy=dy/d;pos[i].x-=ux*p;pos[i].y-=uy*p;pos[j].x+=ux*p;pos[j].y+=uy*p;moved=true;}}
     if(!moved)break;}
   return pos.map(function(p){return map.layerPointToLatLng(p);});}
 var map=L.map('map',{zoomControl:false,attributionControl:false});
 L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',{maxZoom:19}).addTo(map);
 var sm=smooth(DATA.route,18);
 L.polyline(sm,{color:'#EBCB86',weight:13,opacity:.4,lineJoin:'round',lineCap:'round'}).addTo(map);
 var line=L.polyline(sm,{color:'#0A6A2F',weight:5.5,opacity:.97,lineJoin:'round',lineCap:'round'}).addTo(map);
 map.fitBounds(line.getBounds().pad(0.14));
 var dl=declutter(map,DATA.marks,36);
 DATA.marks.forEach(function(m,i){var key=(i==KEY),at=dl[i];
   var tp=map.latLngToLayerPoint(L.latLng(m.ll)),dp=map.latLngToLayerPoint(at);
   if(Math.abs(tp.x-dp.x)+Math.abs(tp.y-dp.y)>6){
     L.polyline([m.ll,at],{color:'#0A6A2F',weight:1,opacity:.5,dashArray:'2,2'}).addTo(map);
     L.circleMarker(m.ll,{radius:2,color:'#0A6A2F',fillOpacity:1}).addTo(map);}
   L.marker(at,{icon:L.divIcon({className:'',html:'<div class="num'+(key?' key':'')+'">'+(i+1)+'</div>',iconSize:[26,26],iconAnchor:[13,13]})}).addTo(map);});
</script></body></html>"""

def gen(slug: str) -> bool:
    kml = KML_DIR / f"{slug}.kml"
    if not kml.exists():
        print(f"  [SKIP] không có KML: {slug}"); return False
    route, marks = parse_kml(kml)
    if len(route) < 2 or not marks:
        print(f"  [WARN] {slug}: route={len(route)} marks={len(marks)} — bỏ qua"); return False
    key = -1
    for i, m in enumerate(marks):
        if any(k in m["nm"] for k in LUNCH_KW):
            key = i; break
    data = json.dumps({"route": route, "marks": marks}, ensure_ascii=False)
    html = HTML_TMPL % {"W": W, "H": H, "DATA": data, "KEY": key}
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".html", dir=str(OUT_DIR),
                                     delete=False, encoding="utf-8") as f:
        tmp = Path(f.name); f.write(html)
    out_png = OUT_DIR / f"{slug}.png"
    cmd = [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
           "--no-sandbox", "--default-background-color=FBF7EEff",
           f"--force-device-scale-factor={SCALE}", f"--window-size={W},{H}",
           "--virtual-time-budget=16000", f"--screenshot={out_png}", tmp.as_uri()]
    r = subprocess.run(cmd, capture_output=True, text=True)
    tmp.unlink(missing_ok=True)
    if out_png.exists():
        print(f"  [OK] {slug}: route {len(route)}pt · {len(marks)} stops · key#{key+1 if key>=0 else '-'}")
        return True
    print(f"  [ERR] {slug}: {r.stderr[:200]}"); return False

def main():
    args = sys.argv[1:]
    if args:
        slugs = args
    else:
        slugs = sorted(p.stem for p in KML_DIR.glob("*.kml"))
    print(f"[gen-route-maps] {len(slugs)} tuyến · scale={SCALE} -> {W*SCALE}x{H*SCALE}")
    ok = sum(gen(s) for s in slugs)
    print(f"[gen-route-maps] {ok}/{len(slugs)} OK -> {OUT_DIR}")

if __name__ == "__main__":
    main()
