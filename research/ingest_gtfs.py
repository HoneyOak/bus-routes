#!/usr/bin/env python3
"""Deterministic audit and canonicalization for the supplied GTFS subset.

Usage: python ingest_gtfs.py [--input data/raw] [--output data/processed]
Uses only Python's standard library. Raw inputs are read-only.
"""
from __future__ import annotations
import argparse, csv, hashlib, json
from collections import Counter
from datetime import datetime
from pathlib import Path

FILES = ('agency.txt','routes.txt','trips.txt','stops.txt','stop_times.txt','calendar.txt','feed_info.txt')
REQ = {
 'agency.txt': {'agency_name','agency_url','agency_timezone'},
 'routes.txt': {'route_id','agency_id','route_type'},
 'trips.txt': {'route_id','service_id','trip_id'},
 'stops.txt': {'stop_id','stop_name','stop_lat','stop_lon'},
 'stop_times.txt': {'trip_id','arrival_time','departure_time','stop_id','stop_sequence'},
 'calendar.txt': {'service_id','monday','tuesday','wednesday','thursday','friday','saturday','sunday','start_date','end_date'},
 'feed_info.txt': {'feed_publisher_name','feed_publisher_url','feed_lang','feed_start_date','feed_end_date'} }

def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()

def read(path):
 with path.open('r',encoding='utf-8-sig',newline='') as f:
  r=csv.DictReader(f); headers=r.fieldnames or []
  missing=sorted(REQ[path.name]-set(headers))
  rows=list(r)
 return headers, rows, missing

def dupes(rows,key):
 c=Counter(r.get(key,'') for r in rows); return sorted(k for k,v in c.items() if k and v>1)

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--input',type=Path,default=Path(__file__).parent/'data/raw'); ap.add_argument('--output',type=Path,default=Path(__file__).parent/'data/processed'); a=ap.parse_args()
 a.output.mkdir(parents=True,exist_ok=True)
 data={}; files={}
 stop_time_row_count=0; stop_time_trip_counts=Counter(); stop_time_trip_ids=set(); stop_time_stop_ids=set(); previous_stop_time_key=None; stop_time_duplicate_keys=0
 for name in FILES:
  p=a.input/name
  if not p.is_file(): raise SystemExit(f'Missing required file: {p}')
  if name=='stop_times.txt':
   target=a.output/'stop_times.csv'
   with p.open('r',encoding='utf-8-sig',newline='') as src, target.open('w',encoding='utf-8',newline='') as dst:
    reader=csv.DictReader(src); hdr=reader.fieldnames or []; missing=sorted(REQ[name]-set(hdr))
    writer=csv.DictWriter(dst,fieldnames=hdr,lineterminator='\n'); writer.writeheader()
    for row in reader:
     stop_time_row_count+=1; tid=row.get('trip_id',''); sid=row.get('stop_id','')
     if tid: stop_time_trip_counts[tid]+=1; stop_time_trip_ids.add(tid)
     if sid: stop_time_stop_ids.add(sid)
     key=(tid,row.get('stop_sequence',''))
     if key==previous_stop_time_key: stop_time_duplicate_keys+=1
     previous_stop_time_key=key
     writer.writerow({k:(v.strip() if isinstance(v,str) else v) for k,v in row.items()})
   files[name]={'bytes':p.stat().st_size,'sha256':digest(p),'headers':hdr,'rows':stop_time_row_count,'missing_required_columns':missing}
  else:
   hdr,rows,missing=read(p); data[name]=rows
   files[name]={'bytes':p.stat().st_size,'sha256':digest(p),'headers':hdr,'rows':len(rows),'missing_required_columns':missing}
 def vals(fn,key): return {r.get(key,'') for r in data[fn] if r.get(key,'')}
 agencies=data['agency.txt']; routes=data['routes.txt']; trips=data['trips.txt']; stops=data['stops.txt']; cal=data['calendar.txt']
 agency_ids=vals('agency.txt','agency_id'); route_ids=vals('routes.txt','route_id'); trip_ids=vals('trips.txt','trip_id'); stop_ids=vals('stops.txt','stop_id'); service_ids=vals('calendar.txt','service_id')
 foreign={
  'routes.agency_id_not_in_agency':sorted({r['agency_id'] for r in routes if r.get('agency_id') and r['agency_id'] not in agency_ids}),
  'trips.route_id_not_in_routes':sorted({r['route_id'] for r in trips if r.get('route_id') and r['route_id'] not in route_ids}),
  'trips.service_id_not_in_calendar':sorted({r['service_id'] for r in trips if r.get('service_id') and r['service_id'] not in service_ids}),
  'stop_times.trip_id_not_in_trips':sorted(stop_time_trip_ids-trip_ids),
  'stop_times.stop_id_not_in_stops':sorted(stop_time_stop_ids-stop_ids)}
 coords=[]; bad_coords=[]
 for r in stops:
  try:
   lat,lon=float(r['stop_lat']),float(r['stop_lon'])
   if not(-90<=lat<=90 and -180<=lon<=180): raise ValueError()
   coords.append((lat,lon))
  except (ValueError,KeyError): bad_coords.append(r.get('stop_id',''))
 bounds={'min_lat':min((p[0] for p in coords),default=None),'max_lat':max((p[0] for p in coords),default=None),'min_lon':min((p[1] for p in coords),default=None),'max_lon':max((p[1] for p in coords),default=None)}
 by_route=Counter(r.get('route_id','') for r in trips); route_agency=Counter((r.get('agency_id') or '(blank)') for r in routes)
 agency_routes={}
 for r in routes: agency_routes.setdefault(r.get('agency_id') or '(blank)',set()).add(r.get('route_id',''))
 trip_routes={}
 for r in trips: trip_routes.setdefault(r.get('route_id',''),set()).add(r.get('trip_id',''))
 agency_trips={}
 for r in routes: agency_trips[r.get('agency_id') or '(blank)']=agency_trips.get(r.get('agency_id') or '(blank)',set())|trip_routes.get(r.get('route_id',''),set())
 frequency=Counter(stop_time_trip_counts.values())
 def fmt_date(s):
  try:return datetime.strptime(s,'%Y%m%d').date().isoformat()
  except:return s
 service_dates=[]
 for c in cal:
  active=[i for i,k in enumerate(('monday','tuesday','wednesday','thursday','friday','saturday','sunday')) if c.get(k)=='1']
  days=[]
  for i in active: days.append(('Mon','Tue','Wed','Thu','Fri','Sat','Sun')[i])
  service_dates.append({'service_id':c.get('service_id'),'days':days,'start_date':fmt_date(c.get('start_date','')),'end_date':fmt_date(c.get('end_date',''))})
 report={'files':files,'counts':{'agencies':len(agencies),'routes':len(routes),'unique_route_ids':len(route_ids),'trips':len(trips),'unique_trip_ids':len(trip_ids),'stops':len(stops),'unique_stop_ids':len(stop_ids),'stop_time_rows':stop_time_row_count,'stop_time_trips_with_rows':len(stop_time_trip_counts),'calendar_services':len(cal)},'duplicates':{'agency_id':dupes(agencies,'agency_id'),'route_id':dupes(routes,'route_id'),'trip_id':dupes(trips,'trip_id'),'stop_id':dupes(stops,'stop_id'),'calendar.service_id':dupes(cal,'service_id'),'stop_times(trip_id,stop_sequence)_duplicate_rows':stop_time_duplicate_keys},'foreign_key_orphans':{k:{'distinct_ids':len(v),'sample':v[:20]} for k,v in foreign.items()},'geography':{'valid_coordinate_rows':len(coords),'invalid_coordinate_stop_ids':bad_coords[:30],'invalid_coordinate_count':len(bad_coords),'bounds_wgs84':bounds},'agencies':{r.get('agency_id') or '(blank)':{'name':r.get('agency_name'),'routes':len(agency_routes.get(r.get('agency_id') or '(blank)',set())),'trips':len(agency_trips.get(r.get('agency_id') or '(blank)',set()))} for r in agencies},'route_type_counts':dict(Counter(r.get('route_type','') for r in routes)),'service_calendars':service_dates,'trip_stop_time_row_frequency':dict(sorted(frequency.items())),'feed_info':data['feed_info.txt'][0] if data['feed_info.txt'] else {},'limitations':['Only the seven supplied GTFS files were available; calendar_dates.txt, shapes.txt, frequencies.txt, transfers.txt, fare files, and attribution/license records were not supplied.','No geographic boundary or official-source validation is applied. Coordinates and agency names indicate representation but do not establish service-area completeness or official authority.','Calendar dates describe scheduled weekly service only; exceptions cannot be represented without calendar_dates.txt.','Canonical outputs retain source columns and identifiers; blank agency_id on routes is interpreted using GTFS default only when exactly one agency exists.']}
 # Emit stable canonical tables in source order; normalize whitespace and selected numeric/date fields.
 for source in ('agency.txt','routes.txt','trips.txt','stops.txt','calendar.txt','feed_info.txt'):
  rows=data[source]; headers=files[source]['headers']; target=a.output/(source[:-4]+'.csv')
  with target.open('w',encoding='utf-8',newline='') as f:
   w=csv.DictWriter(f,fieldnames=headers,lineterminator='\n'); w.writeheader()
   for row in rows:
    out={k:(v.strip() if isinstance(v,str) else v) for k,v in row.items()}
    if source=='stops.txt':
     for key in ('stop_lat','stop_lon'):
      try: out[key]=format(float(out[key]),'.8f')
      except (ValueError,TypeError): pass
    w.writerow(out)
 report_path=a.output/'audit.json'; report_path.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 print(json.dumps(report,indent=2,ensure_ascii=False))
if __name__=='__main__': main()

