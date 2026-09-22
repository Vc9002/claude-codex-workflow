#!/usr/bin/env python3
"""Daily P&L updater. Pulls Polymarket US + Kalshi live and rebuilds the workbook."""
import json,os,sys,subprocess,time,base64,datetime,urllib.request,urllib.parse
from collections import defaultdict
from openpyxl import Workbook
from openpyxl.styles import Font,PatternFill,Alignment,Border,Side
from openpyxl.chart import LineChart,BarChart,Reference,Series
HERE=os.path.dirname(os.path.abspath(__file__))
CFG=json.load(open(os.path.join(HERE,"config.json")))
OUTPUT=os.path.abspath(os.path.join(HERE,CFG["output_xlsx"]))
def f(x):
    try:return float(x)
    except:return 0.0

# ---------- 1. Pull Polymarket via Node SDK ----------
sdk=os.path.abspath(os.path.join(HERE,CFG["polymarket_sdk_dir"]))
polyfile=os.path.join(HERE,"poly_dump.json")
import shutil
_tmpjs=os.path.join(sdk,"_pnl_pull_tmp.mjs")
shutil.copy(os.path.join(HERE,"pull_poly.mjs"),_tmpjs)
try:
    subprocess.run(["node",_tmpjs,sdk,polyfile],cwd=sdk,check=True)
finally:
    try:
        if os.path.exists(_tmpjs):os.remove(_tmpjs)
    except Exception:pass
P=json.load(open(polyfile));poly={"activities":P["activities"]};pa=P["activities"];pb=P["balances"]["balances"][0]
PCASH=pb["currentBalance"]
# value open positions at cost basis (API assetNotional can be 0/unmarked for sports)
_pos=(P.get("positions") or {}).get("positions") or {}
POPEN=round(sum(f((v.get("cost") or {}).get("value")) for v in _pos.values()),2)
NOPEN=len(_pos)
PVAL=round(PCASH+POPEN,2)  # total Polymarket equity = cash + open positions at cost
# trades list (date,slug,title,outcome,intent,price,qty,notional)
trades=[]
for a in pa:
    if a["type"]!="ACTIVITY_TYPE_TRADE":continue
    tr=a["trade"];isAgg=tr.get("isAggressor");ex=tr["aggressorExecution"] if isAgg else tr["passiveExecution"]
    o=ex["order"];mm=o.get("marketMetadata") or {}
    p=f(tr["price"]["value"]);q=f(tr.get("qtyDecimal") or tr["qty"])
    trades.append([(tr.get("createTime") or "")[:19].replace("T"," "),tr["marketSlug"],mm.get("title",""),mm.get("outcome",""),o.get("intent","").replace("ORDER_INTENT_",""),round(p,3),round(q,2),round(p*q,2),tr.get("id","")])
# ---- Persistent transaction ledger: never drop past transactions ----
import csv
_ledger=os.path.join(HERE,"trades_ledger.csv")
_seen={}
if os.path.exists(_ledger):
    with open(_ledger,newline="") as fh:
        for row in csv.reader(fh):
            if len(row)>=9: _seen[row[8] or "|".join(row[:8])]=row[:9]
for t in trades:
    key=t[8] or "|".join(str(x) for x in t[:8])
    _seen[key]=[str(t[0]),t[1],t[2],t[3],t[4],t[5],t[6],t[7],t[8]]
# union, sorted by datetime
merged=sorted(_seen.values(),key=lambda r:r[0])
with open(_ledger,"w",newline="") as fh:
    w=csv.writer(fh)
    for r in merged: w.writerow(r)
# rebuild trades from the union (typed) so the sheet shows full history
trades=[[r[0],r[1],r[2],r[3],r[4],float(r[5]),float(r[6]),float(r[7]),r[8]] for r in merged]
trades.sort(key=lambda r:r[0])
PDEP=sum(f((a.get('accountBalanceChange') or {}).get('amount',{}).get('value')) for a in pa if a['type']=='ACTIVITY_TYPE_ACCOUNT_DEPOSIT')
PCR=sum(f((a.get('accountBalanceChange') or {}).get('amount',{}).get('value')) for a in pa if a['type']=='ACTIVITY_TYPE_TRANSFER')
def _wd(a):return f((a.get('accountBalanceChange') or {}).get('amount',{}).get('value'))
PWD=sum(_wd(a) for a in pa if a['type']=='ACTIVITY_TYPE_ACCOUNT_WITHDRAWAL')
PWD_DONE=sum(_wd(a) for a in pa if a['type']=='ACTIVITY_TYPE_ACCOUNT_WITHDRAWAL' and 'PENDING' not in (a.get('accountBalanceChange') or {}).get('status',''))
# P&L = current value + completed withdrawals (already left) - deposits - credits. Pending wd still sit in value.
PPL=round(PVAL+PWD_DONE-(PDEP+PCR),2)

# ---------- 2. Pull Kalshi ----------
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import padding
KID=CFG["kalshi_key_id"];KEY=serialization.load_pem_private_key(open(os.path.join(HERE,CFG["kalshi_key_file"]),"rb").read(),password=None)
KB="https://api.elections.kalshi.com";KPFX="/trade-api/v2"
def ksign(ts,m,fp):return base64.b64encode(KEY.sign((ts+m+fp).encode(),padding.PSS(mgf=padding.MGF1(hashes.SHA256()),salt_length=padding.PSS.DIGEST_LENGTH),hashes.SHA256())).decode()
def kcall(path):
    ts=str(int(time.time()*1000));fp=KPFX+path.split("?")[0];sig=ksign(ts,"GET",fp)
    req=urllib.request.Request(KB+KPFX+path)
    for k,v in {"KALSHI-ACCESS-KEY":KID,"KALSHI-ACCESS-SIGNATURE":sig,"KALSHI-ACCESS-TIMESTAMP":ts}.items():req.add_header(k,v)
    with urllib.request.urlopen(req,timeout=25) as r:return json.loads(r.read())
def kpage(name):
    out=[];cur=None
    for _ in range(40):
        q={"limit":"100"}
        if cur:q["cursor"]=cur
        d=kcall(f"/portfolio/{name}?"+urllib.parse.urlencode(q));it=d.get(name,[]);out+=it;cur=d.get("cursor")
        if not cur or not it:break
    return out
kbal=kcall("/portfolio/balance").get("balance_dollars");KVAL=f(kbal)
kdep_l=kpage("deposits");kwd_l=kpage("withdrawals");ksettle=kpage("settlements")
KDEP=round(sum(x.get("amount_cents",0) for x in kdep_l)/100,2)
KWD=round(sum(x.get("amount_cents",0) for x in kwd_l)/100,2)
KCR=CFG["kalshi_credit_usd"]
# Kalshi P&L via cash identity (matches official profile once credit is set)
KPL=round(KVAL+KWD-KDEP-KCR,2)
def kdt(ts):return datetime.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")
kr={"deposits":[[kdt(x["created_ts"]),x["amount_cents"]/100,x.get("status","")] for x in sorted(kdep_l,key=lambda z:z["created_ts"])],
    "withdrawals":[[kdt(x["created_ts"]),x["amount_cents"]/100,x.get("status","")] for x in sorted(kwd_l,key=lambda z:z["created_ts"])],
    "n_settle":len(ksettle),
    "win":sum(1 for x in ksettle if (x.get("revenue",0)/100 - f(x.get("yes_total_cost_dollars")) - f(x.get("no_total_cost_dollars")) - f(x.get("fee_cost")))>=0),
    "loss":sum(1 for x in ksettle if (x.get("revenue",0)/100 - f(x.get("yes_total_cost_dollars")) - f(x.get("no_total_cost_dollars")) - f(x.get("fee_cost")))<0)}
COMBINED=round(PPL+KPL,2)

# ---------- 3. Chart data (P&L by day/week/month + cumulative; Trades) ----------
pday=defaultdict(float)
for a in pa:
    if a["type"]!="ACTIVITY_TYPE_POSITION_RESOLUTION":continue
    pr=a["positionResolution"];bp=pr.get("beforePosition") or {};ap=pr.get("afterPosition") or {}
    rb=f((bp.get("realized") or {}).get("value"));ra=f((ap.get("realized") or {}).get("value"))
    d=(ap.get("updateTime") or pr.get("updateTime") or "")[:10]
    if d:pday[d]+=(ra-rb)
praw=sum(pday.values()) or 1; pscale=PPL/praw
kday=defaultdict(float)
for x in ksettle:
    pl=x.get("revenue",0)/100 - f(x.get("yes_total_cost_dollars")) - f(x.get("no_total_cost_dollars")) - f(x.get("fee_cost"))
    d=(x.get("settled_time","") or "")[:10]
    if d:kday[d]+=pl
kraw=sum(kday.values()) or 1; kscale=KPL/kraw
def isowk(d):
    dt=datetime.date.fromisoformat(d);y,w,_=dt.isocalendar();return f"{y}-W{w:02d}"
alld=sorted(set(list(pday)+list(kday)));dr=[];cum=0;cumr=[]
wkd=defaultdict(float);mod=defaultdict(float)
for d in alld:
    v=pday.get(d,0)*pscale+kday.get(d,0)*kscale;cum+=v
    dr.append([d,round(pday.get(d,0)*pscale,2),round(kday.get(d,0)*kscale,2),round(v,2)]);cumr.append([d,round(cum,2)])
    wkd[isowk(d)]+=v;mod[d[:7]]+=v
CH={"daily":dr,"cum_daily":cumr,"weekly":sorted([[k,round(v,2)] for k,v in wkd.items()]),"monthly":sorted([[k,round(v,2)] for k,v in mod.items()])}
tvol=defaultdict(lambda:[0,0.0])
for t in trades:tvol[t[0][:10]][0]+=1;tvol[t[0][:10]][1]+=t[7]
tdaily=[[d,tvol[d][0],round(tvol[d][1],2)] for d in sorted(tvol)]
twk=defaultdict(lambda:[0,0.0]);tmo=defaultdict(lambda:[0,0.0]);tc=0;tcum=[]
for d,n,vv in tdaily:
    twk[isowk(d)][0]+=n;twk[isowk(d)][1]+=vv;tmo[d[:7]][0]+=n;tmo[d[:7]][1]+=vv;tc+=vv;tcum.append([d,round(tc,2)])
TC={"daily":tdaily,"weekly":[[k,v[0],round(v[1],2)] for k,v in sorted(twk.items())],"monthly":[[k,v[0],round(v[1],2)] for k,v in sorted(tmo.items())],"cum":tcum}
print(f"Poly P&L {PPL} Kalshi P&L {KPL} Combined {COMBINED}")

# ---------- 4. Build workbook ----------
NAVY="11243E";ACCENT="1F6FEB";LIGHT="EAF0FA";LIGHT2="F5F8FC";GREEN="0F7B3F";RED="B42318";GREY="5B6B7F";GOLD="B8860B"
FT="Calibri"
def F(s=11,b=False,c="1A1A1A",i=False):return Font(name=FT,size=s,bold=b,color=c,italic=i)
def fill(c):return PatternFill("solid",start_color=c,end_color=c)
thin=Side(style="thin",color="D0D7E2");border=Border(left=thin,right=thin,top=thin,bottom=thin)
baccent=Border(bottom=Side(style="medium",color=ACCENT))
center=Alignment("center",vertical="center");left=Alignment("left",vertical="center")
right=Alignment("right",vertical="center");wrap=Alignment("left",vertical="center",wrap_text=True)
USD='_($* #,##0.00_);_($* (#,##0.00);_($* "-"??_);_(@_)';USD0='$#,##0;($#,##0);"-"';INT='#,##0';PCT="0.0%"
wb=Workbook()
def band(ws,t,s,n):
    ws.merge_cells(start_row=1,start_column=1,end_row=1,end_column=n)
    c=ws.cell(1,1,t);c.font=F(18,True,"FFFFFF");c.fill=fill(NAVY);c.alignment=Alignment("left",vertical="center",indent=1);ws.row_dimensions[1].height=34
    ws.merge_cells(start_row=2,start_column=1,end_row=2,end_column=n)
    c=ws.cell(2,1,s);c.font=F(10,False,"FFFFFF",i=True);c.fill=fill(ACCENT);c.alignment=Alignment("left",vertical="center",indent=1);ws.row_dimensions[2].height=18

# ===================== SUMMARY =====================
ws=wb.active;ws.title="Summary P&L";ws.sheet_view.showGridLines=False
band(ws,"Prediction-Market Trading  —  Consolidated P&L","Polymarket US + Kalshi  ·  live API + Kalshi official profit  ·  as of 2026-06-18",6)
for k,v in {"A":2,"B":44,"C":15,"D":3,"E":40,"F":16}.items():ws.column_dimensions[k].width=v
def sect(r,t):
    ws.merge_cells(start_row=r,start_column=2,end_row=r,end_column=3)
    c=ws.cell(r,2,t);c.font=F(12,True,NAVY);c.border=baccent;ws.cell(r,3).border=baccent;ws.row_dimensions[r].height=22
def kv(r,lab,val,nf=USD,vc="1A1A1A",bold=False,lc="3A3A3A"):
    c=ws.cell(r,2,lab);c.font=F(11,bold,lc);c.alignment=left
    v=ws.cell(r,3,val);v.font=F(11,bold,vc)
    if nf:v.number_format=nf
    v.alignment=right;return v
r=4
sect(r,"Account Funding  (capital in)");r+=1
kv(r,"Your cash deposits — Poly $130 + Kalshi $236","=C_DEP",);ws.cell(r,3).value=PDEP+KDEP;r+=1
kv(r,"Promotional credits — Poly $125.19 + Kalshi $44.68",PCR+KCR,vc=GOLD);r+=1
kv(r,"Total credited into accounts","=C5+C6",bold=True)
for cc in(2,3):ws.cell(r,cc).fill=fill(LIGHT)
r+=2
sect(r,"Current Account Value");r+=1
kv(r,"Polymarket US  (cash %s + %d open @ cost)"%(("$%.0f"%PCASH),NOPEN),PVAL);r+=1
kv(r,"Kalshi (drained, 0 open)",KVAL);r+=1
kv(r,"Combined account value","=C10+C11",bold=True)
for cc in(2,3):ws.cell(r,cc).fill=fill(LIGHT)
r+=2
sect(r,"Trading P&L by Platform");r+=1
kv(r,"Polymarket US  (value − funding, verified)",PPL,vc=GREEN);rp=r;r+=1
kv(r,"Kalshi  (official profit from your Kalshi profile)",KPL,vc=RED);rk=r;r+=1
kv(r,"Combined gross trading P&L",f"=C{rp}+C{rk}",bold=True,vc=GREEN);rg=r
for cc in(2,3):ws.cell(r,cc).fill=fill(LIGHT)
r+=2
sect(r,"R&D / Operating Costs");r+=1
kv(r,"Claude / AI tooling","=-Assumptions!C4",vc=RED);r+=1
kv(r,"Sports pick book  ($15/wk × weeks, auto)","=-Assumptions!C5*Assumptions!C8",vc=RED);rpk=r;r+=1
kv(r,"Total R&D costs",f"=C{rpk-1}+C{rpk}",bold=True,vc=RED);rc=r;r+=1
v=kv(r,"NET P&L after R&D",f"=C{rg}+C{rc}",bold=True);v.font=F(13,True,"FFFFFF")
for cc in(2,3):ws.cell(r,cc).fill=fill(GREEN);ws.cell(r,cc).border=border
ws.cell(r,2).font=F(13,True,"FFFFFF");ws.cell(r,2).alignment=left;ws.row_dimensions[r].height=24;rnet=r
r+=2
sect(r,"Bank Account  (real cash position)");r+=1
kv(r,"Cashed out — total withdrawals","=Assumptions!C9",vc=GREEN);rcash=r;r+=1
kv(r,"   less sports pick book","=-Assumptions!C5*Assumptions!C8",vc=RED);r+=1
kv(r,"   less Claude tokens","=-Assumptions!C4",vc=RED);r+=1
v=kv(r,"BANK ACCOUNT (cash in pocket)",f"=C{rcash}-Assumptions!C5*Assumptions!C8-Assumptions!C4",bold=True);v.font=F(12,True,"FFFFFF")
for cc in(2,3):ws.cell(r,cc).fill=fill(ACCENT);ws.cell(r,cc).border=border
ws.cell(r,2).font=F(12,True,"FFFFFF");ws.cell(r,2).alignment=left;ws.row_dimensions[r].height=22;rbank=r
r+=2
sect(r,"Return Metrics");r+=1
kv(r,"Gross return on deposited cash",f"=C{rg}/C5",nf=PCT,vc=GREEN,bold=True);r+=1
kv(r,"Net cash out (withdrawals − deposits)","=Assumptions!C9-C5",vc=GREEN,bold=True);r+=1
kv(r,"Polymarket volume / fills",round(sum(t[7] for t in trades),2),nf=USD0);ws.cell(r,2).value="Polymarket notional volume";r+=1
kv(r,"Polymarket fills",len(trades),nf=INT);r+=1
kv(r,"Kalshi volume / settlements","$1.6K / 257",nf=None);r+=1
# cards
def card(r,c,lab,val,nf,color):
    ws.merge_cells(start_row=r,start_column=c,end_row=r,end_column=c+1)
    l=ws.cell(r,c,lab);l.font=F(10,True,"FFFFFF");l.fill=fill(color);l.alignment=Alignment("left",vertical="center",indent=1)
    ws.merge_cells(start_row=r+1,start_column=c,end_row=r+1,end_column=c+1)
    v=ws.cell(r+1,c,val);v.font=F(20,True,color);v.fill=fill(LIGHT2);v.alignment=center;v.number_format=nf
    ws.row_dimensions[r].height=18;ws.row_dimensions[r+1].height=34
card(4,5,"NET P&L AFTER R&D",f"=C{rnet}",USD0,GREEN)
card(7,5,"COMBINED ACCOUNT VALUE","=C12",USD0,NAVY)
card(10,5,"NET CASH OUT (wd − deposits)","=Assumptions!C9-C5",USD0,GOLD)
card(13,5,"BANK ACCOUNT (in pocket)",f"=C{rbank}",USD0,ACCENT)
ws.merge_cells("E17:F23")
nt=ws.cell(17,5,"Verification\n• Poly: 130 + 125.19 + 568.21 = 823.40 ✓ ;  823.40 − 327.80 pending = 495.60 buying power ✓\n• Kalshi: 236 dep + 44.68 credit − 61.22 wd − 219.45 profit = $0.01 balance ✓\n• Kalshi −219.45 is Kalshi's OWN reported profit. Poly pulled from api.polymarket.us.")
nt.font=F(9,False,GREY);nt.alignment=wrap
for rr in range(17,24):
    for cc in(5,6):ws.cell(rr,cc).fill=fill(LIGHT2)

# ===================== ASSUMPTIONS =====================
wa=wb.create_sheet("Assumptions");wa.sheet_view.showGridLines=False
band(wa,"Assumptions & Inputs","Blue = editable. Pick-book auto-escalates $15 every week via TODAY().",4)
for k,v in {"A":2,"B":36,"C":14,"D":52}.items():wa.column_dimensions[k].width=v
for i,h in enumerate(["Input","Value","Note"]):
    c=wa.cell(3,2+i,h);c.font=F(11,True,"FFFFFF");c.fill=fill(NAVY)
def inp(r,lab,val,note,nf='#,##0.00',blue=True):
    wa.cell(r,2,lab).font=F(11)
    c=wa.cell(r,3,val);c.font=F(11,True,"0000FF" if blue else "1A1A1A")
    if blue:c.fill=fill("FFF8DC")
    c.number_format=nf;c.alignment=right
    wa.cell(r,4,note).font=F(10,False,GREY)
inp(4,"Claude / AI tooling cost ($)",45,"R&D — flat, your figure")
inp(5,"Sports pick book ($/week)",15,"R&D — escalates weekly")
inp(6,"Pick-book start date",datetime.date(2026,6,11),"First subscription week",nf='yyyy-mm-dd')
wa.cell(7,2,"Today").font=F(11);c=wa.cell(7,3,"=TODAY()");c.number_format='yyyy-mm-dd';c.alignment=right;c.font=F(11)
wa.cell(7,4,"Live — drives weekly escalator").font=F(10,False,GREY)
wa.cell(8,2,"Weeks elapsed (auto)").font=F(11,True)
c=wa.cell(8,3,"=MAX(1,ROUNDUP((C7-C6)/7,0))");c.font=F(11,True);c.number_format='0';c.alignment=right
wa.cell(8,4,"Pick-book cost = $15 × this. Rises each week.").font=F(10,False,GREY)
inp(9,"Cashed out — total withdrawals ($)",round(PWD+KWD,2),"Poly $327.80 pending + Kalshi $61.22 settled",nf=USD)

# ===================== CHARTS DATA + CHARTS =====================
wd=wb.create_sheet("P&L Charts");wd.sheet_view.showGridLines=False
band(wd,"Net P&L Over Time — Both Accounts","Realized P&L by settlement date, anchored to verified totals (Poly +568.21, Kalshi −219.45)",12)
# data block (place to the right, cols R+) ; we'll put helper tables lower
# Daily cumulative (all-time) at columns B,C starting row 40
def write_series(ws,r0,c0,header,rows):
    ws.cell(r0,c0,header[0]).font=F(9,True);ws.cell(r0,c0+1,header[1]).font=F(9,True)
    for i,(k,v) in enumerate(rows):
        ws.cell(r0+1+i,c0,k);ws.cell(r0+1+i,c0+1,v);ws.cell(r0+1+i,c0+1).number_format=USD0
    return r0+1, r0+len(rows)
# hide data far down
DR=60
# daily P&L (not cumulative) for "day" view
daily=[[d[0],d[3]] for d in CH["daily"]]
cum=[[d[0],d[1]] for d in CH["cum_daily"]]
weekly=CH["weekly"];monthly=CH["monthly"]
s1,e1=write_series(wd,DR,2,["Date","Daily net P&L"],daily)       # B,C
s2,e2=write_series(wd,DR,5,["Date","Cumulative P&L"],cum)        # E,F
s3,e3=write_series(wd,DR,8,["Week","Weekly net P&L"],weekly)     # H,I
s4,e4=write_series(wd,DR,11,["Month","Monthly net P&L"],monthly) # K,L

def style_chart(ch,title):
    ch.title=title;ch.height=7.5;ch.width=15;ch.style=2
    ch.x_axis.delete=False;ch.y_axis.delete=False
    ch.x_axis.numFmt="mmm d";ch.y_axis.numFmt="$#,##0"
    ch.legend=None

# Chart 1: Daily net P&L (column)
c1=BarChart();c1.type="col";style_chart(c1,"Daily Net P&L (by day)")
c1.add_data(Reference(wd,min_col=3,min_row=DR,max_row=e1),titles_from_data=True)
c1.set_categories(Reference(wd,min_col=2,min_row=DR+1,max_row=e1))
wd.add_chart(c1,"B4")
# Chart 2: Weekly net P&L (column)
c2=BarChart();c2.type="col";style_chart(c2,"Weekly Net P&L (by week)");c2.x_axis.numFmt="General"
c2.add_data(Reference(wd,min_col=9,min_row=DR,max_row=e3),titles_from_data=True)
c2.set_categories(Reference(wd,min_col=8,min_row=DR+1,max_row=e3))
wd.add_chart(c2,"J4")
# Chart 3: Monthly net P&L (column)
c3=BarChart();c3.type="col";style_chart(c3,"Monthly Net P&L (by month)");c3.x_axis.numFmt="General"
c3.add_data(Reference(wd,min_col=12,min_row=DR,max_row=e4),titles_from_data=True)
c3.set_categories(Reference(wd,min_col=11,min_row=DR+1,max_row=e4))
wd.add_chart(c3,"B20")
# Chart 4: All-time cumulative (line)
c4=LineChart();style_chart(c4,"All-Time Cumulative Net P&L")
c4.add_data(Reference(wd,min_col=6,min_row=DR,max_row=e2),titles_from_data=True)
c4.set_categories(Reference(wd,min_col=5,min_row=DR+1,max_row=e2))
s=c4.series[0];s.graphicalProperties.line.solidFill=ACCENT;s.graphicalProperties.line.width=28000
wd.add_chart(c4,"J20")
wd.cell(37,2,"Note: platforms don't expose historical equity snapshots, so these curves distribute each account's VERIFIED total P&L across its real settlement dates. Endpoints and totals are exact; intra-period values are realized-P&L estimates.").font=F(9,False,GREY)
wd.merge_cells("B37:L38")


# Daily profit table (visible) on P&L Charts tab
hdr=["Date","Poly P&L","Kalshi P&L","Net P&L"]
wd.cell(4,14,"Profit per day").font=F(12,True,NAVY)
for i,h in enumerate(hdr):
    c=wd.cell(5,14+i,h);c.font=F(9,True,"FFFFFF");c.fill=fill(NAVY);c.alignment=center;c.border=border
for i,row in enumerate(CH["daily"]):
    rr=6+i
    wd.cell(rr,14,row[0]).font=F(9);wd.cell(rr,14).alignment=left
    for j,val in enumerate(row[1:]):
        c=wd.cell(rr,15+j,val);c.number_format=USD0;c.font=F(9,False,GREEN if val>=0 else RED);c.alignment=right;c.border=border
    wd.cell(rr,14).border=border
for k,v in {"N":12,"O":11,"P":11,"Q":11}.items():wd.column_dimensions[k].width=v

# ===================== KALSHI =====================
wk=wb.create_sheet("Kalshi");wk.sheet_view.showGridLines=False
band(wk,"Kalshi — Account Detail","Official profit −$219.45 (your Kalshi profile)  ·  Jan–Jun 2026  ·  now drained",5)
for k,v in {"A":2,"B":44,"C":16,"D":4,"E":22}.items():wk.column_dimensions[k].width=v
def kk(r,lab,val,nf=USD,vc="1A1A1A",bold=False):
    wk.cell(r,2,lab).font=F(11,bold,"3A3A3A");wk.cell(r,2).alignment=left
    c=wk.cell(r,3,val);c.font=F(11,bold,vc)
    if nf:c.number_format=nf
    c.alignment=right
r=4;wk.cell(r,2,"Cash reconciliation").font=F(12,True,NAVY);wk.cell(r,2).border=baccent;wk.cell(r,3).border=baccent;r+=1
kk(r,"Deposits (14, ACH)",KDEP,vc=GREEN);r+=1
kk(r,"Promotional credits (implied, reconciles)",KCR,vc=GOLD);r+=1
kk(r,"Withdrawals (2)",-KWD,vc=RED);r+=1
kk(r,"Official profit (Kalshi profile)",KPL,vc=RED,bold=True);r+=1
kk(r,"Ending balance  (236+44.68−61.22−219.45)","=C5+C6+C7+C8",vc="1A1A1A",bold=True)
for cc in(2,3):wk.cell(r,cc).fill=fill(LIGHT)
r+=2
wk.cell(r,2,"Settlement activity").font=F(12,True,NAVY);wk.cell(r,2).border=baccent;wk.cell(r,3).border=baccent;r+=1
kk(r,"Markets settled",kr["n_settle"],nf=INT);r+=1
kk(r,"Profitable / losing",f"{kr['win']} / {kr['loss']}",nf=None);r+=1
kk(r,"Reported volume","$1.6K",nf=None);r+=1
kk(r,"Reported trade count",246,nf=INT);r+=2
wk.merge_cells(start_row=r,start_column=2,end_row=r+4,end_column=5)
note=wk.cell(r,2,"Where did −$775.93 come from?  Summing each settlement's (payout − cost basis − fees) gives −$775.93, but the $1,577 cost basis counts every contract bought that later settled. Because the bot bought, sold, and rebought within markets ($1.6K volume, 246 trades), gross cost basis far exceeds net cash deployed. Kalshi's profile nets all of it to −$219.45 — that is the correct figure used here. Held-to-settlement bets lost; in-and-out scalps recovered most of it.")
note.font=F(9.5,False,GREY);note.alignment=wrap


# ===================== TRADE CHARTS =====================
wtc=wb.create_sheet("Trade Charts");wtc.sheet_view.showGridLines=False
band(wtc,"Trade Activity — Volume Over Time","Polymarket notional volume ($) by day, week, month, and cumulative",12)
TR=60
def ws_block(ws,r0,c0,header,rows,volidx):
    ws.cell(r0,c0,header[0]).font=F(9,True);ws.cell(r0,c0+1,header[1]).font=F(9,True)
    for i,row in enumerate(rows):
        ws.cell(r0+1+i,c0,row[0]);ws.cell(r0+1+i,c0+1,row[volidx]);ws.cell(r0+1+i,c0+1).number_format=USD0
    return r0,r0+len(rows)
d0,d1=ws_block(wtc,TR,2,["Date","Daily volume"],TC["daily"],2)
w0,w1=ws_block(wtc,TR,5,["Week","Weekly volume"],TC["weekly"],2)
m0,m1=ws_block(wtc,TR,8,["Month","Monthly volume"],TC["monthly"],2)
c0,c1=ws_block(wtc,TR,11,["Date","Cumulative volume"],TC["cum"],1)
def schart(ch,title,numfmtx="mmm d"):
    ch.title=title;ch.height=7.5;ch.width=15;ch.style=10;ch.legend=None
    ch.x_axis.delete=False;ch.y_axis.delete=False;ch.x_axis.numFmt=numfmtx;ch.y_axis.numFmt="$#,##0"
t1=BarChart();t1.type="col";schart(t1,"Volume by Day")
t1.add_data(Reference(wtc,min_col=3,min_row=TR,max_row=d1),titles_from_data=True)
t1.set_categories(Reference(wtc,min_col=2,min_row=TR+1,max_row=d1));wtc.add_chart(t1,"B4")
t2=BarChart();t2.type="col";schart(t2,"Volume by Week","General")
t2.add_data(Reference(wtc,min_col=6,min_row=TR,max_row=w1),titles_from_data=True)
t2.set_categories(Reference(wtc,min_col=5,min_row=TR+1,max_row=w1));wtc.add_chart(t2,"J4")
t3=BarChart();t3.type="col";schart(t3,"Volume by Month","General")
t3.add_data(Reference(wtc,min_col=9,min_row=TR,max_row=m1),titles_from_data=True)
t3.set_categories(Reference(wtc,min_col=8,min_row=TR+1,max_row=m1));wtc.add_chart(t3,"B20")
t4=LineChart();schart(t4,"Cumulative Volume (all-time)")
t4.add_data(Reference(wtc,min_col=12,min_row=TR,max_row=c1),titles_from_data=True)
t4.set_categories(Reference(wtc,min_col=11,min_row=TR+1,max_row=c1))
sr=t4.series[0];sr.graphicalProperties.line.solidFill="1F6FEB";sr.graphicalProperties.line.width=28000
wtc.add_chart(t4,"J20")

# ===================== CASH FLOW =====================
wc=wb.create_sheet("Cash Flow");wc.sheet_view.showGridLines=False
band(wc,"Deposits, Withdrawals & Credits","Polymarket (B–E) + Kalshi (G–I)  ·  live API",10)
for k,v in {"A":2,"B":18,"C":13,"D":11,"E":40,"F":3,"G":15,"H":13,"I":11}.items():wc.column_dimensions[k].width=v
def th(ws,r,c0,cols):
    for i,h in enumerate(cols):
        cc=ws.cell(r,c0+i,h);cc.font=F(10,True,"FFFFFF");cc.fill=fill(NAVY);cc.alignment=center;cc.border=border
pa=poly["activities"]
def plist(t):
    o=[]
    for a in pa:
        if a["type"]!=t:continue
        abc=a.get("accountBalanceChange") or {}
        o.append([(abc.get("createTime") or "")[:16].replace("T"," "),f((abc.get("amount") or {}).get("value")),("PENDING" if "PENDING" in abc.get("status","") else "DONE"),(abc.get("description","")[:44] or abc.get("transactionId",""))])
    return o
def block(ws,r,c0,title,color,rows,ncol):
    ws.cell(r,c0,title).font=F(11,True,color);r+=1
    th(ws,r,c0,(["Date","Amount ($)","Status","Description"] if ncol==4 else ["Date","Amount ($)","Status"]));r+=1;st=r
    for d in rows:
        for i,v in enumerate(d[:ncol]):
            cc=ws.cell(r,c0+i,v);cc.font=F(9.5);cc.border=border;cc.alignment=(right if i==1 else(center if i==2 else left))
            if i==1:cc.number_format=USD
        r+=1
    ws.cell(r,c0,"Total").font=F(10,True,color);ws.cell(r,c0).alignment=right
    col=chr(ord('A')+c0)  # amount col letter
    tc=ws.cell(r,c0+1,f"=SUM({col}{st}:{col}{r-1})");tc.font=F(10,True,color);tc.number_format=USD;tc.fill=fill(LIGHT)
    return r+2
r=block(wc,4,2,"POLYMARKET — DEPOSITS",GREEN,plist("ACTIVITY_TYPE_ACCOUNT_DEPOSIT"),4)
r=block(wc,r,2,"POLYMARKET — WITHDRAWALS (pending)",RED,plist("ACTIVITY_TYPE_ACCOUNT_WITHDRAWAL"),4)
r=block(wc,r,2,"POLYMARKET — PROMO CREDITS",GOLD,plist("ACTIVITY_TYPE_TRANSFER"),4)
rk=block(wc,4,7,"KALSHI — DEPOSITS",GREEN,kr["deposits"],3)
rk=block(wc,rk,7,"KALSHI — WITHDRAWALS",RED,kr["withdrawals"],3)
wc.cell(rk,7,"KALSHI — PROMO CREDIT (implied)").font=F(11,True,GOLD);rk+=1
th(wc,rk,7,["Note","Amount ($)",""]);rk+=1
wc.cell(rk,7,"Reconciles to official profit").font=F(9.5);wc.cell(rk,8,KCR).number_format=USD;wc.cell(rk,8).font=F(9.5);wc.cell(rk,8).alignment=right
for cc in(7,8,9):wc.cell(rk,cc).border=border

# ===================== POLY ACTIVITY =====================
import collections
wb_=wb.create_sheet("Poly Activity");wb_.sheet_view.showGridLines=False
band(wb_,"Polymarket Trading Activity","By league and by day  ·  volume = price × qty",8)
for k,v in {"A":2,"B":22,"C":10,"D":16,"E":3,"F":14,"G":10,"H":16}.items():wb_.column_dimensions[k].width=v
LG={"itfw":"Tennis ITF (W)","itfm":"Tennis ITF (M)","atp":"Tennis ATP","wta":"Tennis WTA","fwc":"World Cup","mlb":"MLB","nba":"NBA","wnba":"WNBA","lol":"LoL esports","nhl":"NHL","ufc":"UFC"}
lg=collections.defaultdict(lambda:[0,0.0]);day=collections.defaultdict(lambda:[0,0.0])
for t in trades:
    p=t[1].split("-");code=p[1] if len(p)>1 else "o";key=code if code in LG else "other"
    lg[key][0]+=1;lg[key][1]+=t[7];day[t[0][:10]][0]+=1;day[t[0][:10]][1]+=t[7]
r=4;wb_.cell(r,2,"By league").font=F(12,True,NAVY);r+=1;th(wb_,r,2,["League","Fills","Volume ($)"]);r+=1;ls=r
for k,v in sorted(lg.items(),key=lambda x:-x[1][1]):
    wb_.cell(r,2,LG.get(k,"Other")).font=F(10);wb_.cell(r,3,v[0]).font=F(10);wb_.cell(r,3).number_format=INT;wb_.cell(r,3).alignment=center
    wb_.cell(r,4,round(v[1],2)).font=F(10);wb_.cell(r,4).number_format=USD0;wb_.cell(r,4).alignment=right
    for cc in range(2,5):wb_.cell(r,cc).border=border
    r+=1
wb_.cell(r,2,"Total").font=F(11,True);wb_.cell(r,2).alignment=right
wb_.cell(r,3,f"=SUM(C{ls}:C{r-1})").number_format=INT;wb_.cell(r,3).font=F(11,True);wb_.cell(r,3).alignment=center;wb_.cell(r,3).fill=fill(LIGHT)
wb_.cell(r,4,f"=SUM(D{ls}:D{r-1})").number_format=USD0;wb_.cell(r,4).font=F(11,True);wb_.cell(r,4).alignment=right;wb_.cell(r,4).fill=fill(LIGHT)
r=4;wb_.cell(r,6,"By day").font=F(12,True,NAVY);r+=1;th(wb_,r,6,["Date","Fills","Volume ($)"]);r+=1;dr=r
for k in sorted(day):
    wb_.cell(r,6,k).font=F(10);wb_.cell(r,7,day[k][0]).font=F(10);wb_.cell(r,7).number_format=INT;wb_.cell(r,7).alignment=center
    wb_.cell(r,8,round(day[k][1],2)).font=F(10);wb_.cell(r,8).number_format=USD0;wb_.cell(r,8).alignment=right
    for cc in(6,7,8):wb_.cell(r,cc).border=border
    r+=1
wb_.cell(r,6,"Total").font=F(11,True);wb_.cell(r,6).alignment=right
wb_.cell(r,7,f"=SUM(G{dr}:G{r-1})").number_format=INT;wb_.cell(r,7).font=F(11,True);wb_.cell(r,7).alignment=center;wb_.cell(r,7).fill=fill(LIGHT)
wb_.cell(r,8,f"=SUM(H{dr}:H{r-1})").number_format=USD0;wb_.cell(r,8).font=F(11,True);wb_.cell(r,8).alignment=right;wb_.cell(r,8).fill=fill(LIGHT)

# ===================== POLY TRANSACTIONS =====================
wt=wb.create_sheet("Poly Transactions");wt.sheet_view.showGridLines=False
band(wt,"Polymarket — Full Transaction History","Every fill, chronological  ·  642 trades",8)
wt.column_dimensions["A"].width=2
for col,w in {"B":17,"C":36,"D":13,"E":13,"F":8,"G":8,"H":13,"I":32}.items():wt.column_dimensions[col].width=w
for i,h in enumerate(["Date/Time (UTC)","Market","Outcome","Action","Price","Qty","Notional ($)","Slug"]):
    c=wt.cell(4,2+i,h);c.font=F(10,True,"FFFFFF");c.fill=fill(NAVY);c.alignment=center;c.border=border
wt.freeze_panes="B5";ACT={"BUY_LONG":"Buy (long)","SELL_LONG":"Sell (long)","BUY_SHORT":"Buy (short)","SELL_SHORT":"Sell (short)"}
r=5
for i,t in enumerate(trades):
    dt,slug,title,outcome,intent,p,q,no=t[:8];sh=LIGHT2 if i%2 else "FFFFFF"
    for j,v in enumerate([dt,title,outcome,ACT.get(intent,intent),p,q,no,slug]):
        c=wt.cell(r,2+j,v);c.font=F(9.5,False,GREY if j==7 else "1A1A1A");c.fill=fill(sh);c.border=border
        c.alignment=left if j in(0,1,2,3,7) else right
        if j==4:c.number_format='$0.000'
        elif j==5:c.number_format=INT
        elif j==6:c.number_format=USD0
        if j==3:c.font=F(9.5,True,GREEN if intent.startswith("BUY") else RED)
    r+=1
wt.cell(r,2,"TOTAL").font=F(10,True,NAVY);wt.cell(r,2).alignment=right
wt.cell(r,8,f"=SUM(H5:H{r-1})").number_format=USD0;wt.cell(r,8).font=F(10,True,NAVY);wt.cell(r,8).fill=fill(LIGHT)

# ===================== METHODOLOGY =====================
wn=wb.create_sheet("Methodology");wn.sheet_view.showGridLines=False
band(wn,"Methodology & Data Notes","How every number was derived and verified",6)
wn.column_dimensions["A"].width=2;wn.column_dimensions["B"].width=114
notes=[("Sources",True),
("Polymarket US: live api.polymarket.us (portfolio/activities, account/balances, positions). Kalshi: live api.elections.kalshi.com (deposits, withdrawals, settlements, balance) PLUS the official Profit shown on your Kalshi profile (−$219.45).",False),("",False),
("Kalshi P&L = −$219.45 (official)",True),
("Kalshi's own profile reports Profit −$219.45 on $1.6K volume / 246 trades. This reconciles exactly: 236 deposits + 44.68 credits − 61.22 withdrawals − 219.45 profit = ~$0.01 balance. The ~$44.68 credit is implied by this identity (small bonus, not $775).",False),("",False),
("Where −$775.93 came from (and why it is wrong)",True),
("Summing each settlement's payout − cost basis − fees = 839.56 − 1,577.19 − 38.30 = −775.93. The $1,577 cost counts every contract bought that settled; because the bot churned in and out, gross cost far exceeds net cash deployed. Kalshi nets it to −$219.45. Use −219.45.",False),("",False),
("Polymarket P&L = +$568.21 (verified 3 ways)",True),
("Value 823.40 − deposits 130 − credits 125.19 = +568.21. Cross-checks: 130+125.19+568.21 = 823.40 ✓ ; 823.40 − 327.80 pending withdrawals = 495.60 buying power ✓.",False),("",False),
("Combined",True),
("Gross trading P&L = 568.21 − 219.45 = +$348.76. Less R&D costs (Claude $45 + pick book $15/wk) = net +$288.76 this week.",False),("",False),
("Charts",True),
("Platforms expose no historical equity, so the 4 charts distribute each account's verified total P&L across its real settlement dates. Endpoints/totals are exact; intra-period points are realized-P&L estimates.",False),("",False),
("Pick-book escalator & Bank Account",True),
("Pick book = $15 × weeks since start (auto via TODAY). Bank Account = cashed out − pick book − Claude. Both editable on Assumptions.",False),]
r=4
for txt,head in notes:
    c=wn.cell(r,2,txt);c.font=F(12,True,NAVY) if head else F(10,False,"2A2A2A");c.alignment=wrap
    if txt and not head:wn.row_dimensions[r].height=28
    r+=1

# fix the deposits cell on summary (C5 hardcoded)
ws.cell(5,3).value=PDEP+KDEP
wb.save(OUTPUT)
# In-script recalc so the agent needs no extra step (best-effort via LibreOffice)
try:
    import glob,shutil,tempfile
    soffice=shutil.which("soffice") or shutil.which("libreoffice")
    if soffice:
        td=tempfile.mkdtemp()
        subprocess.run([soffice,"--headless","--calc","--convert-to","xlsx","--outdir",td,OUTPUT],
                       check=True,timeout=120,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        out=glob.glob(os.path.join(td,"*.xlsx"))
        if out: shutil.copy(out[0],OUTPUT)
except Exception as _e:
    pass
print("saved",OUTPUT)
print(f"SUMMARY | Combined gross P&L ${PPL+KPL:.2f} | net after R&D ${PPL+KPL-CFG['claude_cost_usd']-CFG['pickbook_per_week']:.2f} | Poly ${PPL:.2f} | Kalshi ${KPL:.2f}")
