import math
# Focused east-to-city network for Rachel's complete demo. Coordinates are approximate station centroids.
STATIONS = [
 {"code":"EW2","name":"Tampines","lat":1.3530,"lon":103.9452,"line":"EWL"},
 {"code":"EW3","name":"Simei","lat":1.3432,"lon":103.9533,"line":"EWL"},
 {"code":"EW4","name":"Tanah Merah","lat":1.3273,"lon":103.9465,"line":"EWL"},
 {"code":"EW5","name":"Bedok","lat":1.3240,"lon":103.9300,"line":"EWL"},
 {"code":"EW6","name":"Kembangan","lat":1.3210,"lon":103.9129,"line":"EWL"},
 {"code":"EW7","name":"Eunos","lat":1.3198,"lon":103.9030,"line":"EWL"},
 {"code":"EW8","name":"Paya Lebar","lat":1.3181,"lon":103.8926,"line":"EWL"},
 {"code":"EW9","name":"Aljunied","lat":1.3164,"lon":103.8829,"line":"EWL"},
 {"code":"EW10","name":"Kallang","lat":1.3115,"lon":103.8714,"line":"EWL"},
 {"code":"EW11","name":"Lavender","lat":1.3074,"lon":103.8631,"line":"EWL"},
 {"code":"EW12","name":"Bugis","lat":1.3007,"lon":103.8560,"line":"EWL"},
 {"code":"EW13","name":"City Hall","lat":1.2931,"lon":103.8520,"line":"EWL"},
 {"code":"EW14","name":"Raffles Place","lat":1.2839,"lon":103.8515,"line":"EWL"},
 {"code":"DT32","name":"Tampines","lat":1.3540,"lon":103.9430,"line":"DTL"},
 {"code":"DT31","name":"Tampines West","lat":1.3456,"lon":103.9384,"line":"DTL"},
 {"code":"DT30","name":"Bedok Reservoir","lat":1.3366,"lon":103.9322,"line":"DTL"},
 {"code":"DT29","name":"Bedok North","lat":1.3347,"lon":103.9179,"line":"DTL"},
 {"code":"DT28","name":"Kaki Bukit","lat":1.3349,"lon":103.9082,"line":"DTL"},
 {"code":"DT27","name":"Ubi","lat":1.3299,"lon":103.8992,"line":"DTL"},
 {"code":"DT26","name":"MacPherson","lat":1.3262,"lon":103.8903,"line":"DTL"},
 {"code":"DT25","name":"Mattar","lat":1.3269,"lon":103.8832,"line":"DTL"},
 {"code":"DT24","name":"Geylang Bahru","lat":1.3213,"lon":103.8719,"line":"DTL"},
 {"code":"DT23","name":"Bendemeer","lat":1.3137,"lon":103.8627,"line":"DTL"},
 {"code":"DT22","name":"Jalan Besar","lat":1.3052,"lon":103.8553,"line":"DTL"},
 {"code":"DT21","name":"Bencoolen","lat":1.2989,"lon":103.8504,"line":"DTL"},
 {"code":"DT20","name":"Fort Canning","lat":1.2925,"lon":103.8443,"line":"DTL"},
 {"code":"DT19","name":"Chinatown","lat":1.2844,"lon":103.8436,"line":"DTL"},
]
BY_CODE={s['code']:s for s in STATIONS}
def haversine(a,b):
    R=6371000; p1=math.radians(a['lat']); p2=math.radians(b['lat']); dp=p2-p1; dl=math.radians(b['lon']-a['lon'])
    x=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(x))
def nearby_stations(point,max_m):
    vals=[{"station":s,"metres":haversine(point,s)} for s in STATIONS]
    vals=[x for x in vals if x['metres']<=max_m]
    return sorted(vals,key=lambda x:x['metres'])
GRAPH={s['code']:[] for s in STATIONS}
def add_edge(a,b,line):
    d=haversine(BY_CODE[a],BY_CODE[b]); sec=max(90,round(d/12.5+30))
    GRAPH[a].append({"to":b,"mode":"rail","line":line,"seconds":sec}); GRAPH[b].append({"to":a,"mode":"rail","line":line,"seconds":sec})
def seq(codes,line):
    for a,b in zip(codes,codes[1:]): add_edge(a,b,line)
seq([f"EW{i}" for i in range(2,15)],"EWL")
seq(["DT32","DT31","DT30","DT29","DT28","DT27","DT26","DT25","DT24","DT23","DT22","DT21","DT20","DT19"],"DTL")
# Tampines interchange and city walk from Chinatown to Raffles Place area.
GRAPH['EW2'].append({"to":"DT32","mode":"transfer","seconds":240}); GRAPH['DT32'].append({"to":"EW2","mode":"transfer","seconds":240})
