import copy
import json

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase

from .models import Questionnaire
from .validation import validate_questionnaire

VALID = {
    'schemaVersion': '1.0',
    'id': 'customer-feedback',
    'title': 'Customer feedback',
    'description': 'Tell us how we did.',
    'questions': [
        {'id': 'name', 'type': 'text', 'text': 'Your name', 'required': False, 'maxLength': 100},
        {'id': 'age', 'type': 'number', 'text': 'Age', 'min': 0, 'max': 130, 'integer': True},
        {
            'id': 'satisfaction', 'type': 'single_choice', 'text': 'How satisfied are you?', 'required': True,
            'options': [{'value': 'yes', 'label': 'Very'}, {'value': 'no', 'label': 'Not at all'}],
        },
        {
            'id': 'channels', 'type': 'multiple_choice', 'text': 'How did you hear about us?',
            'options': [{'value': 'web', 'label': 'Web'}, {'value': 'friend', 'label': 'A friend'}],
            'maxSelections': 2,
        },
        {'id': 'recommend', 'type': 'boolean', 'text': 'Would you recommend us?'},
        {'id': 'visited', 'type': 'date', 'text': 'When did you visit?'},
        {'id': 'nps', 'type': 'scale', 'text': 'Rate us', 'min': 0, 'max': 10, 'minLabel': 'Bad'},
    ],
}


def variant(mutate):
    data = copy.deepcopy(VALID)
    mutate(data)
    return data


class ValidationTests(TestCase):
    def assertInvalid(self, data, fragment):
        errors = validate_questionnaire(data)
        self.assertTrue(any(fragment in e for e in errors), errors)

    def test_valid_document(self):
        self.assertEqual(validate_questionnaire(VALID), [])

    def test_empty_questionnaire_is_valid(self):
        self.assertEqual(validate_questionnaire(variant(lambda d: d.update(questions=[]))), [])

    def test_missing_title(self):
        self.assertInvalid(variant(lambda d: d.pop('title')), "'title' is a required property")

    def test_wrong_schema_version(self):
        self.assertInvalid(variant(lambda d: d.update(schemaVersion='2.0')), 'schemaVersion')

    def test_bad_identifier(self):
        self.assertInvalid(variant(lambda d: d.update(id='1 bad id')), 'id')

    def test_unknown_question_type(self):
        self.assertInvalid(variant(lambda d: d['questions'][0].update(type='slider')), 'questions[0].type')

    def test_property_from_another_type_is_rejected(self):
        self.assertInvalid(variant(lambda d: d['questions'][0].update(options=[])), 'Unevaluated properties')

    def test_choice_needs_two_options(self):
        self.assertInvalid(variant(lambda d: d['questions'][2]['options'].pop()), 'questions[2].options')

    def test_scale_requires_bounds(self):
        self.assertInvalid(variant(lambda d: d['questions'][6].pop('max')), "'max' is a required property")

    def test_duplicate_question_ids(self):
        self.assertInvalid(variant(lambda d: d['questions'][1].update(id='name')), "duplicate question id 'name'")

    def test_duplicate_option_values(self):
        self.assertInvalid(
            variant(lambda d: d['questions'][2]['options'][1].update(value='yes')), "duplicate option value 'yes'")

    def test_min_not_less_than_max(self):
        self.assertInvalid(variant(lambda d: d['questions'][6].update(min=10)), 'min must be less than max')

    def test_max_selections_exceeds_options(self):
        self.assertInvalid(variant(lambda d: d['questions'][3].update(maxSelections=3)), 'maxSelections')


class ApiTests(APITestCase):
    url = reverse('questionnaire-list')

    def test_create_and_retrieve(self):
        response = self.client.post(self.url, {'data': VALID}, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['slug'], 'customer-feedback')
        self.assertEqual(response.data['title'], 'Customer feedback')

        detail = self.client.get(reverse('questionnaire-detail', args=[response.data['id']]))
        self.assertEqual(detail.data['data'], VALID)

    def test_invalid_document_is_rejected(self):
        response = self.client.post(self.url, {'data': variant(lambda d: d.pop('questions'))}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn("'questions' is a required property", str(response.data['data']))
        self.assertFalse(Questionnaire.objects.exists())

    def test_duplicate_id_is_rejected(self):
        self.client.post(self.url, {'data': VALID}, format='json')
        response = self.client.post(self.url, {'data': VALID}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('already exists', str(response.data['data']))

    def test_update_keeps_own_id_and_syncs_title(self):
        pk = self.client.post(self.url, {'data': VALID}, format='json').data['id']
        updated = variant(lambda d: d.update(title='Renamed'))
        response = self.client.put(reverse('questionnaire-detail', args=[pk]), {'data': updated}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(Questionnaire.objects.get(pk=pk).title, 'Renamed')

    def test_export_downloads_json_file(self):
        pk = self.client.post(self.url, {'data': VALID}, format='json').data['id']
        response = self.client.get(reverse('questionnaire-export', args=[pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Disposition'], 'attachment; filename="customer-feedback.json"')
        self.assertEqual(json.loads(response.content), VALID)

    def test_schema_endpoint(self):
        response = self.client.get(reverse('questionnaire-schema'))
        self.assertEqual(response.json()['title'], 'Questionnaire')


class PageTests(TestCase):
    def test_pages_render(self):
        q = Questionnaire.objects.create(data=VALID)
        for url in [reverse('questionnaire-list-page'), reverse('builder-new'), reverse('builder-edit', args=[q.pk])]:
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_new_builder_passes_null_pk(self):
        response = self.client.get(reverse('builder-new'))
        self.assertContains(response, '<script id="questionnaire-pk" type="application/json">null</script>', html=True)
