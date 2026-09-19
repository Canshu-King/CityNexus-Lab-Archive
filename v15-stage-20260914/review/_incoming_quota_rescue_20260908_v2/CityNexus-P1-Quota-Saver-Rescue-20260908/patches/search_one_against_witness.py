from pathlib import Path
import argparse,copy,json,sys,yaml,time
root=Path('/mnt/data/cnx_rescue');sys.path[:0]=[str(root/'visio-renderer'),str(root/'visio-renderer/calibration')]
from route_p1_negotiated_grid import load,build_axes,build_graph
from explore_p1_disjoint_pool import _candidate_pool
from route_candidate_selector import make_candidate,candidates_contact,candidate_contacts_fixed
from routing_geometry import route_points,node_box,segment_intersects_box_interior
ap=argparse.ArgumentParser();ap.add_argument('route');ap.add_argument('witness');ap.add_argument('--samples',type=int,default=100);ap.add_argument('--seed',type=int,default=12345);ap.add_argument('--out');args=ap.parse_args()
w=yaml.safe_load(Path(args.witness).read_text()); plan=w['metadata']['plan']
sem,orig,nodes,routes,over,frozen,mutable=load(plan)
fixed=[]
for raw in w['routes']:
 if raw['id']==args.route: continue
 rr=copy.deepcopy(routes[raw['id']]);rr['waypoints']=copy.deepcopy(raw['waypoints']);pts=route_points(rr,nodes)
 fixed.append(make_candidate({'routeId':raw['id'],'family':'witness','points':pts,'cost':0,'tag':'w:'+raw['id']}))
xs,ys=build_axes(sem,mutable,nodes,frozen);ix,iy,allowed=build_graph(xs,ys,nodes,frozen)
vals=_candidate_pool(routes[args.route],nodes,xs,ys,ix,iy,allowed,args.samples,args.seed)
rows=[]
for c in vals:
 contacts=[x.route_id for x in fixed if candidates_contact(c,x)]
 if not contacts:
  rows.append({'tag':c.tag,'family':c.family,'cost':c.cost,'points':[[x/200,y/200] for x,y in c.points]})
print(json.dumps({'route':args.route,'generated':len(vals),'clean':len(rows),'examples':rows[:20]},indent=2))
if args.out:Path(args.out).write_text(json.dumps({'route':args.route,'generated':len(vals),'clean':len(rows),'examples':rows[:100]},indent=2),encoding='utf-8')
