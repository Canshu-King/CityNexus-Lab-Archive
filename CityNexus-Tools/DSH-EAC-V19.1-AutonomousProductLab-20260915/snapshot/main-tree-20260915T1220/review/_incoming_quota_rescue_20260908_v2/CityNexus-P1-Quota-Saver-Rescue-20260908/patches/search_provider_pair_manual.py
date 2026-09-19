from pathlib import Path
import sys,copy,random,json,time
root=Path('/mnt/data/cnx_rescue');sys.path[:0]=[str(root/'visio-renderer'),str(root/'visio-renderer/calibration')]
from route_p1_negotiated_grid import load,build_axes,build_graph
from search_p1_global_port_rotations import genus,target_options
from routing_geometry import route_points,node_box,segment_intersects_box_interior,path_is_orthogonal,side_port
from explore_p1_disjoint_pool import _candidate_pool,_candidate_points_cm
from route_candidate_selector import candidates_contact,make_candidate

PLAN='PLAN_TRAVELER_SKELETON_PLANAR_GRID'
sem,orig,nodes,routes0,over,frozen0,mut=load(PLAN)
# manual traveler ports/routes
M={
'A-T-UC-11': {'sourcePortFraction':1/3,'targetSide':'TOP','targetPortFraction':(24.0-20.9)/4.8,'waypoints':[[4.6,9.2],[4.6,6.0],[24.0,6.0]]},
'A-T-UC-06': {'sourcePortFraction':13/30,'targetSide':'BOTTOM','targetPortFraction':(12.5-8.7)/4.8,'waypoints':[[5.0,9.5],[5.0,9.9],[12.5,9.9]]},
'A-T-UC-07': {'sourcePortFraction':8/15,'targetSide':'LEFT','targetPortFraction':(8.2-7.525)/1.35,'waypoints':[[4.8,9.8],[4.8,10.0],[13.0,10.0],[13.0,9.0],[14.6,9.0],[14.6,8.2]]},
}
base=copy.deepcopy(routes0)
for rid,v in M.items(): base[rid].update(v)
manual_hard={rid:route_points(base[rid],nodes) for rid in M}
hard0={**frozen0,**manual_hard}

# source fractions corresponding exact 0.1 y lanes
def source_fracs(nid):
 n=nodes[nid]; top=n['y']-n['height']/2; h=n['height'];
 ys=[]; y=round(top+0.1,1); end=round(top+h-0.1,1)
 while y<=end+1e-9:
  ys.append((y-top)/h); y=round(y+0.1,1)
 return ys
b_src=source_fracs('ACT-BOOKING'); p_src=source_fracs('ACT-PAYAUTH')
# priority targets: all exact ports, shuffled by natural-side preference / center-ish
def opts(rid):
 node=nodes[base[rid]['target']]
 arr=target_options(node)
 pref={'A-B-06':{'RIGHT':0,'BOTTOM':1,'TOP':2,'LEFT':3}, 'A-PA-07':{'RIGHT':0,'TOP':1,'BOTTOM':2,'LEFT':3}}[rid]
 arr=sorted(arr,key=lambda sf:(pref[sf[0]],abs(float(sf[1])-0.5)))
 return arr
b_opts=opts('A-B-06'); p_opts=opts('A-PA-07')

rng=random.Random(2026090803)
# create deterministic mixed samples incl top priorities and random tail
B=[];P=[]
for f in b_src:
 for s,t in b_opts[:32]: B.append((f,s,t))
for f in p_src:
 for s,t in p_opts[:32]: P.append((f,s,t))
# random extra
for _ in range(1000):
 B.append((rng.choice(b_src),*rng.choice(b_opts)))
 P.append((rng.choice(p_src),*rng.choice(p_opts)))
# dedupe
B=list(dict.fromkeys(B));P=list(dict.fromkeys(P))
rng.shuffle(B);rng.shuffle(P)
start=time.monotonic(); trials=0; genus0=0; routed1=0
# pair sampling randomized with some full combinations early
pairs=[]
for i in range(min(500,len(B))):
 for j in range(min(20,len(P))): pairs.append((B[i],P[(i*17+j)%len(P)]))
for _ in range(30000): pairs.append((rng.choice(B),rng.choice(P)))
seen=set()
for bc,pc in pairs:
 key=(bc,pc)
 if key in seen: continue
 seen.add(key);trials+=1
 routes=copy.deepcopy(base)
 bf,bs,bt=bc;pf,ps,pt=pc
 routes['A-B-06']['sourcePortFraction']=bf;routes['A-B-06']['targetSide']=bs;routes['A-B-06']['targetPortFraction']=bt
 routes['A-PA-07']['sourcePortFraction']=pf;routes['A-PA-07']['targetSide']=ps;routes['A-PA-07']['targetPortFraction']=pt
 if genus(routes,nodes)!=0: continue
 genus0+=1
 local=[routes['A-B-06'],routes['A-PA-07']]
 xs,ys=build_axes(sem,local,nodes,hard0);ix,iy,allowed=build_graph(xs,ys,nodes,hard0)
 # try both route orders and candidate samples
 for first,second in [('A-B-06','A-PA-07'),('A-PA-07','A-B-06')]:
  r1=routes[first];r2=routes[second]
  pool1=_candidate_pool(r1,nodes,xs,ys,ix,iy,allowed,8, 100000+trials*31+(0 if first=='A-B-06' else 1))
  if not pool1: continue
  routed1+=1
  for c1 in pool1[:8]:
   hard1=dict(hard0); hard1['__first__']=_candidate_points_cm(c1)
   xs2,ys2=build_axes(sem,[r2],nodes,hard1);ix2,iy2,allowed2=build_graph(xs2,ys2,nodes,hard1)
   pool2=_candidate_pool(r2,nodes,xs2,ys2,ix2,iy2,allowed2,10, 200000+trials*47+len(c1.points))
   for c2 in pool2:
    if not candidates_contact(c1,c2):
      out={'status':'PASS','trials':trials,'genus0':genus0,'elapsed':time.monotonic()-start,
           'ports':{'A-B-06':{'sourcePortFraction':bf,'targetSide':bs,'targetPortFraction':bt},'A-PA-07':{'sourcePortFraction':pf,'targetSide':ps,'targetPortFraction':pt}},
           'paths':{first:_candidate_points_cm(c1),second:_candidate_points_cm(c2)}}
      print(json.dumps(out,indent=2));Path('/mnt/data/cnx_rescue/provider_pair_witness.json').write_text(json.dumps(out,indent=2));raise SystemExit(0)
 if trials%100==0: print(json.dumps({'trials':trials,'genus0':genus0,'elapsed':round(time.monotonic()-start,2)}),flush=True)
 if time.monotonic()-start>110: break
print(json.dumps({'status':'FAIL','trials':trials,'genus0':genus0,'elapsed':time.monotonic()-start},indent=2))
