
from pathlib import Path
import streamlit as st

def download_example_button(
        path: str, 
        file_name: str = "statements_example.xlsx",
        label: str = "📥 Скачать пример",
    ):
    example_file_path = Path(path)
    if example_file_path.exists():
        with open(example_file_path, "rb") as f:
            st.download_button(
                label=label,
                data=f,
                file_name=file_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
