from django.test import TestCase

from conversation.memory_tools import delete_memory, list_memory, save_memory
from conversation.models import Conversation, ConversationMetadata


class SaveMemoryTest(TestCase):
    def test_save_creates_metadata(self):
        conv = Conversation.objects.create(name="test")

        result = save_memory(conv.id, "user_name", "John")

        self.assertEqual(result, "saved: user_name")
        memory = ConversationMetadata.objects.get(conversation=conv, key="user_name")
        self.assertEqual(memory.value, "John")

    def test_save_updates_existing_key(self):
        conv = Conversation.objects.create(name="test")
        save_memory(conv.id, "user_name", "John")

        save_memory(conv.id, "user_name", "Jane")

        memories = ConversationMetadata.objects.filter(
            conversation=conv, key="user_name"
        )
        self.assertEqual(memories.count(), 1)
        self.assertEqual(memories.first().value, "Jane")

    def test_save_revives_soft_deleted_key(self):
        conv = Conversation.objects.create(name="test")
        save_memory(conv.id, "user_name", "John")
        delete_memory(conv.id, "user_name")

        save_memory(conv.id, "user_name", "Jane")

        self.assertEqual(list_memory(conv.id), [{"key": "user_name", "value": "Jane"}])

    def test_save_returns_error_for_unknown_conversation(self):
        result = save_memory(999, "user_name", "John")

        self.assertEqual(result, "error: conversation 999 not found")
        self.assertEqual(ConversationMetadata.objects.count(), 0)


class ListMemoryTest(TestCase):
    def test_list_returns_memories_in_creation_order(self):
        conv = Conversation.objects.create(name="test")
        save_memory(conv.id, "user_name", "John")
        save_memory(conv.id, "role", "Lawyer")

        self.assertEqual(
            list_memory(conv.id),
            [
                {"key": "user_name", "value": "John"},
                {"key": "role", "value": "Lawyer"},
            ],
        )

    def test_list_excludes_deleted_and_other_conversations(self):
        conv = Conversation.objects.create(name="test")
        other = Conversation.objects.create(name="other")
        save_memory(conv.id, "user_name", "John")
        save_memory(conv.id, "role", "Lawyer")
        save_memory(other.id, "user_name", "Jane")
        delete_memory(conv.id, "role")

        self.assertEqual(list_memory(conv.id), [{"key": "user_name", "value": "John"}])

    def test_list_returns_empty_for_no_memories(self):
        conv = Conversation.objects.create(name="test")

        self.assertEqual(list_memory(conv.id), [])


class DeleteMemoryTest(TestCase):
    def test_delete_soft_deletes_memory(self):
        conv = Conversation.objects.create(name="test")
        save_memory(conv.id, "user_name", "John")

        result = delete_memory(conv.id, "user_name")

        self.assertEqual(result, "deleted: user_name")
        memory = ConversationMetadata.objects.get(conversation=conv, key="user_name")
        self.assertTrue(memory.is_deleted)
        self.assertIsNotNone(memory.deleted_at)

    def test_delete_returns_error_for_unknown_key(self):
        conv = Conversation.objects.create(name="test")

        result = delete_memory(conv.id, "nope")

        self.assertEqual(result, "error: memory 'nope' not found")
