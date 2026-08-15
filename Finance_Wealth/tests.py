from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import FinancialGoal


class FinancialGoalModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='financeuser', email='finance@example.com', password='StrongPass123!'
        )

    def test_progress_percentage_real_value(self):
        goal = FinancialGoal.objects.create(
            user=self.user, name='Emergency Fund',
            target_amount=Decimal('10000'), current_amount=Decimal('2500'),
        )
        self.assertEqual(goal.progress_percentage(), 25)

    def test_progress_percentage_capped_at_100(self):
        goal = FinancialGoal.objects.create(
            user=self.user, name='Overshot Goal',
            target_amount=Decimal('1000'), current_amount=Decimal('1500'),
        )
        self.assertEqual(goal.progress_percentage(), 100)

    def test_progress_percentage_none_when_no_target(self):
        goal = FinancialGoal.objects.create(
            user=self.user, name='Zero Target',
            target_amount=Decimal('0'), current_amount=Decimal('0'),
        )
        self.assertIsNone(goal.progress_percentage())

    def test_remaining_amount(self):
        goal = FinancialGoal.objects.create(
            user=self.user, name='Laptop Fund',
            target_amount=Decimal('1000'), current_amount=Decimal('400'),
        )
        self.assertEqual(goal.remaining_amount(), Decimal('600'))


class FinancialGoalViewsTests(TestCase):
    """Phase 4.0: CRUD pages exist, are scoped to the owning user, and the
    finance dashboard renders real data (no hardcoded placeholders).
    """

    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username='owner', email='owner@example.com', password='StrongPass123!'
        )
        self.other_user = self.User.objects.create_user(
            username='other', email='other@example.com', password='StrongPass123!'
        )
        self.goal = FinancialGoal.objects.create(
            user=self.user, name='Trip to Mombasa',
            target_amount=Decimal('5000'), current_amount=Decimal('1000'),
        )
        self.client.force_login(self.user)

    def test_finance_dashboard_shows_real_totals(self):
        response = self.client.get(reverse('finance-dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Trip to Mombasa')
        self.assertContains(response, '5000')
        self.assertContains(response, '1000')

    def test_finance_dashboard_empty_state_for_new_user(self):
        empty_user = self.User.objects.create_user(
            username='emptyuser', email='empty@example.com', password='StrongPass123!'
        )
        self.client.force_login(empty_user)
        response = self.client.get(reverse('finance-dashboard'))
        self.assertContains(response, 'No financial goals yet')

    def test_goal_list_scoped_to_owner(self):
        response = self.client.get(reverse('financial-goal-list'))
        self.assertContains(response, 'Trip to Mombasa')

        self.client.force_login(self.other_user)
        response = self.client.get(reverse('financial-goal-list'))
        self.assertNotContains(response, 'Trip to Mombasa')

    def test_goal_detail_404_for_non_owner(self):
        self.client.force_login(self.other_user)
        response = self.client.get(reverse('financial-goal-detail', args=[self.goal.id]))
        self.assertEqual(response.status_code, 404)

    def test_create_goal(self):
        response = self.client.post(reverse('financial-goal-create'), {
            'name': 'New Laptop',
            'category': 'purchase',
            'target_amount': '1500',
            'current_amount': '0',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(FinancialGoal.objects.filter(user=self.user, name='New Laptop').exists())

    def test_create_goal_rejects_zero_target(self):
        response = self.client.post(reverse('financial-goal-create'), {
            'name': 'Bad Goal',
            'target_amount': '0',
            'current_amount': '0',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(FinancialGoal.objects.filter(name='Bad Goal').exists())

    def test_delete_goal_scoped_to_owner(self):
        self.client.force_login(self.other_user)
        response = self.client.post(reverse('financial-goal-delete', args=[self.goal.id]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(FinancialGoal.objects.filter(id=self.goal.id).exists())


class DashboardFinanceCardTests(TestCase):
    """Phase 4.0: the Accounts dashboard's Finance card uses real
    FinancialGoal data instead of the old "coming soon" placeholder.
    """

    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username='dashfinanceuser', email='dashfinance@example.com', password='StrongPass123!'
        )
        self.client.force_login(self.user)

    def test_dashboard_shows_finance_goal_when_present(self):
        FinancialGoal.objects.create(
            user=self.user, name='Rainy Day Fund',
            target_amount=Decimal('20000'), current_amount=Decimal('5000'),
        )
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, 'Rainy Day Fund')
        self.assertNotContains(response, 'Coming soon')

    def test_dashboard_shows_honest_empty_state_when_no_goals(self):
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, 'No financial goals yet')
