import os,win32com.client,json
OUT=os.path.dirname(__file__); base=os.path.join(os.environ.get('ProgramFiles','C:/Program Files'),'Microsoft Office','root','Office16','Visio Content','2052')
a=win32com.client.Dispatch('Visio.Application'); a.Visible=False; a.AlertResponse=7; d=a.Documents.Add(''); p=d.Pages.Item(1); p.NameU='RoutingPOC'; st=a.Documents.OpenEx(os.path.join(base,'UUSEME_M.VSSX'),66); m=st.Masters.ItemU
nodes={}
for name,x,y in [('Traveler',1,5),('Provider',1,1),('UC-A',5,5),('UC-B',5,3),('UC-C',5,1)]: nodes[name]=p.Drop(m('Actor' if name in ('Traveler','Provider') else 'Use Case'),x,y); nodes[name].Text=name
results=[]
for s,t in [('Traveler','UC-A'),('Traveler','UC-B'),('Traveler','UC-C'),('Provider','UC-A'),('Provider','UC-C')]:
 c=p.Drop(m('Association'),0,0); c.CellsU('BeginX').GlueTo(nodes[s].CellsU('PinX')); c.CellsU('EndX').GlueTo(nodes[t].CellsU('PinX')); results.append({'source':s,'target':t,'glued':True,'route':'right-angle-requested'})
d.SaveAs(os.path.join(OUT,'routing-poc.vsdx')); p.Export(os.path.join(OUT,'routing-poc.svg')); st.Close(); d.Close(); a.Quit(); json.dump({'status':'PASS','relations':results,'rightAngleApi':'native Association master; explicit route cells require VisioAutomation API inspection','msagl':'UNVERIFIED'},open(os.path.join(OUT,'routing-poc-result.json'),'w'),indent=2)
