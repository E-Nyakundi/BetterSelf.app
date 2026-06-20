from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from datetime import date, time, timedelta

from .models import Profile
from Time_Manager.models import Goals, YearlyGoal, MonthlyGoal, WeeklyGoal, DayGoal, DailyGoal
from WellBeing.models import JournalEntry
from Inventory.models import Item


@override_settings(
    ALLOWED_HOSTS=['testserver', '127.0.0.1', 'localhost'],
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    ACCOUNT_EMAIL_VERIFICATION='optional',
)
class AccountsViewsTests(TestCase):
    def setUp(self):
        self.User = get_user_model()

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response['Location'])

    def test_signup_creates_profile_and_sends_verification_email(self):
        response = self.client.post(reverse('sign-up'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })

        self.assertRedirects(response, reverse('login'))
        user = self.User.objects.get(username='newuser')
        self.assertTrue(Profile.objects.filter(user=user, email='new@example.com').exists())
        self.assertEqual(len(mail.outbox), 1)

    def test_unverified_user_can_still_login(self):
        # Email verification is optional for now: an unverified user should
        # be able to log in without any extra friction.
        user = self.User.objects.create_user(
            username='unverified',
            email='unverified@example.com',
            password='StrongPass123!',
        )
        EmailAddress.objects.create(user=user, email=user.email, verified=False, primary=True)

        response = self.client.post(reverse('login'), {
            'username': 'unverified',
            'password': 'StrongPass123!',
        })

        self.assertRedirects(response, reverse('dashboard'))
        self.assertIn('_auth_user_id', self.client.session)

    def test_verified_user_can_login(self):
        user = self.User.objects.create_user(
            username='verified',
            email='verified@example.com',
            password='StrongPass123!',
        )
        EmailAddress.objects.create(user=user, email=user.email, verified=True, primary=True)

        response = self.client.post(reverse('login'), {
            'username': 'verified',
            'password': 'StrongPass123!',
        })

        self.assertRedirects(response, reverse('dashboard'))

    def test_edit_profile_invalid_upload_rerenders_with_errors(self):
        user = self.User.objects.create_user(
            username='profileuser',
            email='profile@example.com',
            password='StrongPass123!',
        )
        self.client.force_login(user)

        response = self.client.post(reverse('edit_profile'), {
            'email': 'profile@example.com',
            'title': 'New User',
            'profile_img': SimpleUploadedFile('bad.txt', b'not an image', content_type='text/plain'),
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Upload a valid image')

    def test_edit_profile_recreates_missing_profile(self):
        user = self.User.objects.create_user(
            username='missingprofile',
            email='missing@example.com',
            password='StrongPass123!',
        )
        user.profile.delete()
        self.client.force_login(user)

        response = self.client.get(reverse('edit_profile'))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_logout_signs_user_out(self):
        user = self.User.objects.create_user(
            username='logoutuser',
            email='logout@example.com',
            password='StrongPass123!',
        )
        self.client.force_login(user)

        response = self.client.get(reverse('logout'))

        self.assertRedirects(response, reverse('login'))
        self.assertNotIn('_auth_user_id', self.client.session)


@override_settings(ALLOWED_HOSTS=['testserver', '127.0.0.1', 'localhost'])
class DashboardCardsTests(TestCase):
    """Phase 1: every card on the dashboard traces to a real query.

    This is the "renders the dashboard once Phase 1 exists, asserting each
    card's numbers match a known fixture" test the roadmap calls for in
    Phase 8 — added now, while the fixture is fresh in mind, rather than
    deferred and re-derived later.
    """

    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username='dashuser', email='dash@example.com', password='StrongPass123!'
        )
        self.today = date.today()

        goal = Goals.objects.create(user=self.user, name='Learn Mandarin')
        yearly = YearlyGoal.objects.create(goals=goal, goal='Y1', year=self.today)
        monthly = MonthlyGoal.objects.create(yearly_goal=yearly, goal='M1', month=self.today)
        weekly = WeeklyGoal.objects.create(
            monthly_goal=monthly, goal='W1', start_date=self.today, end_date=self.today
        )
        self.day_goal = DayGoal.objects.create(weekly_goal=weekly, goal='D1', date=self.today)

        # 3 completed on prior days (a real streak), 1 pending today.
        for i in range(1, 4):
            DailyGoal.objects.create(
                day_goal=self.day_goal, goal=f'Done {i}', date=self.today - timedelta(days=i),
                completed=True, start_time=time(9, 0), end_time=time(10, 0),
            )
        self.pending_goal = DailyGoal.objects.create(
            day_goal=self.day_goal, goal='Pending today', date=self.today,
            completed=False, start_time=time(14, 0), end_time=time(15, 0),
        )

        JournalEntry.objects.create(user=self.user, days_date=self.today, mood=4, energy=2)
        Item.objects.create(user=self.user, name='Hiking boots')

        self.client.force_login(self.user)

    def test_dashboard_renders_real_data_not_placeholders(self):
        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        # Goal progress: 3/4 DailyGoal leaves completed = 75%.
        self.assertContains(response, 'Learn Mandarin')
        self.assertContains(response, '75%')
        # Today's Focus shows the still-pending task.
        self.assertContains(response, 'Pending today')
        # Recent Activity includes the inventory addition.
        self.assertContains(response, 'Hiking boots')
        # None of the old hardcoded placeholder values should ever appear.
        self.assertNotIn('Gym Session', content)
        self.assertNotIn('KES 12,400', content)
        self.assertNotIn('Become EEE Engineer', content)

    def test_dashboard_with_no_data_shows_honest_empty_states(self):
        empty_user = self.User.objects.create_user(
            username='emptyuser', email='empty@example.com', password='StrongPass123!'
        )
        self.client.force_login(empty_user)

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No goals yet')
        self.assertContains(response, 'Streak tracking starts now')

    def test_toggle_daily_goal_flips_completion_and_updates_progress(self):
        goal = Goals.objects.get(name='Learn Mandarin')
        self.assertEqual(goal.progress_percentage(), 75)

        response = self.client.post(
            reverse('toggle_daily_goal', args=[self.pending_goal.id])
        )

        self.assertRedirects(response, reverse('dashboard'))
        self.pending_goal.refresh_from_db()
        self.assertTrue(self.pending_goal.completed)
        self.assertEqual(goal.progress_percentage(), 100)

    def test_toggle_daily_goal_is_scoped_to_the_owning_user(self):
        other_user = self.User.objects.create_user(
            username='otheruser', email='other@example.com', password='StrongPass123!'
        )
        self.client.force_login(other_user)

        response = self.client.post(
            reverse('toggle_daily_goal', args=[self.pending_goal.id])
        )

        self.assertEqual(response.status_code, 404)
        self.pending_goal.refresh_from_db()
        self.assertFalse(self.pending_goal.completed)


class SignalsTests(TestCase):
    """Accounts/signals.py used to be an accidental duplicate of settings.py
    (no signal handlers actually connected). These cover the real handlers
    that replaced it."""

    def test_post_migrate_syncs_site_domain(self):
        from django.contrib.sites.models import Site
        site = Site.objects.get(pk=1)
        self.assertNotEqual(site.domain, "example.com")

    def test_profile_auto_created_for_new_user(self):
        user = get_user_model().objects.create_user(
            username='autoprofile', email='autoprofile@example.com', password='StrongPass123!'
        )
        self.assertTrue(Profile.objects.filter(user=user).exists())
