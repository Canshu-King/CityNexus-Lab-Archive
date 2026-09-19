from pathlib import Path
import sys,copy,yaml,json
root=Path('/mnt/data/cnx_rescue');sys.path[:0]=[str(root/'visio-renderer'),str(root/'visio-renderer/calibration')]
from route_p1_negotiated_grid import load
from route_candidate_selector import make_candidate,candidates_contact,candidate_contacts_fixed
from routing_geometry import route_points,node_box,segment_intersects_box_interior
PLAN='PLAN_QUOTA_SAVER_UPPER_SEPARATED_20260908'
sem,orig,nodes,routes,over,frozen,mutable=load(PLAN)
w=yaml.safe_load((root/'P1_PARTIAL12_WITNESS.yaml').read_text());wb={r['id']:r for r in w['routes']}
FIX=['A-T-UC-02','A-T-UC-04','A-T-UC-05','A-T-UC-11','A-T-UC-07','A-T-UC-06']
fixed=[]
for rid in FIX:
 rr=copy.deepcopy(routes[rid]);rr['waypoints']=copy.deepcopy(wb[rid]['waypoints']);pts=route_points(rr,nodes)
 fixed.append(make_candidate({'routeId':rid,'points':pts,'cost':0,'tag':'f:'+rid}))
# CD05 manual
cd05=make_candidate({'routeId':'A-CD-UC-05','points':[(29.9,4.7),(26.5,4.7),(26.5,4.9),(25.7,4.9)],'cost':0,'tag':'cd05'})
fixed.append(cd05)
data=json.load(open(root/'pair_cd04_m04_uppertrial_small.json'))
valid=[]
for i,ex in enumerate(data['examples']):
 cs=[];bad=[]
 for rid in ['A-CD-UC-04','A-M-UC-04']:
  val=ex[rid]
  try:c=make_candidate({'routeId':rid,'points':val['points'],'cost':val.get('cost',0),'tag':f'e{i}:{rid}'})
  except Exception as e:bad.append([rid,'make',str(e)]);continue
  if candidate_contacts_fixed(c,frozen.values()):bad.append([rid,'frozen'])
  contacts=[x.route_id for x in fixed if candidates_contact(c,x)]
  if contacts:bad.append([rid,'fixedContacts',contacts])
  # nodes
  rr=routes[rid];bn=[]
  for nid,n in nodes.items():
   if nid in (rr['source'],rr['target']):continue
   if any(segment_intersects_box_interior(tuple(a),tuple(b),node_box(n)) for a,b in zip(val['points'],val['points'][1:])):bn.append(nid)
  if bn:bad.append([rid,'nodes',bn])
  cs.append(c)
 if len(cs)==2 and candidates_contact(cs[0],cs[1]):bad.append(['pair','contact'])
 if not bad:valid.append({'index':i,'example':ex})
 else: print('example',i,'BAD',bad)
print('valid',len(valid),[v['index'] for v in valid])
(root/'VALID_UPPER_PAIR_EXAMPLES.json').write_text(json.dumps(valid,indent=2),encoding='utf-8')
