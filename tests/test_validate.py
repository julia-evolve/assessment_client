from pathlib import Path

import pandas as pd
import pytest

from src.assessment_client.app import validate_competency_data


BASE_DIR = Path(__file__).resolve().parent
EXAMPLES_DIR = BASE_DIR / "examples"
MATRIX_EXAMPLE = EXAMPLES_DIR / "matrix_example.xlsx"
QA_EXAMPLE = EXAMPLES_DIR / "qa_example.xlsx"


def load_example_dataframes():
	"""Helper that always loads fresh copies of the example Excel files."""
	df_competency = pd.read_excel(MATRIX_EXAMPLE)
	df_qa = pd.read_excel(QA_EXAMPLE)
	return df_competency, df_qa


@pytest.fixture()
def example_dataframes():
	return load_example_dataframes()


def test_validate_competency_data_accepts_examples(example_dataframes):
	df_competency, df_qa = example_dataframes

	# Should not raise for the curated example spreadsheets
	validate_competency_data(df_competency.copy(), df_qa.copy())


def test_validate_competency_data_rejects_parentheses_in_matrix_name(example_dataframes):
	df_competency, df_qa = example_dataframes
	first_index = df_competency.index[0]
	original_name = df_competency.loc[first_index, 'name']
	df_competency.loc[first_index, 'name'] = f"{original_name} (комментарий)"

	with pytest.raises(ValueError, match="скобках"):
		validate_competency_data(df_competency.copy(), df_qa.copy())


def test_validate_competency_data_rejects_parentheses_in_qa_competencies(example_dataframes):
	df_competency, df_qa = example_dataframes
	first_index = df_qa.index[0]
	df_qa.loc[first_index, 'Компетенции'] = "Коммуникация (нельзя)"

	with pytest.raises(ValueError, match="скобках"):
		validate_competency_data(df_competency.copy(), df_qa.copy())


def test_validate_competency_data_detects_mismatched_names(example_dataframes):
	df_competency, df_qa = example_dataframes

	# QA mentions a competency absent from matrix
	df_qa.loc[df_qa.index[0], 'Компетенции'] = "Несуществующая компетенция"

	with pytest.raises(ValueError, match="без соответствий"):
		validate_competency_data(df_competency.copy(), df_qa.copy())

	# Matrix has an extra competency the QA file never references
	extra_row = {col: '' for col in df_competency.columns}
	extra_row['name'] = 'Лишняя компетенция'
	df_comp_with_extra = pd.concat([df_competency, pd.DataFrame([extra_row])], ignore_index=True)

	with pytest.raises(ValueError, match="которых нет в таблице ответов"):
		validate_competency_data(df_comp_with_extra, df_qa.copy())
