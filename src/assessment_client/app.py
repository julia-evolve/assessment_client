import pandas as pd
import streamlit as st

from assessment_client.pages.assessment_report import render as render_assessment_report
from assessment_client.pages.matrix_competencies import render as render_matrix_competencies
from assessment_client.pages.create_assessment import render as render_create_assessment

st.set_page_config(
    page_title="Assessment Client",
    layout="wide"
)

PAGES = {
    "Матрица компетенций": render_matrix_competencies,
    "Отчёт по оценке": render_assessment_report,
    "Создание ассессмента": render_create_assessment,
}

# Пути к примерам файлов
ANSWERS_EXAMPLE_PATH = "src/assessment_client/examples/answers.xlsx"
LOGIC_EXAMPLE_PATH = "src/assessment_client/examples/logic.xlsx"
MATRIX_EXAMPLE_PATH = "src/assessment_client/examples/matrix.xlsx"


def load_example_metadata():
    """Загружает метаданные из примеров Excel-файлов."""
    answers_df = pd.read_excel(ANSWERS_EXAMPLE_PATH, sheet_name="Результаты участников")
    logic_df = pd.read_excel(LOGIC_EXAMPLE_PATH)
    matrix_df = pd.read_excel(MATRIX_EXAMPLE_PATH)

    return {
        "question_types": answers_df["Название главы"].unique().tolist(),
        "answers_columns": answers_df.columns.tolist(),
        "logic_columns": logic_df.columns.tolist(),
        "matrix_columns": matrix_df.columns.tolist()
    }


def format_column_list(columns: list) -> str:
    """Форматирует список колонок для отображения в markdown."""
    return " | ".join(f"`{col}`" for col in columns)


def format_bullet_list(items: list) -> str:
    """Форматирует список элементов как markdown bullet list."""
    return "\n".join(f"- **{item}**" for item in items)


def render_instructions(metadata: dict):
    """Отображает памятку по заполнению таблиц."""
    question_types = metadata["question_types"]
    answers_columns = metadata["answers_columns"]
    logic_columns = metadata["logic_columns"]
    matrix_columns = metadata["matrix_columns"]

    st.markdown(f"""
## ⚠️ ОБЯЗАТЕЛЬНО К ПРОЧТЕНИЮ

---

## Колонки в таблице — **СТРОГО как в примере**
❗ **Названия колонок должны совпадать с примером 1-в-1, посимвольно**.  
🧨 **Даже одно отличие в названии колонки может сломать обработку данных.**

---

### Обязательные колонки в файле **Answers** (лист «Результаты участников»):

{format_column_list(answers_columns)}

---

### Обязательные колонки в файле **Logic**:

{format_column_list(logic_columns)}

⚠️ Одна строка - одна компетенция. Если вопрос относится к нескольким компетенциям, необходимо продублировать строку и указать другую компетенцию.  
⚠️ Индикаторы для компетенции необходимо разделить `;` + новой строкой.  
🧨 Индикаторы должны буква-в-букву совпадать с названием индикатора в матрице компетенций.

---
### Обязательные колонки в файле **Matrix**:

{format_column_list(matrix_columns)}  
🧩 Если нет индикаторов необходимо скопировать название компетенции и описания в индикатор


---

## Название главы — **строго {len(question_types)} допустимых вариантов**
Название главы **может быть только одно из следующих**:

{format_bullet_list(question_types)}

🚫 **Любые другие названия глав недопустимы.**  
🚫 **Нельзя изменять формулировки, порядок слов или регистр.**

---

## ✅ Коротко главное
- 🧱 Колонки — **строго как в примере**
- 🧩 Главы — **только {len(question_types)} допустимых**
- 💙 Одна строка — одна компетенция  
- 🧠 Индикаторы — разделены `;`+ новой строкой
- 📝 Детали — **в комментариях**

""")


def main():
    st.title("Домашняя страница Assessment Client")
    st.markdown("Выберите страницу для перехода в боковом меню.")

    metadata = load_example_metadata()
    render_instructions(metadata)

if __name__ == "__main__":
    main()
