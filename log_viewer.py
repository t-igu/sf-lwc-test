import streamlit as st
import duckdb
import json
from pathlib import Path

LOG_DIR = Path("C:/workspace/python/github_projects/sf-lwc-test/logs/*.log")

st.title("Worker Log Viewer (DuckDB + Streamlit)")

con = duckdb.connect()

# JSON を flatten して読み込む
df = con.sql(f"""
    SELECT
        *
    FROM read_json_auto('{LOG_DIR.as_posix()}',
        maximum_depth=5,
        ignore_errors=true
    )
""").df()

# object 型を全部文字列化（Streamlit 対策）
for col in df.columns:
    if df[col].dtype == "object":
        df[col] = df[col].astype(str)

st.dataframe(df)
