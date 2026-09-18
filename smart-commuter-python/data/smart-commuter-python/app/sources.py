import os,json,asyncio,time
from pathlib import Path
import httpx
DATAMALL='https://datamall2.mytransport.sg/ltaodataservice'; WEATHER='https://api-open.data.gov.sg/v2/real-time/api'
REPLAY=Path(__file__).resolve().parents[1]/'data'/'replay'; CACHE={}
def cached(k):
    x=CACHE.get(k); return x[1] if x and x[0]>time.time() else None
def put(k,v,ttl): CACHE[k]=(time.time()+ttl,v); return v
async def get_json(url,headers=None):
    timeout=float(os.getenv('UPSTREAM_TIMEOUT_MS','4000'))/1000
    async with httpx.AsyncClient(timeout=timeout) as c:
        r=await c.get(url,headers=headers); r.raise_for_status(); return r.json()
async def datamall(endpoint,query='',ttl=30):
    k=f'{endpoint}{query}'; hit=cached(k)
    if hit is not None: return hit
    key=os.getenv('LTA_ACCOUNT_KEY')
    if not key: raise RuntimeError('LTA_ACCOUNT_KEY is not set. Copy .env.example to .env and add your DataMall key.')
    return put(k,await get_json(f'{DATAMALL}/{endpoint}{query}',{'AccountKey':key,'accept':'application/json'}),ttl)
async def train_alerts(replay=None):
    if replay:
        f=REPLAY/f'{Path(replay).name}.json'
        if not f.exists(): raise FileNotFoundError(f'No replay scenario named {replay}.')
        raw=json.loads(f.read_text()); v=dict(raw.get('value',raw)); v.update(simulated=True,scenario=raw.get('scenario',replay)); return v
    b=await datamall('TrainServiceAlerts'); v=dict(b.get('value',{})); v['simulated']=False; return v
async def crowd_realtime(code): return (await datamall('PCDRealTime',f'?TrainLine={code}',300)).get('value',[])
async def lift_maintenance(): return (await datamall('v2/FacilitiesMaintenance','',600)).get('value',[])
async def nowcast():
    b=await get_json(f'{WEATHER}/two-hr-forecast'); data=b.get('data',{}); rec=(data.get('items') or data.get('records') or [{}])[0]
    forecasts=rec.get('forecasts',[]); areas=[]
    for a in data.get('area_metadata',[]):
        f=next((x for x in forecasts if x.get('area')==a.get('name')),{}); loc=a.get('label_location',{})
        areas.append({'name':a.get('name'),'lat':loc.get('latitude'),'lon':loc.get('longitude'),'forecast':f.get('forecast')})
    return {'areas':areas}
def forecast_near(weather,p):
    vals=[a for a in weather.get('areas',[]) if isinstance(a.get('lat'),(int,float)) and a.get('forecast')]
    return min(vals,key=lambda a:(a['lat']-p['lat'])**2+(a['lon']-p['lon'])**2,default=None)
def is_wet(t): return any(x in (t or '').lower() for x in ('rain','shower','thunder'))
