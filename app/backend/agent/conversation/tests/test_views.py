from conversation.models import Conversation, ConversationMetadata
from django.test import TestCase
from rest_framework.test import APIClient


class ConversationViewTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = '/conversations/'

    def test_get_conversations_empty(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_get_conversations(self):
        conv1 = Conversation.objects.create(name='conv1')
        conv2 = Conversation.objects.create(name='conv2')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)
        self.assertTrue(any(c['id'] == conv1.id for c in response.json()))
        self.assertTrue(any(c['id'] == conv2.id for c in response.json()))

    def test_get_conversations_excludes_deleted(self):
        active = Conversation.objects.create(name='active')
        deleted = Conversation.objects.create(name='deleted')
        deleted.delete()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['id'], active.id)

    def test_post_conversation(self):
        response = self.client.post(self.url, {'name': 'new conv'}, format='json')
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['name'], 'new conv')
        self.assertTrue(Conversation.objects.filter(id=data['id']).exists())

    def test_post_conversation_missing_name(self):
        response = self.client.post(self.url, {}, format='json')
        self.assertEqual(response.status_code, 400)


class ConversationDetailViewTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.conversation = Conversation.objects.create(name='test conv')
        self.url = f'/conversations/{self.conversation.id}/'

    def test_get_conversation(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['id'], self.conversation.id)
        self.assertEqual(data['name'], 'test conv')
        self.assertIn('metadata', data)

    def test_get_conversation_with_metadata(self):
        created = ConversationMetadata.objects.create(
            conversation=self.conversation, key='model', value='gpt-4'
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        metadata = response.json()['metadata']
        self.assertEqual(len(metadata), 1)
        self.assertEqual(metadata[0]['key'], created.key)
        self.assertEqual(metadata[0]['value'], created.value)

    def test_get_conversation_not_found(self):
        response = self.client.get('/conversations/9999/')
        self.assertEqual(response.status_code, 404)

    def test_get_conversation_deleted(self):
        self.conversation.delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_patch_conversation_name(self):
        response = self.client.patch(self.url, {'name': 'updated name'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['name'], 'updated name')
        self.conversation.refresh_from_db()
        self.assertEqual(self.conversation.name, 'updated name')

    def test_patch_conversation_not_found(self):
        response = self.client.patch('/conversations/9999/', {'name': 'x'}, format='json')
        self.assertEqual(response.status_code, 404)

    def test_delete_conversation(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 204)
        self.conversation.refresh_from_db()
        self.assertTrue(self.conversation.is_deleted)

    def test_delete_conversation_not_found(self):
        response = self.client.delete('/conversations/9999/')
        self.assertEqual(response.status_code, 404)
