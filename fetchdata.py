import datetime as dt
import os
import sqlite3
from pathlib import Path

import requests
from dotenv import load_dotenv

MAPP = Path(__file__).parent
load_dotenv(MAPP / ".env")

API_URL = "https://api.wheretheiss.at/v1/satellites/25544"


def hamta():
    svar = requests.get(API_URL, timeout=30)
    svar.raise_for_status()
    d = svar.json()
    tidpunkt = dt.datetime.fromtimestamp(d["timestamp"], dt.timezone.utc)
    return (
        tidpunkt.strftime("%Y-%m-%d %H:%M:%S"),
        d["latitude"],
        d["longitude"],
        d["altitude"],
        d["velocity"],
        d["visibility"],
    )


def spara_sqlite(rad):
    con = sqlite3.connect(MAPP / "data.db")
    con.execute("""
        CREATE TABLE IF NOT EXISTS iss_position (
            id            INTEGER PRIMARY KEY,
            tidpunkt      TEXT NOT NULL UNIQUE,
            latitud       REAL NOT NULL,
            longitud      REAL NOT NULL,
            hojd_km       REAL NOT NULL,
            hastighet_kmh REAL NOT NULL,
            synlighet     TEXT NOT NULL
        )""")
    con.execute("""
        INSERT OR IGNORE INTO iss_position
            (tidpunkt, latitud, longitud, hojd_km, hastighet_kmh, synlighet)
        VALUES (?, ?, ?, ?, ?, ?)""", rad)
    con.commit()
    antal = con.execute("SELECT COUNT(*) FROM iss_position").fetchone()[0]
    con.close()
    return antal


def spara_mariadb(rad):
    import pymysql

    con = pymysql.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", "3306")),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASS"],
        database=os.environ["DB_NAME"],
    )
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS iss_position (
            id            INT AUTO_INCREMENT PRIMARY KEY,
            tidpunkt      DATETIME NOT NULL UNIQUE,
            latitud       DOUBLE NOT NULL,
            longitud      DOUBLE NOT NULL,
            hojd_km       DOUBLE NOT NULL,
            hastighet_kmh DOUBLE NOT NULL,
            synlighet     VARCHAR(20) NOT NULL
        )""")
    cur.execute("""
        INSERT IGNORE INTO iss_position
            (tidpunkt, latitud, longitud, hojd_km, hastighet_kmh, synlighet)
        VALUES (%s, %s, %s, %s, %s, %s)""", rad)
    con.commit()
    cur.execute("SELECT COUNT(*) FROM iss_position")
    antal = cur.fetchone()[0]
    con.close()
    return antal


if __name__ == "__main__":
    rad = hamta()
    if os.environ.get("DB_HOST"):
        antal = spara_mariadb(rad)
        mal = "MariaDB"
    else:
        antal = spara_sqlite(rad)
        mal = "SQLite"
    print(f"Sparade {rad} i {mal}. Tabellen har nu {antal} rader.")
