import os,json
from pathlib import Path
from datetime import datetime,timedelta,timezone
from fastapi import FastAPI,Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from app import personas,lines,router,advice,sources
from app.network import STATIONS,BY_CODE
load_dotenv()
app=FastAPI(title='Today\'s run — Smart Commuter Companion')
ROOT=Path(__file__).parent; PUBLIC=ROOT/'public'
SGT=timezone(timedelta(hours=8))
def arrival_time(hhmm,now):
    h,m=map(int,hhmm.split(':')); target=now.replace(hour=h,minute=m,second=0,microsecond=0)
    return target+timedelta(days=1) if target<=now else target
def shape(j,p):
    return {'legs':j['legs'],'minutes':round(j['seconds']/60),'lowMinutes':round(j['lowSeconds']/60),'highMinutes':round(j['highSeconds']/60),'transfers':j['transfers'],'stops':j['stops'],'linesUsed':[{'id':x,'name':lines.name_of(x),'colour':lines.colour_of(x)} for x in j['linesUsed']],'stationsUsed':j['stationsUsed'],'geometry':router.geometry(j,p['origin'],p['destination']),'railGeometry': router.rail_geometry(j),'accessGeometry': router.access_geometry(),'egressGeometry': router.egress_geometry(),'chinatownEgressGeometry': router.chinatown_egress_geometry(),}
@app.get('/api/personas')
def api_personas(): return {'personas':personas.list_public()}
@app.get('/api/stations')
def api_stations(): return {'stations':STATIONS}
@app.get('/api/scenarios')
def api_scenarios():
    out=[]
    for f in sorted((ROOT/'data'/'replay').glob('*.json')):
        raw=json.loads(f.read_text()); out.append({'id':f.stem,'scenario':raw.get('scenario',f.name),'note':raw.get('note')})
    return {'scenarios':out}
@app.get('/api/brief')
async def api_brief(persona:str='rachel',replay:str|None=None):
    p=personas.get(persona); now=datetime.now(SGT); arrive=arrival_time(p['arriveBy'],now); degraded=[]
    baseline=router.plan(p['origin'],p['destination'],p)
    alerts={'Status':1,'AffectedSegments':[],'Message':[],'simulated':False}
    try: alerts=await sources.train_alerts(replay)
    except Exception as e: degraded.append(f'Train alerts unavailable ({e}).')
    disruption=advice.disruption_for(alerts,baseline.get('stationsUsed',[])); blocked=set(disruption['stations'] if disruption else [])
    crowd={}
    for lid in baseline.get('linesUsed',[]):
        try:
            for row in await sources.crowd_realtime(lines.to_crowd_code(lid)):
                if row.get('Station') and row.get('CrowdLevel'): crowd[row['Station'].upper()]=row['CrowdLevel'].lower()
        except Exception: degraded.append(f'Crowd density for {lid} unavailable.')
    weather_near=None; wet=False
    try:
        w=await sources.nowcast(); a=sources.forecast_near(w,p['origin'])
        if a: weather_near=f"{a['forecast']} in {a['name']}"; wet=sources.is_wet(a['forecast'])
    except Exception: degraded.append('Weather unavailable.')
    lifts=[]
    try:
        used=set(baseline.get('stationsUsed',[])); lifts=[x for x in await sources.lift_maintenance() if str(x.get('StationCode','')).upper() in used]
    except Exception: degraded.append('Lift maintenance unavailable.')
    actual = router.plan(
    p['origin'],
    p['destination'],
    p,
    blocked,
    crowd,
    wet)

    chosen = actual

    board = (
        chosen.get('boarding')
        if chosen.get('ok')
        else baseline.get('boarding'))

    bname = BY_CODE.get(board, {}).get('name', board)

    verdict = advice.decide(
        p,
        baseline,
        chosen,
        arrive,
        now,
        disruption,
        crowd.get(board),
        bname,
        weather_near,
        lifts)   
    return {'ok':True,'generatedAt':now.isoformat(),'simulated':bool(alerts.get('simulated')),'scenario':alerts.get('scenario'),'degraded':degraded,'persona':{k:p[k] for k in ('id','name','summary','complete','arriveBy','usualDeparture','origin','destination')},'verdict':verdict,'baseline':shape(baseline,p),'actual':shape(actual,p) if actual.get('ok') else None,'routeChanged':actual.get('ok') and actual.get('linesUsed')!=baseline.get('linesUsed'),'disruption':disruption,'advisory':advice.latest_message(alerts),'crowd':crowd,'weather':weather_near,'liftIssues':lifts}
@app.get('/')
def root():
    return FileResponse(PUBLIC/'index.html')
app.mount('/',StaticFiles(directory=PUBLIC,html=True),name='public')
