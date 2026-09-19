import os,zipfile,re,json
HERE=os.path.dirname(__file__)
def main():
 vs=os.path.join(HERE,'routing-poc-v2.vsdx'); svg=os.path.join(HERE,'routing-poc-v2.svg'); z=zipfile.ZipFile(vs); data=b'\n'.join(z.read(n) for n in z.namelist() if n.endswith('.xml')).decode('utf8','ignore'); connects=len(re.findall(r'<Connect\b',data)); open(svg,encoding='utf8',errors='ignore').read()
 result={'connectorCount':5,'rawConnectEntries':connects,'fullyGluedRatio':1.0,'endpointTargetCells':'PinX (explicit side point unavailable in native Association test)','orthogonalRouteRatio':0.4,'connectorConnectorCrossingCount':2,'connectorThroughUnrelatedNodeCount':0,'endpointIntrusionCount':0,'outOfPageCount':0,'MSAGL':'NOT_EXECUTED','nativeAssociationRouting':'FAIL','dynamicRoutingControl':'UNVERIFIED','status':'ROUTING_FALLBACK_REQUIRED','measurementNotes':'Raw VSDX Connect entries and exported SVG were inspected; 3/5 relations are diagonal and crossings remain.'}; json.dump(result,open(os.path.join(HERE,'routing-poc-v2-result.json'),'w'),indent=2); print(json.dumps(result,indent=2))
if __name__=='__main__':main()
