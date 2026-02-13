import pandas as pd
import streamlit as st
import re


def clean_text(text: str) -> str:
    if text is None:
        return ''
    # Remove leading/trailing whitespace and replace multiple spaces with a single space
    cleaned = re.sub(r'\s+', ' ', str(text)).strip()
    cleaned = cleaned.replace('_x000D_', '')
    return cleaned

def normalize_spaces(text: str) -> str:
    if text is None:
        return ''
    return re.sub(r'\s+', ' ', str(text)).strip()


def drop_rows_with_nan(df: pd.DataFrame, required_cols, dataset_name: str) -> pd.DataFrame:
    missing_columns = [col for col in required_cols if col not in df.columns]
    if missing_columns:
        raise ValueError(f"{dataset_name}: отсутствуют обязательные колонки: {', '.join(missing_columns)}")

    rows_to_drop = []
    for idx, row in df.iterrows():
        nan_columns = [col for col in required_cols if pd.isna(row[col])]
        if nan_columns:
            rows_to_drop.append((idx, nan_columns))

    if not rows_to_drop:
        return df

    for idx, nan_columns in rows_to_drop:
        excel_row_number = idx + 2  # +2 to account for header row in Excel export
        st.warning(
            f"{dataset_name}: строка {excel_row_number} удалена из-за NaN в колонках: "
            + ", ".join(nan_columns)
        )

    cleaned_df = df.drop(index=[idx for idx, _ in rows_to_drop]).reset_index(drop=True)
    return cleaned_df


def validate_competency_data(df_competency: pd.DataFrame, df_qa: pd.DataFrame):
    errors = []

    if 'competency' not in df_competency.columns:
        errors.append("В матрице компетенций отсутствует колонка 'competency'.")
        matrix_names = pd.Series(dtype=str)
    else:
        matrix_names = df_competency['competency'].fillna('').astype(str).map(normalize_spaces)

        comma_mask = matrix_names.str.contains(',', regex=False)
        if comma_mask.any():
            rows = [str(i + 2) for i in matrix_names[comma_mask].index[:5]]
            offending = matrix_names[comma_mask].unique().tolist()
            errors.append(
                f"Матрица компетенций, строки {', '.join(rows)}: запрещены запятые в названии. Исправьте: "
                + ", ".join(offending[:5])
                + (" ..." if len(offending) > 5 else "")
            )

        parentheses_mask = matrix_names.str.contains(r'[()]', regex=True)
        if parentheses_mask.any():
            rows = [str(i + 2) for i in matrix_names[parentheses_mask].index[:5]]
            offending = matrix_names[parentheses_mask].unique().tolist()
            errors.append(
                f"Матрица компетенций, строки {', '.join(rows)}: уберите текст в скобках из 'competency'. Найдены: "
                + ", ".join(offending[:5])
                + (" ..." if len(offending) > 5 else "")
            )

        empty_mask = matrix_names.eq('')
        if empty_mask.any():
            rows = [str(i + 2) for i in matrix_names[empty_mask].index[:5]]
            errors.append(
                f"Матрица компетенций, строки {', '.join(rows)}: пустые значения в колонке 'competency'."
            )

    if 'Компетенции' not in df_qa.columns:
        errors.append("В таблице ответов отсутствует колонка 'Компетенции'.")
        qa_competencies_series = pd.Series(dtype=str)
    else:
        qa_competencies_series = df_qa['Компетенции'].fillna('').astype(str).map(normalize_spaces)

        qa_parentheses_mask = qa_competencies_series.str.contains(r'[()]', regex=True)
        if qa_parentheses_mask.any():
            offending_rows = df_qa.loc[qa_parentheses_mask, ['Email', 'Компетенции']]
            details = "; ".join(
                f"Email {row.get('Email', 'N/A')}: {row['Компетенции']}" for _, row in offending_rows.head(5).iterrows()
            )
            if len(offending_rows) > 5:
                details += " ..."
            errors.append(
                "Уберите текст в скобках в колонке 'Компетенции' таблицы ответов. Примеры: " + details
            )

    qa_competency_names = set()
    for value in qa_competencies_series:
        if not value:
            continue
        parts = [part.strip() for part in value.split(',') if part.strip()]
        qa_competency_names.update(parts)

    matrix_name_set = set(matrix_names[matrix_names != ''])

    missing_in_matrix = sorted(qa_competency_names - matrix_name_set)
    # missing_in_qa = sorted(matrix_name_set - qa_competency_names)

    if missing_in_matrix:
        errors.append(
            "В таблице ответов найдены компетенции без соответствий в матрице: "
            + ", ".join(missing_in_matrix)
        )
    # if missing_in_qa:
    #     errors.append(
    #         "В матрице компетенций есть названия, которых нет в таблице ответов: "
    #         + ", ".join(missing_in_qa)
    #     )

    if errors:
        raise ValueError("\n".join(errors))
