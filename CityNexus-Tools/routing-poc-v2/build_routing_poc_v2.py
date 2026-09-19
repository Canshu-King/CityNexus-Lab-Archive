import os,win32com.client
OUT=os.path.dirname(__file__); base=os.path.join(os.environ.get('ProgramFiles','C:/Program Files'),'Microsoft Office','root','Office16','Visio Content','2052')
a=win32com.client.Dispatch('Visio.Application'); a.Visible=False; a.AlertResponse=7; d=a.Documents.Add(''); p=d.Pages.Item(1); p.NameU='RoutingPOC-V2'; st=a.Documents.OpenEx(os.path.join(base,'UUSEME_M.VSSX'),66); m=st.Masters.ItemU
nodes={}
for name,x,y in [('Traveler',1.5,6),('Provider',1.5,2),('UC-A',5.5,6),('UC-B',5.5,4),('UC-C',5.5,2)]: nodes[name]=p.Drop(m('Actor' if name in ('Traveler','Provider') else 'Use Case'),x,y); nodes[name].Text=name
for s,t in [('Traveler','UC-A'),('Traveler','UC-B'),('Traveler','UC-C'),('Provider','UC-A'),('Provider','UC-C')]:
 c=p.Drop(m('Association'),0,0); c.CellsU('BeginX').GlueTo(nodes[s].CellsU('PinX')); c.CellsU('EndX').GlueTo(nodes[t].CellsU('PinX'))
d.SaveAs(os.path.join(OUT,'routing-poc-v2.vsdx')); p.Export(os.path.join(OUT,'routing-poc-v2.svg')); st.Close(); d.Close(); a.Quit()
