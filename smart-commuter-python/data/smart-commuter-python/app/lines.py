import re
LINES = [
 {"id":"EWL","name":"East West","colour":"#009645","alerts":"EWL","crowd":"EWL","prefixes":["EW"]},
 {"id":"CGL","name":"Changi branch","colour":"#009645","alerts":"EWL","crowd":"CGL","prefixes":["CG"]},
 {"id":"NSL","name":"North South","colour":"#D42E12","alerts":"NSL","crowd":"NSL","prefixes":["NS"]},
 {"id":"NEL","name":"North East","colour":"#9900AA","alerts":"NEL","crowd":"NEL","prefixes":["NE"]},
 {"id":"CCL","name":"Circle","colour":"#FA9E0D","alerts":"CCL","crowd":"CCL","prefixes":["CC"]},
 {"id":"CEL","name":"Circle extension","colour":"#FA9E0D","alerts":"CCL","crowd":"CEL","prefixes":["CE"]},
 {"id":"DTL","name":"Downtown","colour":"#005EC4","alerts":"DTL","crowd":"DTL","prefixes":["DT"]},
 {"id":"TEL","name":"Thomson-East Coast","colour":"#9D5B25","alerts":"TEL","crowd":"TEL","prefixes":["TE"]},
 {"id":"BPL","name":"Bukit Panjang LRT","colour":"#748477","alerts":"BPL","crowd":"BPL","prefixes":["BP"]},
 {"id":"STL","name":"Sengkang LRT","colour":"#748477","alerts":"STL","crowd":"SLRT","prefixes":["STC","SE","SW"]},
 {"id":"PTL","name":"Punggol LRT","colour":"#748477","alerts":"PTL","crowd":"PLRT","prefixes":["PTC","PE","PW"]},
]
BY_ID={x['id']:x for x in LINES}
def from_alert_code(code): return [x['id'] for x in LINES if x['alerts']==code]
def to_crowd_code(line_id): return BY_ID.get(line_id,{}).get('crowd')
def colour_of(line_id): return BY_ID.get(line_id,{}).get('colour','#5A6672')
def name_of(line_id): return BY_ID.get(line_id,{}).get('name',line_id)
def parse_station_list(raw):
    if not isinstance(raw,str) or not raw: return []
    if re.search(r'island[\s-]?wide',raw,re.I): return ['*']
    return [s for s in (x.strip().upper() for x in re.split(r'[,;|]',raw)) if re.match(r'^[A-Z]{2,3}\d+$',s)]
