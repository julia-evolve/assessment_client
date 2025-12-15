import streamlit as st

from assessment_client.pages.assessment_report import render as render_assessment_report
from assessment_client.pages.matrix_competencies import render as render_matrix_competencies

st.set_page_config(
    page_title="Assessment Client",
    layout="wide"
)

PAGES = {
    "Матрица компетенций": render_matrix_competencies,
    "Отчёт по оценке": render_assessment_report,
}


def main():
    st.title("Домашняя страница Assessment Client")
    st.markdown("Выберите страницу для перехода в боковом меню.")


if __name__ == "__main__":
    main()
