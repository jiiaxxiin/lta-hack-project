import json
import xml.etree.ElementTree as ET
from pathlib import Path
from .network import GRAPH,BY_CODE,nearby_stations
from . import lines
STREET_FACTOR=1.35
from .network import (
    GRAPH,
    BY_CODE,
    nearby_stations,
    STATIONS,
    haversine
)
from . import lines
ROOT = Path(__file__).resolve().parent.parent

EWL_GEOJSON = (
    ROOT
    / "data"
    / "geometry"
    / "ewl.geojson"
)
DTL_GEOJSON = (
    ROOT
    / "data"
    / "geometry"
    / "dtl.geojson"
)
HOME_TO_TAMPINES_GPX = (
    ROOT
    / "data"
    / "geometry"
    / "home_to_tampines.gpx"
)
RAFFLES_TO_OFFICE_GPX = (
    ROOT
    / "data"
    / "geometry"
    / "raffles_to_office.gpx"
)
CHINATOWN_TO_OFFICE_GPX = (
    ROOT
    / "data"
    / "geometry"
    / "chinatown_to_office.gpx"
)


STREET_FACTOR = 1.35
def load_line_geometry(path):
    """
    Load railway geometry from an OSM GeoJSON file.

    GeoJSON:
        [longitude, latitude]

    Leaflet:
        [latitude, longitude]
    """

    if not path.exists():
        return []

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except Exception:
        return []

    linestrings = []

    for feature in data.get("features", []):
        geometry = feature.get("geometry") or {}

        if geometry.get("type") != "LineString":
            continue

        coordinates = geometry.get("coordinates", [])

        if len(coordinates) < 2:
            continue

        points = [
            [lat, lon]
            for lon, lat in coordinates
        ]

        linestrings.append(points)

    return linestrings

def load_ewl_geometry():
    return load_line_geometry(EWL_GEOJSON)


def load_dtl_geometry():
    return load_line_geometry(DTL_GEOJSON)

def load_gpx_geometry(path):
    """
    Read a GPX route and return Leaflet coordinates:
    [latitude, longitude]
    """

    if not path.exists():
        return []

    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except Exception:
        return []

    points = []

    # GPX files normally use a namespace, so {*} allows
    # Python to match trkpt regardless of namespace.
    for point in root.findall(".//{*}trkpt"):
        lat = point.get("lat")
        lon = point.get("lon")

        if lat is None or lon is None:
            continue

        points.append([
            float(lat),
            float(lon)
        ])

    # Some exported GPX files contain route points rather
    # than track points.
    if not points:
        for point in root.findall(".//{*}rtept"):
            lat = point.get("lat")
            lon = point.get("lon")

            if lat is None or lon is None:
                continue

            points.append([
                float(lat),
                float(lon)
            ])

    return points

def access_geometry():
    return load_gpx_geometry(
        HOME_TO_TAMPINES_GPX
    )

def egress_geometry():
    return load_gpx_geometry(
        RAFFLES_TO_OFFICE_GPX
    )
def chinatown_egress_geometry():
    return load_gpx_geometry(
        CHINATOWN_TO_OFFICE_GPX
    )


def nearest_geometry_point(
    linestrings,
    station
):
    best = None

    for line_index, line in enumerate(linestrings):

        for point_index, point in enumerate(line):

            candidate = {
                "lat": point[0],
                "lon": point[1]
            }

            distance = haversine(
                station,
                candidate
            )

            if (
                best is None
                or distance < best["distance"]
            ):
                best = {
                    "line": line_index,
                    "index": point_index,
                    "distance": distance
                }

    return best

def detailed_ewl_segment(
    from_code,
    to_code
):
    linestrings = load_ewl_geometry()

    if not linestrings:
        return []

    start_station = BY_CODE.get(from_code)
    end_station = BY_CODE.get(to_code)

    if not start_station or not end_station:
        return []

    start = nearest_geometry_point(
        linestrings,
        start_station
    )

    end = nearest_geometry_point(
        linestrings,
        end_station
    )

    if not start or not end:
        return []

    # For now both stations must fall on the
    # same exported LineString.
    if start["line"] != end["line"]:
        return []

    line = linestrings[start["line"]]

    a = start["index"]
    b = end["index"]

    if a <= b:
        return line[a:b + 1]

    return list(
        reversed(line[b:a + 1])
    )
def detailed_dtl_segment(from_code, to_code):
    linestrings = load_dtl_geometry()

    if not linestrings:
        return []

    start_station = BY_CODE.get(from_code)
    end_station = BY_CODE.get(to_code)

    if not start_station or not end_station:
        return []

    best_segment = None
    best_score = None

    # Try every LineString separately.
    # We want one that passes close to BOTH stations.
    for line in linestrings:

        if len(line) < 2:
            continue

        start_index = None
        start_distance = None

        end_index = None
        end_distance = None

        for index, point in enumerate(line):

            candidate = {
                "lat": point[0],
                "lon": point[1]
            }

            distance_to_start = haversine(
                start_station,
                candidate
            )

            distance_to_end = haversine(
                end_station,
                candidate
            )

            if (
                start_distance is None
                or distance_to_start < start_distance
            ):
                start_distance = distance_to_start
                start_index = index

            if (
                end_distance is None
                or distance_to_end < end_distance
            ):
                end_distance = distance_to_end
                end_index = index

        if start_index is None or end_index is None:
            continue

        # Lower = better.
        score = start_distance + end_distance

        if best_score is None or score < best_score:

            a = start_index
            b = end_index

            if a <= b:
                segment = line[a:b + 1]
            else:
                segment = list(
                    reversed(line[b:a + 1])
                )

            if len(segment) >= 2:
                best_score = score
                best_segment = segment

    return best_segment or []

def station_sequence(from_code, to_code, line):
    """
    Return every station between from_code and to_code
    on the requested MRT line.
    """

    line_stations = [
        station
        for station in STATIONS
        if station["line"] == line
    ]

    codes = [
        station["code"]
        for station in line_stations
    ]

    if from_code not in codes or to_code not in codes:
        return []

    start = codes.index(from_code)
    end = codes.index(to_code)

    if start <= end:
        return line_stations[start:end + 1]

    return list(
        reversed(line_stations[end:start + 1])
    )

def plan(origin, destination, persona, blocked=None, crowd=None, wet=False):
    blocked = set(blocked or [])
    crowd = dict(crowd or {})

    walk = lambda m: round(
        m * STREET_FACTOR * (1.15 if wet else 1)
        / persona["walkSpeed"]
    )

    starts = nearby_stations(
        origin,
        persona["maxWalkM"] / STREET_FACTOR
    )

    ends = nearby_stations(
        destination,
        persona["maxWalkM"] / STREET_FACTOR
    )

    if not starts or not ends:
        return {
            "ok": False,
            "reason": "No station within walking distance of one end of this trip."
        }

    dist = {}
    prev = {}
    q = []

    for x in starts:
        c=x['station']['code']
        if c in blocked: continue
        cost=walk(x['metres']); dist[c]=cost; prev[c]=(None,{'mode':'access','seconds':cost,'metres':x['metres']}); q.append((cost,c))
    settled=set()
    while q:
        q.sort(); cost,c=q.pop(0)
        if c in settled: continue
        settled.add(c)
        for e in GRAPH.get(c,[]):
            if c in blocked or e['to'] in blocked: continue
            pen=120 if e['mode']=='rail' and crowd.get(e['to'])=='h' else 0
            nxt=cost+e['seconds']+pen
            if nxt < dist.get(e['to'],10**18):
                dist[e['to']]=nxt; prev[e['to']]=(c,{**e,'crowdPenalty':pen}); q.append((nxt,e['to']))
    best=None
    for x in ends:
        c=x['station']['code']
        if c in dist:
            total=dist[c]+walk(x['metres'])
            if best is None or total<best[0]: best=(total,c,x['metres'])
    if not best: return {'ok':False,'reason':'No route to the destination with the current disruptions.'}
    total,end_code,egress=best; chain=[]; cur=end_code
    while cur:
        fr,e=prev[cur]; chain.insert(0,(cur,fr,e)); cur=fr
    boarding=BY_CODE[chain[0][0]]; alighting=BY_CODE[end_code]
    legs=[{'mode':'walk','from':origin['label'],'to':f"{boarding['name']} station",'seconds':chain[0][2]['seconds'],'metres':round(chain[0][2]['metres']*STREET_FACTOR)}]
    ride=None
    for code,fr,e in chain[1:]:
        st=BY_CODE[code]
        if e['mode']=='rail':
            if ride and ride['line']==e['line']:
                ride['to']=st['name']; ride['toCode']=code; ride['seconds']+=e['seconds']+e.get('crowdPenalty',0); ride['stops']+=1
            else:
                if ride: legs.append(ride)
                fst=BY_CODE[fr]; ride={'mode':'rail','line':e['line'],'lineName':lines.name_of(e['line']),'colour':lines.colour_of(e['line']),'from':fst['name'],'fromCode':fr,'to':st['name'],'toCode':code,'seconds':e['seconds']+e.get('crowdPenalty',0),'stops':1}
        else:
            if ride: legs.append(ride); ride=None
            legs.append({'mode':'transfer','from':BY_CODE[fr]['name'],'to':st['name'],'seconds':e['seconds']})
    if ride: legs.append(ride)
    legs.append({'mode':'walk','from':f"{alighting['name']} station",'to':destination['label'],'seconds':walk(egress),'metres':round(egress*STREET_FACTOR)})
    rails=[x for x in legs if x['mode']=='rail']; transfers=sum(x['mode']=='transfer' for x in legs)
    spread=60*len(rails)+45*transfers+(180 if any(crowd.get(x['fromCode'])=='h' for x in rails) else 0)+(60 if wet else 0)
    return {'ok':True,'legs':legs,'seconds':total,'lowSeconds':max(60,total-round(spread*.35)),'highSeconds':total+spread,'transfers':transfers,'stops':sum(x['stops'] for x in rails),'linesUsed':list(dict.fromkeys(x['line'] for x in rails)),'stationsUsed':[c for x in rails for c in (x['fromCode'],x['toCode'])],'boarding':boarding['code'],'alighting':alighting['code']}

def geometry(journey, origin, destination):
    points = []

    # Start at the actual origin
    points.append([
        origin["lat"],
        origin["lon"]
    ])

    for leg in journey["legs"]:

        if leg["mode"] != "rail":
            continue

        stations = station_sequence(
            leg["fromCode"],
            leg["toCode"],
            leg["line"]
        )

        for station in stations:

            point = [
                station["lat"],
                station["lon"]
            ]

            if point not in points:
                points.append(point)

    # Finish at the actual destination
    destination_point = [
        destination["lat"],
        destination["lon"]
    ]

    if destination_point not in points:
        points.append(destination_point)

    return points

def rail_geometry(journey):
    points = []

    for leg in journey["legs"]:

        if leg["mode"] != "rail":
            continue

        # -------------------------
        # Detailed EWL geometry
        # -------------------------
        if leg["line"] == "EWL":
            detailed = detailed_ewl_segment(
                leg["fromCode"],
                leg["toCode"]
            )

            if detailed:
                for point in detailed:
                    if not points or points[-1] != point:
                        points.append(point)

                continue

        # -------------------------
        # Detailed DTL geometry
        # -------------------------
        if leg["line"] == "DTL":
            detailed = detailed_dtl_segment(
                leg["fromCode"],
                leg["toCode"]
            )

            if detailed:
                for point in detailed:
                    if not points or points[-1] != point:
                        points.append(point)

                continue

        # -------------------------
        # Fallback geometry
        # -------------------------
        stations = station_sequence(
            leg["fromCode"],
            leg["toCode"],
            leg["line"]
        )

        for station in stations:
            point = [
                station["lat"],
                station["lon"]
            ]

            if not points or points[-1] != point:
                points.append(point)

    return points
