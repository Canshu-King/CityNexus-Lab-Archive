from pathlib import Path
import argparse, copy, json, math, sys, yaml
ROOT=Path('/mnt/data/cnx_rescue')
sys.path[:0]=[str(ROOT/'visio-renderer'),str(ROOT/'visio-renderer/calibration')]
from route_p1_negotiated_grid import load
from route_candidate_selector import make_candidate,candidates_contact,candidate_contacts_fixed,candidate_self_contacts
from routing_geometry import route_points,node_box,segment_intersects_box_interior

EPS=1e-9

def decimals_ok(v,places=3):
    return abs(v-round(v,places)) < 1e-8

def validate(path, out=None):
    data=yaml.safe_load(Path(path).read_text(encoding='utf-8'))
    plan=data.get('metadata',{}).get('plan')
    if not plan: raise SystemExit('metadata.plan missing')
    sem,orig,nodes,routes,over,frozen,mutable=load(plan)
    report={'status':'PASS','plan':plan,'associationWitnessCount':0,'frozenExtendCount':len(frozen),'checkedRouteCount':0,'routeFailures':{},'crossRouteContacts':[]}
    cs=[]
    seen=set()
    for raw in data.get('routes',[]):
        rid=raw['id']; seen.add(rid)
        base=routes.get(rid)
        fails=[]
        if not base: fails.append('unknown route'); report['routeFailures'][rid]=fails; continue
        for k in ('connectorType','source','target','sourceSide','targetSide'):
            if raw.get(k)!=base.get(k): fails.append(f'{k} mismatch expected={base.get(k)!r} got={raw.get(k)!r}')
        for k in ('sourcePortFraction','targetPortFraction'):
            if abs(float(raw.get(k))-float(base.get(k)))>1e-9: fails.append(f'{k} mismatch expected={base.get(k)} got={raw.get(k)}')
        rr=copy.deepcopy(base); rr['waypoints']=copy.deepcopy(raw.get('waypoints',[]))
        pts=route_points(rr,nodes)
        # structural checks
        try:
            c=make_candidate({'routeId':rid,'family':'partial-witness','points':pts,'cost':0,'tag':'partial:'+rid})
        except Exception as e:
            fails.append(f'candidate invalid: {e}'); c=None
        # endpoint tangency implied by route_points + first/last segment, check direction explicitly
        ss=rr['sourceSide']; ts=rr['targetSide']
        if len(pts)>=2:
            dx=pts[1][0]-pts[0][0]; dy=pts[1][1]-pts[0][1]
            ok={'LEFT':dx<0 and abs(dy)<EPS,'RIGHT':dx>0 and abs(dy)<EPS,'TOP':dy>0 and abs(dx)<EPS,'BOTTOM':dy<0 and abs(dx)<EPS}.get(ss,False)
            if not ok: fails.append(f'source endpoint tangent wrong side={ss} first={pts[:2]}')
            dx=pts[-1][0]-pts[-2][0]; dy=pts[-1][1]-pts[-2][1]
            ok={'LEFT':dx>0 and abs(dy)<EPS,'RIGHT':dx<0 and abs(dy)<EPS,'TOP':dy>0 and abs(dx)<EPS,'BOTTOM':dy<0 and abs(dx)<EPS}.get(ts,False)
            if not ok: fails.append(f'target endpoint tangent wrong side={ts} last={pts[-2:]}')
        # page bounds
        W=float(sem['pageWidth']); H=float(sem['pageHeight'])
        if any(x<-EPS or x>W+EPS or y<-EPS or y>H+EPS for x,y in pts): fails.append('out of page')
        # nodes
        for nid,n in nodes.items():
            if nid in (rr['source'],rr['target']): continue
            box=node_box(n)
            if any(segment_intersects_box_interior(tuple(a),tuple(b),box) for a,b in zip(pts,pts[1:])):
                fails.append(f'through unrelated node {nid}')
        # min segment
        for a,b in zip(pts,pts[1:]):
            length=abs(a[0]-b[0])+abs(a[1]-b[1])
            if length < 0.1-1e-8: fails.append(f'short segment {a}->{b} len={length}')
        # redundant collinear
        for a,b,c3 in zip(pts,pts[1:],pts[2:]):
            if (abs(a[0]-b[0])<EPS and abs(b[0]-c3[0])<EPS) or (abs(a[1]-b[1])<EPS and abs(b[1]-c3[1])<EPS):
                fails.append(f'redundant collinear point {b}')
        # waypoint precision: allow .005 exact-grid because some generated family paths use it; formal normalizer can round later.
        if any(not decimals_ok(float(v),3) for p in raw.get('waypoints',[]) for v in p): fails.append('waypoint >3 decimal precision')
        if c and candidate_contacts_fixed(c,frozen.values()): fails.append('contact frozen Extend')
        if fails: report['routeFailures'][rid]=fails
        if c: cs.append(c)
    report['associationWitnessCount']=len(data.get('routes',[])); report['checkedRouteCount']=len(cs)+len(frozen)
    for i,a in enumerate(cs):
        for b in cs[i+1:]:
            if candidates_contact(a,b): report['crossRouteContacts'].append([a.route_id,b.route_id])
    if report['routeFailures'] or report['crossRouteContacts']: report['status']='FAIL'
    if out: Path(out).write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('witness');ap.add_argument('--out');args=ap.parse_args()
    r=validate(args.witness,args.out);print(json.dumps(r,indent=2)); raise SystemExit(0 if r['status']=='PASS' else 1)
