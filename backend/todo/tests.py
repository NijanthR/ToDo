from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Task, Category, SubTask


class AuthAndDataIsolationTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create User 1
        self.user1 = User.objects.create_user(
            username='alice',
            password='Password123!',
            email='alice@example.com'
        )
        # Create User 2
        self.user2 = User.objects.create_user(
            username='bob',
            password='Password123!',
            email='bob@example.com'
        )

        # Categories for User 1 & 2
        self.cat_user1 = Category.objects.create(user=self.user1, name='Alice Work', color='#6366f1')
        self.cat_user2 = Category.objects.create(user=self.user2, name='Bob Work', color='#10b981')

        # Tasks for User 1 & 2
        self.task_user1 = Task.objects.create(
            user=self.user1,
            title="Alice Secret Task",
            description="Confidential to Alice",
            category=self.cat_user1,
            priority=Task.Priority.HIGH
        )
        self.task_user2 = Task.objects.create(
            user=self.user2,
            title="Bob Private Task",
            description="Confidential to Bob",
            category=self.cat_user2,
            priority=Task.Priority.LOW
        )

    def test_unauthenticated_access_redirects_to_login(self):
        """Unauthenticated user should be redirected to login page."""
        response = self.client.get(reverse('todo:task_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_user_registration_creates_account_and_default_categories(self):
        """Registering a new user should log them in and create default categories."""
        response = self.client.post(reverse('todo:register'), {
            'username': 'charlie',
            'email': 'charlie@example.com',
            'password': 'CharliePassword123!',
            'confirm_password': 'CharliePassword123!'
        })
        self.assertEqual(response.status_code, 302)
        new_user = User.objects.filter(username='charlie').first()
        self.assertIsNotNone(new_user)
        # Verify default categories created
        user_categories = list(Category.objects.filter(user=new_user).values_list('name', flat=True))
        self.assertIn('Work', user_categories)
        self.assertIn('Personal', user_categories)
        self.assertIn('Study', user_categories)

    def test_login_and_logout(self):
        """User can log in and log out."""
        login_res = self.client.post(reverse('todo:login'), {
            'username': 'alice',
            'password': 'Password123!'
        })
        self.assertEqual(login_res.status_code, 302)
        self.assertEqual(login_res.url, reverse('todo:task_list'))

        # Check logged in task list view
        view_res = self.client.get(reverse('todo:task_list'))
        self.assertEqual(view_res.status_code, 200)
        self.assertContains(view_res, "Alice Secret Task")
        self.assertNotContains(view_res, "Bob Private Task")
        self.assertContains(view_res, "alice")

        # Logout
        logout_res = self.client.get(reverse('todo:logout'))
        self.assertEqual(logout_res.status_code, 302)
        self.assertIn('/login/', logout_res.url)

    def test_data_isolation_task_list(self):
        """Alice can only see Alice's tasks and categories."""
        self.client.login(username='alice', password='Password123!')
        response = self.client.get(reverse('todo:task_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alice Secret Task")
        self.assertNotContains(response, "Bob Private Task")
        self.assertContains(response, "Alice Work")
        self.assertNotContains(response, "Bob Work")

    def test_data_isolation_cross_user_toggle_prevented(self):
        """Alice cannot toggle Bob's task."""
        self.client.login(username='alice', password='Password123!')
        response = self.client.post(
            reverse('todo:task_toggle', args=[self.task_user2.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 404)
        self.task_user2.refresh_from_db()
        self.assertFalse(self.task_user2.completed)

    def test_data_isolation_cross_user_delete_prevented(self):
        """Alice cannot delete Bob's task."""
        self.client.login(username='alice', password='Password123!')
        response = self.client.post(
            reverse('todo:task_delete', args=[self.task_user2.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Task.objects.filter(id=self.task_user2.id).exists())

    def test_authenticated_task_crud_and_subtasks(self):
        """Alice can create tasks and subtasks under her own account."""
        self.client.login(username='alice', password='Password123!')
        
        # Create Task
        res = self.client.post(reverse('todo:task_create'), {
            'title': 'Alice New Mission',
            'priority': 'MEDIUM',
            'category': self.cat_user1.id,
        })
        self.assertEqual(res.status_code, 302)
        new_task = Task.objects.filter(title='Alice New Mission', user=self.user1).first()
        self.assertIsNotNone(new_task)
        self.assertEqual(new_task.user, self.user1)

        # Create Subtask
        sub_res = self.client.post(
            reverse('todo:subtask_create', args=[new_task.id]),
            data='{"title": "Step A"}',
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(sub_res.status_code, 200)
        subtask = new_task.subtasks.first()
        self.assertIsNotNone(subtask)
        self.assertEqual(subtask.title, 'Step A')

        # Toggle Task
        toggle_res = self.client.post(
            reverse('todo:task_toggle', args=[new_task.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(toggle_res.status_code, 200)
        new_task.refresh_from_db()
        self.assertTrue(new_task.completed)
