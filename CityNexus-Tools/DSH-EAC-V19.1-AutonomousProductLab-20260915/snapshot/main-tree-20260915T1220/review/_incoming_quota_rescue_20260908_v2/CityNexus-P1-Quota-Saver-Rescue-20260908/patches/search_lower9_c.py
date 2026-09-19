from pathlib import Path
import sys,copy,yaml,json,time
root=Path('/mnt/data/cnx_rescue');sys.path[:0]=[str(root/'visio-renderer'),str(root/'visio-renderer/calibration')]
from route_p1_negotiated_grid import load,build_axes,build_graph
from explore_p1_disjoint_pool import _candidate_pool,_merge_candidate,_path_cost
from route_candidate_selector import make_candidate,candidates_contact,build_conflicts,route_pair_compatibility,arc_consistency_prune,find_first_solution
from routing_geometry import route_points,node_box,segment_intersects_box_interior
PLAN='PLAN_QUOTA_SAVER_DUAL_ROTATED_20260908'
UPPER={'A-T-UC-02','A-T-UC-04','A-T-UC-05','A-T-UC-11','A-T-UC-07','A-T-UC-06','A-CD-UC-04','A-CD-UC-05','A-M-UC-04'}
LOWER=['A-T-UC-10','A-T-UC-08','A-T-UC-12','A-B-06','A-PA-07','A-CE-09','A-CD-UC-10','A-M-UC-08','A-M-UC-10']
sem,orig,nodes,routes,over,frozen,mutable=load(PLAN)
w=yaml.safe_load((root/'P1_PARTIAL15C_WITNESS.yaml').read_text());wby={r['id']:r for r in w['routes']}
upper=[]
for rid in UPPER:
 raw=wby[rid];rr=copy.deepcopy(routes[rid]);rr['waypoints']=copy.deepcopy(raw['waypoints']);pts=route_points(rr,nodes)
 upper.append(make_candidate({'routeId':rid,'family':'upper-fixed','points':pts,'cost':0,'tag':'upper:'+rid}))
xs,ys=build_axes(sem,mutable,nodes,frozen);ix,iy,allowed=build_graph(xs,ys,nodes,frozen)
samples=int(sys.argv[1]) if len(sys.argv)>1 else 8;seed=2026090851
pools={};t=time.time()
for rid in LOWER:
 vals=_candidate_pool(routes[rid],nodes,xs,ys,ix,iy,allowed,samples,seed+sum(map(ord,rid))*997)
 clean=[c for c in vals if not any(candidates_contact(c,x) for x in upper)]
 pools[rid]=clean
 # inject lower seed from partial15 if current port matches (it does)
 raw=wby.get(rid)
 if raw:
  rr=copy.deepcopy(routes[rid]);rr['waypoints']=copy.deepcopy(raw['waypoints']);pts=route_points(rr,nodes)
  try:c=make_candidate({'routeId':rid,'family':'partial15','points':pts,'cost':_path_cost(pts),'tag':'partial15:'+rid})
  except Exception:c=None
  if c and not any(candidates_contact(c,x) for x in upper):_merge_candidate(pools[rid],c)
 print('pool',rid,'gen',len(vals),'clean',len(pools[rid]),'t',round(time.time()-t,1),flush=True)
# inject prior pair evidence endpoint-compatible and upper-clean
edir=Path('/mnt/data/cnx_assist_prev/CityNexus-P1-Codex-Deep-Assist-20260908/evidence')
def endpoints_match(rid,pts):
 rr=copy.deepcopy(routes[rid]);rr['waypoints']=[]; ep=route_points(rr,nodes)
 return len(pts)>=2 and all(abs(float(pts[0][i])-ep[0][i])<1e-6 and abs(float(pts[-1][i])-ep[-1][i])<1e-6 for i in (0,1))
added={}
for fp in edir.glob('pair_*.json'):
 try:data=json.load(open(fp))
 except:continue
 for ei,ex in enumerate(data.get('examples',[])):
  for rid,val in ex.items():
   if rid not in pools or not isinstance(val,dict) or 'points' not in val:continue
   pts=val['points']
   if not endpoints_match(rid,pts):continue
   try:c=make_candidate({'routeId':rid,'family':'prior-pair','points':pts,'cost':val.get('cost',_path_cost(pts)),'tag':f'{fp.stem}:{ei}:{rid}'})
   except Exception:continue
   if any(candidates_contact(c,x) for x in upper):continue
   before=len(pools[rid]);_merge_candidate(pools[rid],c)
   if len(pools[rid])>before:added[rid]=added.get(rid,0)+1
print('evidenceAdded',added)
# Inject exact individually upper-clean reachability witnesses from the dual-rotation barrier proof.
reach=json.load(open(root/'UPPER_BARRIER_DIAGNOSTIC.json'))
reach_added={}
for rid in ('A-CD-UC-10','A-M-UC-08','A-M-UC-10'):
    pts=reach.get(rid,{}).get('allFixed')
    if not pts:
        continue
    try:
        c=make_candidate({'routeId':rid,'family':'upper-reachability','points':pts,'cost':_path_cost(pts),'tag':'upper-reach:'+rid})
    except Exception:
        continue
    if any(candidates_contact(c,x) for x in upper):
        continue
    before=len(pools[rid]);_merge_candidate(pools[rid],c)
    if len(pools[rid])>before:reach_added[rid]=1
print('reachabilityAdded',reach_added)
print('counts',{k:len(v) for k,v in pools.items()},'total',sum(map(len,pools.values())))
if any(not v for v in pools.values()):print('EMPTY_BASE',[k for k,v in pools.items() if not v]);raise SystemExit(2)
conf=build_conflicts(pools);pairs=route_pair_compatibility(pools,conflicts=conf);imp=[x for x in pairs if x['compatiblePairs']==0]
print('impossible',[(x['routeA'],x['routeB']) for x in imp])
ac=arc_consistency_prune(pools,conflicts=conf);print('ac',ac['status'],ac['emptyRoutes'],{k:len(v) for k,v in ac['domains'].items()})
if ac['status']=='PASS':
 res=find_first_solution(ac['domains'],conflicts=build_conflicts(ac['domains']),time_limit_seconds=120)
 print('csp',res['status'],res.get('reason'),res.get('expandedStates'),res.get('maxDepth'),res.get('deadEndCounts'))
 if res['status']=='PASS':
  out={rid:{'points':[[x/200,y/200] for x,y in c.points],'tag':c.tag,'family':c.family,'cost':c.cost} for rid,c in res['selection'].items()}
  (root/'LOWER9_SOLUTION.json').write_text(json.dumps(out,indent=2),encoding='utf-8');print(json.dumps(out,indent=2));raise SystemExit(0)
# diagnostics
(root/'LOWER9_DIAGNOSTIC.json').write_text(json.dumps({'counts':{k:len(v) for k,v in pools.items()},'impossible':imp,'ac':{'status':ac['status'],'emptyRoutes':ac['emptyRoutes'],'remaining':{k:len(v) for k,v in ac['domains'].items()},'removals':ac['removals'][-100:]}},indent=2),encoding='utf-8')
raise SystemExit(2)
