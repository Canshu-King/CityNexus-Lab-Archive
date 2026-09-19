from pathlib import Path
import sys,copy,yaml,json,random
from collections import Counter
root=Path('/mnt/data/cnx_rescue');sys.path[:0]=[str(root/'visio-renderer'),str(root/'visio-renderer/calibration')]
from route_p1_negotiated_grid import load,build_axes,build_graph,astar,compact
from routing_geometry import route_points
from critical_grid_geometry import q,unq,closed_contact
PLAN='PLAN_QUOTA_SAVER_UPPER_SEPARATED_20260908'
BASEFIX=['A-T-UC-02','A-T-UC-04','A-T-UC-05','A-T-UC-11','A-T-UC-07','A-T-UC-06']
TEST=['A-CD-UC-10','A-M-UC-08','A-M-UC-10']
sem,orig,nodes,routes,over,frozen,mutable=load(PLAN)
w=yaml.safe_load((root/'P1_PARTIAL12_WITNESS.yaml').read_text());wb={r['id']:r for r in w['routes']}
valid=json.load(open(root/'VALID_UPPER_PAIR_EXAMPLES.json'))
# common CD05 path
cd05=[(29.9,4.7),(26.5,4.7),(26.5,4.9),(25.7,4.9)]
common={}
for rid in BASEFIX:
 rr=copy.deepcopy(routes[rid]);rr['waypoints']=copy.deepcopy(wb[rid]['waypoints']);common[rid]=route_points(rr,nodes)
common['A-CD-UC-05']=cd05

def solve_with_paths(test_rid, pathmap):
    xs,ys=build_axes(sem,mutable,nodes,frozen)
    xi={q(x) for x in xs}; yi={q(y) for y in ys};clr=q(.1);W=q(float(sem['pageWidth']));H=q(float(sem['pageHeight']))
    barrier_segments=[]
    for pts in pathmap.values():
        for a,b in zip(pts,pts[1:]):
            qa=(q(a[0]),q(a[1]));qb=(q(b[0]),q(b[1]));barrier_segments.append((qa,qb))
            for x in (qa[0],qb[0]):
                for d in (0,-clr,clr):
                    if 0<=x+d<=W:xi.add(x+d)
            for y in (qa[1],qb[1]):
                for d in (0,-clr,clr):
                    if 0<=y+d<=H:yi.add(y+d)
    xs=[unq(v) for v in sorted(xi)];ys=[unq(v) for v in sorted(yi)];ix,iy,base_allowed=build_graph(xs,ys,nodes,frozen)
    def allowed(a,b):
        if not base_allowed(a,b):return False
        qa=(q(a[0]),q(a[1]));qb=(q(b[0]),q(b[1]))
        return not any(closed_contact(qa,qb,c,d) for c,d in barrier_segments)
    p=astar(routes[test_rid],nodes,xs,ys,ix,iy,allowed,Counter(),Counter(),Counter(),Counter(),0.0,0.2,random.Random(1),hard=True,noise=0.0)
    return compact(p) if p else None

rows=[]
for row in valid:
    i=row['index']; ex=row['example']; paths=dict(common)
    paths['A-CD-UC-04']=ex['A-CD-UC-04']['points'];paths['A-M-UC-04']=ex['A-M-UC-04']['points']
    r={'index':i,'reach':{}}
    for rid in TEST:
        p=solve_with_paths(rid,paths);r['reach'][rid]=p
    print('index',i,{rid:bool(p) for rid,p in r['reach'].items()},flush=True)
    rows.append(r)
(root/'UPPER_PAIR_REACHABILITY.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
