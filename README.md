# Meesho Seller Analytics

Public read-only Streamlit dashboard for NiviaSports (4079171), Ejaart (65448), PCP Enterprises (1184273) and Happy Heaven (2501181).

## Deploy
On Streamlit Community Cloud, deploy this repository, branch `main`, file `app.py`.

## Publish reports
The dashboard reads the newest matching CSV per seller from `data/`. Run `python3 sync_reports.py` on the Mac after Meesho exports have downloaded. The script asks for a GitHub fine-grained token with Contents: Read and write permission. The token is entered invisibly and is not saved.

## Privacy
This repository is PUBLIC. Every uploaded CSV, including order-level fields, is publicly accessible. Do not upload credentials, local bridge files, extension files, tokens, or passwords. Meesho export automation remains on the Mac; this cloud dashboard is read-only.
