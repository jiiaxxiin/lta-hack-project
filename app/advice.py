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
def decide(
    persona,
    baseline,
    actual,
    arrive_by,
    now,
    disruption=None,
    crowd_at_boarding=None,
    boarding_name='',
    weather_near=None,
    lift_issues=None
):
    lift_issues = lift_issues or []
    because = []
    level = 'clear'
    action = None

    baseline_ok = baseline.get('ok', False)
    actual_ok = actual.get('ok', False)

    # ------------------------------------------------------------
    # CASE 1: disruption exists but our current router cannot
    # produce a valid alternative journey.
    # ------------------------------------------------------------
    if disruption and not actual_ok:

        level = 'severe'

        line_name = lines.name_of(disruption['lineId'])

        because.append(
            f"{line_name} Line: no service at "
            f"{', '.join(disruption['stations'][:6])}"
            f"{'...' if len(disruption['stations']) > 6 else ''}."
        )

        if disruption.get('freeBus'):
            if disruption['freeBus'] == '*':
                because.append(
                    "Free bus rides island-wide are active."
                )
            else:
                because.append(
                    f"Free bus boarding at {disruption['freeBus']}."
                )

        if disruption.get('freeShuttle'):
            because.append(
                "Free MRT shuttle running."
            )

        if weather_near and any(
            word in weather_near.lower()
            for word in ('rain', 'shower', 'thunder')
        ):
            because.append(
                f"{weather_near} forecast near you."
            )

        # We deliberately do not invent a journey that the
        # current routing engine cannot calculate.
        if disruption.get('freeShuttle'):
            action = (
                "EWL unavailable — use the free MRT shuttle "
                "or free bus service."
            )
        elif disruption.get('freeBus'):
            action = (
                "EWL unavailable — use the activated free bus service."
            )
        else:
            action = (
                "EWL unavailable — no valid rail alternative found."
            )

        return {
            'level': level,
            'interrupt': True,
            'headline': action,
            'action': action,
            'because': because,
            'deltaMinutes': None,
            'leaveBy': None,
            'leaveInMinutes': None,
            'arriveBy': clock(arrive_by)
        }

    # ------------------------------------------------------------
    # From here onwards we have a valid actual journey.
    # ------------------------------------------------------------

    if not actual_ok:
        return {
            'level': 'severe',
            'interrupt': True,
            'headline': 'No valid route available right now.',
            'action': 'Check another transport option.',
            'because': [
                actual.get(
                    'reason',
                    'The journey could not be planned.'
                )
            ],
            'deltaMinutes': None,
            'leaveBy': None,
            'leaveInMinutes': None,
            'arriveBy': clock(arrive_by)
        }

    delta = (
        minutes(actual['seconds'] - baseline['seconds'])
        if baseline_ok
        else 0
    )

    departure = arrive_by - timedelta(
        seconds=actual['highSeconds']
        + persona.get('bufferSeconds', 300)
    )

    slack = round(
        (departure - now).total_seconds() / 60
    )

    # ------------------------------------------------------------
    # Train disruption where a valid reroute DOES exist
    # ------------------------------------------------------------

    if disruption:

        line_name = lines.name_of(disruption['lineId'])

        because.append(
            f"{line_name} Line: no service at "
            f"{', '.join(disruption['stations'][:6])}"
            f"{'...' if len(disruption['stations']) > 6 else ''}."
        )

        reroutes = (
            actual.get('linesUsed')
            != baseline.get('linesUsed')
        )

        if reroutes:
            level = 'severe'

            first = next(
                (
                    leg for leg in actual['legs']
                    if leg['mode'] == 'rail'
                ),
                None
            )

            if first:
                action = (
                    f"Take the {first['lineName']} Line "
                    f"from {first['from']}, "
                    f"+{max(delta, 1)} min."
                )
            else:
                action = "Use today's alternative route."

        else:
            level = 'warn'
            action = (
                f"Same route still works, "
                f"allow +{max(delta, 1)} min."
            )

        if disruption.get('freeBus'):
            if disruption['freeBus'] == '*':
                because.append(
                    "Free bus rides island-wide are active."
                )
            else:
                because.append(
                    f"Free bus boarding at "
                    f"{disruption['freeBus']}."
                )

        if disruption.get('freeShuttle'):
            because.append(
                "Free MRT shuttle running."
            )

    # ------------------------------------------------------------
    # Crowding
    # ------------------------------------------------------------

    if crowd_at_boarding == 'h':

        because.append(
            f"{boarding_name} platform is crowded — "
            "expect to let one train go."
        )

        if level == 'clear':
            level = 'warn'

            if persona['prefersComfort']:
                action = (
                    "Leave 15 min later and the crush clears."
                )
            else:
                action = (
                    "Leave 10 min earlier to keep your arrival time."
                )

    # ------------------------------------------------------------
    # Weather
    # ------------------------------------------------------------

    if weather_near and any(
        word in weather_near.lower()
        for word in ('rain', 'shower', 'thunder')
    ):
        because.append(
            f"{weather_near} forecast near you."
        )

    # ------------------------------------------------------------
    # Lift maintenance
    # ------------------------------------------------------------

    for lift in lift_issues:

        because.append(
            f"{lift.get('StationName', 'Station')}: "
            f"lift {lift.get('LiftID', '')} out of service "
            f"({lift.get('LiftDesc', 'no detail given')})."
        )

        if persona['avoidsStairs']:
            level = 'warn'

            if action is None:
                action = (
                    f"Use {lift.get('StationName', 'this station')} "
                    "only if you can reach another lift."
                )

    # ------------------------------------------------------------
    # Should this commuter actually be interrupted?
    # ------------------------------------------------------------

    threshold = persona.get('noticeThresholdMin', 8)

    interrupt = (
        level == 'severe'
        or (level == 'warn' and delta >= threshold)
        or (level == 'warn' and slack <= 5)
        or (
            persona['prefersComfort']
            and crowd_at_boarding == 'h'
        )
        or (
            persona['avoidsStairs']
            and bool(lift_issues)
        )
    )

    # ------------------------------------------------------------
    # Human-readable headline
    # ------------------------------------------------------------

    if level == 'clear':

        headline = (
            f"Normal run today. "
            f"Leave by {clock(departure)}."
        )

    elif not interrupt:

        if delta > 0:
            headline = (
                f"+{delta} min — not enough "
                "to change anything."
            )
        else:
            headline = (
                "Minor delay — not enough "
                "to change anything."
            )

    else:

        headline = (
            action
            or f"Leave by {clock(departure)}."
        )

    return {
        'level': level,
        'interrupt': interrupt,
        'headline': headline,
        'action': action,
        'because': because,
        'deltaMinutes': delta,
        'leaveBy': clock(departure),
        'leaveInMinutes': slack,
        'arriveBy': clock(arrive_by)
    }
