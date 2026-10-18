"""Validation of questionnaire documents against the 1.0 JSON Schema.

JSON Schema covers structure and types. The checks it can't express
(unique ids, min <= max, ...) live in ``_semantic_errors``.
"""

import json
from functools import cache
from pathlib import Path

from jsonschema import Draft202012Validator

SCHEMA_VERSION = '1.0'
SCHEMA_PATH = Path(__file__).parent / 'schema' / f'questionnaire-{SCHEMA_VERSION}.schema.json'


@cache
def load_schema():
    return json.loads(SCHEMA_PATH.read_text())


@cache
def _validator():
    schema = load_schema()
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _path(parts):
    """Render a JSON path such as ``questions[2].options[0].value``."""
    out = ''
    for part in parts:
        out += f'[{part}]' if isinstance(part, int) else (f'.{part}' if out else str(part))
    return out or '(root)'


def _semantic_errors(data):
    errors = []
    seen_questions = set()
    for i, question in enumerate(data.get('questions', [])):
        where = f'questions[{i}]'
        qid = question.get('id')
        if qid in seen_questions:
            errors.append(f"{where}.id: duplicate question id '{qid}'")
        seen_questions.add(qid)

        lo, hi = question.get('min'), question.get('max')
        if lo is not None and hi is not None and lo >= hi:
            errors.append(f'{where}: min must be less than max')

        options = question.get('options', [])
        seen_values = set()
        for j, option in enumerate(options):
            if option.get('value') in seen_values:
                errors.append(f"{where}.options[{j}].value: duplicate option value '{option['value']}'")
            seen_values.add(option.get('value'))

        min_sel, max_sel = question.get('minSelections'), question.get('maxSelections')
        if max_sel is not None and max_sel > len(options):
            errors.append(f'{where}.maxSelections: cannot exceed the number of options')
        if min_sel is not None and max_sel is not None and min_sel > max_sel:
            errors.append(f'{where}: minSelections must not exceed maxSelections')
    return errors


def validate_questionnaire(data):
    """Return a list of human-readable error strings; empty means valid."""
    errors = [
        f'{_path(err.absolute_path)}: {err.message}'
        for err in sorted(_validator().iter_errors(data), key=lambda e: list(map(str, e.absolute_path)))
    ]
    # Semantic checks assume the structure is sound.
    if not errors:
        errors = _semantic_errors(data)
    return errors
