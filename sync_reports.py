#!/usr/bin/env python3
"""Publish latest Meesho CSV reports from ~/Downloads to this public GitHub repository."""
import base64,getpass,re
from pathlib import Path
import requests
OWNER="jamwalnitin-prog"; REPO="meesho-seller-analytics"
SELLERS={"4079171":"NiviaSports","65448":"Ejaart","1184273":"PCP Enterprises","2501181":"Happy Heaven"}
API=f"https://api.github.com/repos/{OWNER}/{REPO}/contents"
DOWNLOADS=Path.home()/"Downloads"
token=getpass.getpass("GitHub fine-grained token (hidden input): ").strip()
if not token: raise SystemExit("No token supplied")
headers={"Authorization":f"Bearer {token}","Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28"}
for sid,name in SELLERS.items():
    files=[p for p in DOWNLOADS.glob("Orders_*.csv") if re.search(rf"_{sid}(?: \(\d+\))?\.csv$",p.name,re.I)]
    if not files: print(f"SKIP {name}: no CSV found"); continue
    p=max(files,key=lambda x:x.stat().st_mtime); path=f"data/{p.name}"
    old=requests.get(f"{API}/{path}",headers=headers,timeout=30)
    payload={"message":f"Publish latest {name} report","content":base64.b64encode(p.read_bytes()).decode(),"branch":"main"}
    if old.status_code==200: payload["sha"]=old.json()["sha"]
    elif old.status_code!=404: print(f"FAIL {name}: lookup HTTP {old.status_code}"); continue
    r=requests.put(f"{API}/{path}",headers=headers,json=payload,timeout=120)
    print(("OK " if r.ok else "FAIL ")+f"{name}: {p.name}"+("" if r.ok else f" (HTTP {r.status_code})"))
print("Upload complete. The CSVs in this PUBLIC repository are visible to anyone.")
