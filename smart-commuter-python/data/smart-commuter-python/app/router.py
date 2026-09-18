from .network import GRAPH,BY_CODE,nearby_stations
from . import lines
STREET_FACTOR=1.35

def plan(origin,destination,persona,blocked=None,crowd=None,wet=False):
    blocked=set(blocked or []); crowd=dict(crowd or {})
    walk=lambda m: round(m*STREET_FACTOR*(1.15 if wet else 1)/persona['walkSpeed'])
    starts=nearby_stations(origin,persona['maxWalkM']); ends=nearby_stations(destination,persona['maxWalkM']*1.5)
    if not starts or not ends: return {'ok':False,'reason':'No station within walking distance of one end of this trip.'}
    dist={}; prev={}; q=[]
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

def geometry(journey,origin,destination):
    pts=[[origin['lat'],origin['lon']]]
    for leg in journey['legs']:
        if leg['mode']=='rail':
            a,b=BY_CODE[leg['fromCode']],BY_CODE[leg['toCode']]; pts += [[a['lat'],a['lon']],[b['lat'],b['lon']]]
    pts.append([destination['lat'],destination['lon']]); return pts
