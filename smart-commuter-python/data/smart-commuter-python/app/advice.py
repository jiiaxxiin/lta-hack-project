from datetime import timedelta
from . import lines
def minutes(s): return round(s/60)
def clock(dt): return dt.strftime('%H:%M')
def disruption_for(alerts,station_codes):
    if not alerts or alerts.get('Status')!=2: return None
    used=set(station_codes)
    for seg in alerts.get('AffectedSegments',[]):
        affected=lines.parse_station_list(seg.get('Stations'))
        overlap=[x for x in affected if x in used]
        if not overlap: continue
        ids=lines.from_alert_code(seg.get('Line'))
        fb=lines.parse_station_list(seg.get('FreePublicBus'))
        fs=lines.parse_station_list(seg.get('FreeMRTShuttle'))
        return {'lineId':ids[0] if ids else seg.get('Line'),'lineCode':seg.get('Line'),'direction':seg.get('Direction'),'stations':affected,'overlap':overlap,'freeBus':('*' if fb and fb[0]=='*' else ', '.join(fb) if fb else None),'freeShuttle':bool(fs),'shuttleDirection':None if seg.get('MRTShuttleDirection') in (None,'Both') else seg.get('MRTShuttleDirection')}
    return None
def latest_message(alerts):
    msgs=alerts.get('Message',[]) if alerts else []
    return sorted(msgs,key=lambda x:str(x.get('CreatedDate','')),reverse=True)[0] if msgs else None
def decide(persona,baseline,actual,arrive_by,now,disruption=None,crowd_at_boarding=None,boarding_name='',weather_near=None,lift_issues=None):
    lift_issues=lift_issues or []; because=[]; level='clear'; action=None
    delta=minutes(actual['seconds']-baseline['seconds']) if actual.get('ok') and baseline.get('ok') else 0
    departure=arrive_by-timedelta(seconds=actual['highSeconds']+persona.get('bufferSeconds',300)); slack=round((departure-now).total_seconds()/60)
    if disruption:
        because.append(f"{lines.name_of(disruption['lineId'])} Line: no service at {', '.join(disruption['stations'][:6])}{'…' if len(disruption['stations'])>6 else ''}.")
        reroutes=actual.get('ok') and actual['linesUsed']!=baseline['linesUsed']
        if reroutes:
            level='severe'; first=next(x for x in actual['legs'] if x['mode']=='rail'); action=f"Take the {first['lineName']} Line from {first['from']}, +{max(delta,1)} min."
        else: level='warn'; action=f"Same route still works, allow +{max(delta,1)} min."
        if disruption.get('freeBus'): because.append('Free bus rides island-wide are active.' if disruption['freeBus']=='*' else f"Free bus boarding at {disruption['freeBus']}.")
        if disruption.get('freeShuttle'): because.append('Free MRT shuttle running.')
    if crowd_at_boarding=='h':
        because.append(f"{boarding_name} platform is crowded — expect to let one train go.")
        if level=='clear': level='warn'; action='Leave 15 min later and the crush clears.' if persona['prefersComfort'] else 'Leave 10 min earlier to keep your arrival time.'
    if weather_near and any(w in weather_near.lower() for w in ('rain','shower','thunder')): because.append(f"{weather_near} forecast near you.")
    for lift in lift_issues:
        because.append(f"{lift.get('StationName','Station')}: lift {lift.get('LiftID','')} out of service ({lift.get('LiftDesc','no detail given')}).")
        if persona['avoidsStairs']: level='warn'; action=action or f"Use {lift.get('StationName','this station')} only if you can reach another lift."
    threshold=persona.get('noticeThresholdMin',8)
    interrupt=level=='severe' or (level=='warn' and delta>=threshold) or (level=='warn' and slack<=5) or (persona['prefersComfort'] and crowd_at_boarding=='h') or (persona['avoidsStairs'] and bool(lift_issues))
    headline=(f"Normal run today. Leave by {clock(departure)}." if level=='clear' else (f"{f'+{delta} min' if delta>0 else 'Minor delay'} — not enough to change anything." if not interrupt else action or f"Leave by {clock(departure)}."))
    return {'level':level,'interrupt':interrupt,'headline':headline,'action':action,'because':because,'deltaMinutes':delta,'leaveBy':clock(departure),'leaveInMinutes':slack,'arriveBy':clock(arrive_by)}
