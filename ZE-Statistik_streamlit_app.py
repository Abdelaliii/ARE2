import streamlit as st
import pandas as pd
import requests
from requests_ntlm import HttpNtlmAuth
from sqlalchemy import create_engine
from datetime import date
import time

st.title("📥 NEVARIS Datenabruf")

# Eingaben
st.sidebar.header("🔐 Zugangsdaten & Einstellungen")

username = st.sidebar.text_input("Benutzername", value="SYSTEEX\\Abdelali.Elyoussfi")
password = st.sidebar.text_input("Passwort", type="password")
mandanten = st.sidebar.multiselect("Mandanten", [10, 11, 12, 13, 14, 15, 16, 18, 21, 24, 25, 26, 27, 29, 30, 32, 99], default=[32])
start_date = st.sidebar.date_input("Startdatum", value=pd.to_datetime("2025-04-01"))
end_date = st.sidebar.date_input("Enddatum", value=pd.to_datetime("2025-12-31"))

run = st.button("🔄 Daten abrufen")

if run:
    start_time = time.time()
    heute = date.today().isoformat()
    auth = HttpNtlmAuth(username, password)
    headers = {"Accept": "application/json"}

    pg_conn_str = "postgresql+psycopg2://postgres:RnR3G9cDzMxyRLfzeA6f@10.101.53.155:5432/Spielwiese"
    engine = create_engine(pg_conn_str)

    # Endpunkte (hier nur ohne Datum als Beispiel)
    endpunkte = {
        "debitorenuebersicht_od_export": "debuebersicht",
        "op_sachpostenreferenz_od_export": "opsachpostenreferenz",
    }

    def daten_importieren(url_basis, mandant, tabellenname):
        all_records = []
        url = url_basis
        while url:
            response = requests.get(url, auth=auth, headers=headers)
            if response.status_code == 200:
                payload = response.json()
                records = payload.get("value", [])
                for r in records:
                    r["Mandant"] = mandant
                all_records.extend(records)
                url = payload.get("@odata.nextLink", None)
            else:
                st.error(f"❌ Fehler bei {tabellenname} (Mandant {mandant}): {response.status_code}")
                return []
        return all_records

    with st.spinner("Lade Daten..."):
        for tabellenname, endpoint in endpunkte.items():
            all_data = []
            for mandant in mandanten:
                base_url = f"http://are-hu-nvms:8048/INTEGRATION/ODataV4/Company('{mandant}')/{endpoint}"
                data = daten_importieren(base_url, mandant, endpoint)
                for d in data:
                    d["Stichtag"] = heute
                all_data.extend(data)

            if all_data:
                df = pd.DataFrame(all_data)
                df.to_sql(tabellenname, engine, if_exists="append", index=False)
                st.success(f"{tabellenname}: {len(df)} Zeilen gespeichert.")
            else:
                st.warning(f"⚠️ Keine Daten für '{tabellenname}'.")

    st.success(f"✅ Fertig in {int(time.time() - start_time)} Sekunden")
