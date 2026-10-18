# Questionnaire JSON format — version 1.0

Each questionnaire is one JSON document. The authoritative definition is the JSON Schema (draft 2020-12) at
[`questionnaires/schema/questionnaire-1.0.schema.json`](../questionnaires/schema/questionnaire-1.0.schema.json),
also served by the app at `/api/schema/questionnaire-1.0.json`. This page explains it and lists the extra rules
that JSON Schema can't express.

## Example

```json
{
  "schemaVersion": "1.0",
  "id": "customer-feedback",
  "title": "Customer feedback",
  "description": "Tell us how we did.",
  "questions": [
    {
      "id": "satisfaction",
      "type": "single_choice",
      "text": "How satisfied are you?",
      "required": true,
      "options": [
        { "value": "very", "label": "Very satisfied" },
        { "value": "not", "label": "Not satisfied" }
      ]
    },
    { "id": "nps", "type": "scale", "text": "How likely are you to recommend us?", "min": 0, "max": 10,
      "minLabel": "Not likely", "maxLabel": "Very likely" },
    { "id": "comments", "type": "text", "text": "Anything else?", "multiline": true }
  ]
}
```

## Top level

| Field | Type | Required | Notes |
|---|---|---|---|
| `schemaVersion` | string | yes | Always `"1.0"` for this version. |
| `id` | identifier | yes | Unique across all questionnaires in the app. Used as the export file name. |
| `title` | string (1–200) | yes | |
| `description` | string (≤5000) | no | |
| `questions` | array of questions | yes | May be empty. Order is display order. |

No other fields are allowed.

An **identifier** starts with a letter, followed by up to 63 letters, digits, `_` or `-`
(regex `^[A-Za-z][A-Za-z0-9_-]{0,63}$`).

## Questions

Every question has these fields:

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | identifier | yes | Unique within the questionnaire. |
| `type` | string | yes | One of the types below. |
| `text` | string (1–1000) | yes | The question as shown to the respondent. |
| `help` | string (≤2000) | no | Extra guidance shown under the question. |
| `required` | boolean | no | Default `false`. |

Each type allows only the extra fields listed for it. A field that belongs to another type (for example
`options` on a `text` question) is rejected.

| `type` | Answer | Extra fields |
|---|---|---|
| `text` | Free text | `multiline` (boolean), `maxLength` (integer ≥ 1) |
| `number` | A number | `min`, `max` (numbers), `integer` (boolean: whole numbers only) |
| `single_choice` | One option | `options` (**required**, ≥ 2) |
| `multiple_choice` | Zero or more options | `options` (**required**, ≥ 2), `minSelections` (integer ≥ 0), `maxSelections` (integer ≥ 1) |
| `boolean` | Yes / no | — |
| `date` | A calendar date | — |
| `scale` | An integer between two bounds | `min`, `max` (**required** integers), `minLabel`, `maxLabel` (strings ≤ 100) |

An **option** is `{ "value": <identifier>, "label": <string 1–500> }`. `value` is the stable, machine-readable
answer; `label` is what the respondent sees.

## Extra rules (checked by the app, not by JSON Schema)

- Question `id`s are unique within a questionnaire.
- Option `value`s are unique within a question.
- Where both are given, `min` < `max` (`number` and `scale`).
- `maxSelections` is no greater than the number of options, and `minSelections` ≤ `maxSelections`.
- The top-level `id` is unique across the app.

These live in `questionnaires/validation.py`. Anyone validating exported files with a generic JSON Schema
validator should apply them as well.

## Versioning

`schemaVersion` names the version of this format. Adding optional fields or new question types is a minor
change (`1.1`). Removing or renaming fields, or tightening rules so that existing documents become invalid, is
a major change (`2.0`). Each version gets its own schema file, `questionnaire-<version>.schema.json`.
