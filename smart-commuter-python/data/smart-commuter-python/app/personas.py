PERSONAS = {
    "rachel": {
        "id":"rachel","name":"Rachel","summary":"Tampines to Raffles Place, same trip for four years.","complete":True,
        "origin":{"lat":1.35298,"lon":103.94390,"label":"Home, Tampines St 11"},
        "destination":{"lat":1.28440,"lon":103.85180,"label":"Office, Raffles Place"},
        "arriveBy":"08:45","usualDeparture":"07:40","walkSpeed":1.35,"maxWalkM":1000,"bufferSeconds":300,
        "noticeThresholdMin":8,"prefersComfort":False,"avoidsStairs":False,
    },
    "arjun": {
        "id":"arjun","name":"Arjun","summary":"Punggol to one-north, flexible start, hates a crush.","complete":False,
        "origin":{"lat":1.40520,"lon":103.90230,"label":"Home, Punggol Field"},
        "destination":{"lat":1.29940,"lon":103.78730,"label":"Office, one-north"},
        "arriveBy":"10:00","usualDeparture":"08:30","walkSpeed":1.4,"maxWalkM":1500,"bufferSeconds":180,
        "noticeThresholdMin":12,"prefersComfort":True,"avoidsStairs":False,
    },
    "lim": {
        "id":"lim","name":"Mdm Lim","summary":"Bedok to Singapore General Hospital, fortnightly.","complete":False,
        "origin":{"lat":1.32560,"lon":103.92980,"label":"Home, Bedok North Ave 1"},
        "destination":{"lat":1.27930,"lon":103.83570,"label":"Singapore General Hospital"},
        "arriveBy":"10:30","usualDeparture":"09:00","walkSpeed":0.7,"maxWalkM":600,"bufferSeconds":900,
        "noticeThresholdMin":5,"prefersComfort":True,"avoidsStairs":True,
    },
}

def get(persona_id): return PERSONAS.get(persona_id, PERSONAS["rachel"])
def list_public():
    keys=("id","name","summary","complete","arriveBy","usualDeparture")
    return [{k:p[k] for k in keys} for p in PERSONAS.values()]
