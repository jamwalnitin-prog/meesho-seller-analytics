import re
from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Meesho Seller Analytics",page_icon="📊",layout="wide")
ROOT=Path(__file__).parent
DATA=ROOT/"data"
SELLERS={"4079171":"NiviaSports","65448":"Ejaart","1184273":"PCP Enterprises","2501181":"Happy Heaven"}
PRICE="Supplier Discounted Price (Incl GST and Commision)"
LIST="Supplier Listed Price (Incl. GST + Commission)"
STATUS="Reason for Credit Entry"

def norm(df):
    df=df.copy()
    for c in [PRICE,LIST,"Quantity"]:
        if c in df: df[c]=pd.to_numeric(df[c],errors="coerce").fillna(0)
    if "Order Date" in df: df["Order Date"]=pd.to_datetime(df["Order Date"],errors="coerce",dayfirst=False)
    for c in ["Customer State","Product Name","SKU","Size","Order source",STATUS]:
        if c in df: df[c]=df[c].fillna("Unknown").astype(str).str.strip().replace("","Unknown")
    df["Order Status"]=df[STATUS].str.upper() if STATUS in df else "UNKNOWN"
    if "Sub Order No" in df: df=df.drop_duplicates(subset=["Sub Order No"],keep="last")
    return df

def money(v): return f"₹{v:,.0f}"
def rate(n,d): return n/d*100 if d else 0

st.title("Meesho Seller Analytics")
st.caption("Consolidated and account-wise reporting across four Meesho seller accounts")
parts=[]; files={}
for sid,name in SELLERS.items():
    matches=[p for p in DATA.glob("Orders_*.csv") if re.search(rf"_{sid}(?: \\(\\d+\\))?\\.csv$",p.name,re.I)]
    if matches:
        p=max(matches,key=lambda x:x.stat().st_mtime)
        try:
            d=norm(pd.read_csv(p))
            if not d.empty:
                d["_seller_id"]=sid;d["_seller"]=name;d["_file"]=p.name
                parts.append(d);files[sid]=p.name
        except Exception as e: st.error(f"{name}: unable to read {p.name}: {e}")
if not parts:
    st.warning("No reports published yet. Upload the latest seller CSVs to the repository data/ folder using sync_reports.py.")
    st.stop()
df=pd.concat(parts,ignore_index=True)
with st.expander("Seller accounts included",expanded=True):
    chosen=st.multiselect("Accounts",list(files),default=list(files),format_func=lambda x:f"{SELLERS[x]} ({x})")
df=df[df["_seller_id"].isin(chosen)]
if df.empty: st.stop()
with st.expander("Filters",expanded=True):
    a,b,c=st.columns(3)
    if "Order Date" in df and df["Order Date"].notna().any():
        dates=df["Order Date"].dropna()
        dr=a.date_input("Order date range",(dates.min().date(),dates.max().date()))
        if isinstance(dr,tuple) and len(dr)==2: df=df[df["Order Date"].dt.date.between(dr[0],dr[1])]
    states=sorted(df["Customer State"].unique()) if "Customer State" in df else []
    chosen_states=b.multiselect("Customer state",states,default=states)
    statuses=sorted(df["Order Status"].unique())
    chosen_status=c.multiselect("Order status",statuses,default=statuses)
    if "Customer State" in df: df=df[df["Customer State"].isin(chosen_states)]
    df=df[df["Order Status"].isin(chosen_status)]
orders=df["Sub Order No"].nunique() if "Sub Order No" in df else len(df)
units=df["Quantity"].sum() if "Quantity" in df else 0
value=df[PRICE].sum() if PRICE in df else 0
delivered=(df["Order Status"]=="DELIVERED").sum()
cancel=df["Order Status"].str.contains("CANCEL",na=False).sum()
rto=df["Order Status"].str.startswith("RTO",na=False).sum()
k=st.columns(5)
for col,label,val in zip(k,["Sub-orders","Units","Supplier discounted value","Delivered","Cancellation + RTO"],[f"{orders:,}",f"{units:,.0f}",money(value),f"{delivered:,}",f"{cancel+rto:,}"]): col.metric(label,val)
st.caption("Latest report files: "+" • ".join(f"{SELLERS[s]}: {files[s]}" for s in files if s in chosen))
st.info("Financial values are exported report fields, not confirmed payouts or profit. Cost, fees, logistics, ads and settlement data are not included.")
tabs=st.tabs(["Overview","Account-wise View","Sales & Growth","Products & SKUs","Fulfilment","Geography","Finance","Cancellation & RTO","Order Explorer","Seller Comparison"])
with tabs[0]:
    x,y=st.columns(2)
    x.subheader("Order status");x.bar_chart(df["Order Status"].value_counts())
    y.subheader("Top products by units")
    if "Product Name" in df: y.dataframe(df.groupby("Product Name").agg(Orders=("Sub Order No","nunique"),Units=("Quantity","sum")).sort_values("Units",ascending=False).head(15),use_container_width=True)
with tabs[1]:
    names=sorted(df["_seller"].unique())
    name=st.selectbox("Choose seller",names)
    d=df[df["_seller"]==name].copy()
    n=d["Sub Order No"].nunique() if "Sub Order No" in d else len(d)
    q=d["Quantity"].sum() if "Quantity" in d else 0
    v=d[PRICE].sum() if PRICE in d else 0
    dl=(d["Order Status"]=="DELIVERED").sum(); ca=d["Order Status"].str.contains("CANCEL",na=False).sum(); rt=d["Order Status"].str.startswith("RTO",na=False).sum()
    cols=st.columns(5)
    for col,l,val in zip(cols,["Sub-orders","Units","Discounted value","Delivered","Cancel + RTO"],[f"{n:,}",f"{q:,.0f}",money(v),f"{dl:,}",f"{ca+rt:,}"]):col.metric(l,val)
    st.caption(f"Seller ID: {d['_seller_id'].iloc[0]} • Report: {d['_file'].iloc[0]}")
    x,y=st.columns(2);x.bar_chart(d["Order Status"].value_counts())
    if "Product Name" in d:y.dataframe(d.groupby("Product Name").agg(Units=("Quantity","sum")).sort_values("Units",ascending=False).head(15),use_container_width=True)
    if "Customer State" in d: st.dataframe(d.groupby("Customer State").agg(Orders=("Sub Order No","nunique"),Units=("Quantity","sum")).sort_values("Orders",ascending=False),use_container_width=True)
    st.dataframe(d,use_container_width=True,hide_index=True)
    st.download_button("Download seller report",d.to_csv(index=False).encode("utf-8-sig"),f"{name.lower().replace(' ','_')}_orders.csv","text/csv")
with tabs[2]:
    if "Order Date" in df and df["Order Date"].notna().any():
        t=df.dropna(subset=["Order Date"]).groupby(df.dropna(subset=["Order Date"])["Order Date"].dt.date).agg(Orders=("Sub Order No","nunique"),Units=("Quantity","sum"))
        st.line_chart(t)
    if "Order source" in df: st.bar_chart(df["Order source"].value_counts())
with tabs[3]:
    if "Product Name" in df: st.dataframe(df.groupby("Product Name").agg(Orders=("Sub Order No","nunique"),Units=("Quantity","sum"),Discounted_Value=(PRICE,"sum")).sort_values("Units",ascending=False),use_container_width=True)
    if "SKU" in df: st.dataframe(df.groupby(["SKU"]+(["Size"] if "Size" in df else [])).agg(Units=("Quantity","sum")).sort_values("Units",ascending=False),use_container_width=True)
with tabs[4]:
    st.bar_chart(df["Order Status"].value_counts())
    st.dataframe(df.groupby("Order Status").agg(Orders=("Sub Order No","nunique"),Units=("Quantity","sum")).sort_values("Orders",ascending=False),use_container_width=True)
with tabs[5]:
    if "Customer State" in df: st.dataframe(df.groupby("Customer State").agg(Orders=("Sub Order No","nunique"),Units=("Quantity","sum"),Discounted_Value=(PRICE,"sum")).sort_values("Orders",ascending=False),use_container_width=True)
with tabs[6]:
    listed=df[LIST].sum() if LIST in df else 0
    st.metric("Supplier listed value",money(listed));st.metric("Supplier discounted value",money(value))
    st.caption("Difference between exported price fields is not profit, margin, realised revenue or settlement.")
with tabs[7]:
    st.metric("Cancelled",f"{cancel:,}",f"{rate(cancel,orders):.1f}%")
    st.metric("RTO",f"{rto:,}",f"{rate(rto,orders):.1f}%")
    risk=df[df["Order Status"].str.contains("CANCEL|RTO|RETURN",case=False,na=False)]
    if "Product Name" in risk:st.dataframe(risk.groupby("Product Name").size().sort_values(ascending=False).head(20))
with tabs[8]:
    q=st.text_input("Search order, SKU, product, state or packet ID")
    d=df.copy()
    if q:
        mask=pd.Series(False,index=d.index)
        for col in ["Sub Order No","SKU","Product Name","Customer State","Packet Id"]:
            if col in d:mask|=d[col].astype(str).str.contains(q,case=False,na=False)
        d=d[mask]
    st.dataframe(d,use_container_width=True,hide_index=True)
    st.download_button("Download filtered orders",d.to_csv(index=False).encode("utf-8-sig"),"filtered_orders.csv","text/csv")
with tabs[9]:
    rows=[]
    for sid,g in df.groupby(["_seller_id","_seller"]):
        rows.append({"Seller":sid[1],"Seller ID":sid[0],"Sub-orders":g["Sub Order No"].nunique(),"Units":g["Quantity"].sum(),"Discounted value":g[PRICE].sum(),"Delivered":(g["Order Status"]=="DELIVERED").sum(),"Cancelled":g["Order Status"].str.contains("CANCEL",na=False).sum(),"RTO":g["Order Status"].str.startswith("RTO",na=False).sum()})
    st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
st.caption("Each seller uses its latest published report. Reports are snapshots; differing date ranges can make comparisons misleading. This public dashboard contains order-level data from its public repository.")
