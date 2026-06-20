import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from Finance_Wealth.models import FinancialGoal
from .models import Transaction

User = get_user_model()


def make_callback_payload(checkout_request_id, *, success=True, receipt="NLJ7RT61SV", amount=100):
    if success:
        result = {
            "MerchantRequestID": "29115-34620561-1",
            "CheckoutRequestID": checkout_request_id,
            "ResultCode": 0,
            "ResultDesc": "The service request is processed successfully.",
            "CallbackMetadata": {
                "Item": [
                    {"Name": "Amount", "Value": amount},
                    {"Name": "MpesaReceiptNumber", "Value": receipt},
                    {"Name": "TransactionDate", "Value": 20191219102115},
                    {"Name": "PhoneNumber", "Value": 254708374149},
                ]
            },
        }
    else:
        result = {
            "MerchantRequestID": "29115-34620561-1",
            "CheckoutRequestID": checkout_request_id,
            "ResultCode": 1032,
            "ResultDesc": "Request cancelled by user.",
        }
    return json.dumps({"Body": {"stkCallback": result}})


class TransactionModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="pw")

    def test_str_representation(self):
        txn = Transaction.objects.create(
            user=self.user, amount=100, phone_number="254700000000",
            checkout_request_id="abc123",
        )
        self.assertIn("254700000000", str(txn))

    def test_mark_success_sets_fields(self):
        txn = Transaction.objects.create(
            user=self.user, amount=100, phone_number="254700000000",
            checkout_request_id="abc123",
        )
        txn.mark_success(mpesa_receipt_number="REC123", raw_payload={"ok": True})
        txn.refresh_from_db()
        self.assertEqual(txn.status, Transaction.STATUS_SUCCESS)
        self.assertEqual(txn.mpesa_receipt_number, "REC123")

    def test_mark_failed_sets_fields(self):
        txn = Transaction.objects.create(
            user=self.user, amount=100, phone_number="254700000000",
            checkout_request_id="abc123",
        )
        txn.mark_failed(raw_payload={"error": True})
        txn.refresh_from_db()
        self.assertEqual(txn.status, Transaction.STATUS_FAILED)

    def test_checkout_request_id_unique(self):
        Transaction.objects.create(
            user=self.user, amount=100, phone_number="254700000000",
            checkout_request_id="dup-id",
        )
        with self.assertRaises(Exception):
            Transaction.objects.create(
                user=self.user, amount=200, phone_number="254700000001",
                checkout_request_id="dup-id",
            )


class StkCallbackTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="pw")
        self.txn = Transaction.objects.create(
            user=self.user, amount=100, phone_number="254700000000",
            checkout_request_id="checkout-1",
        )
        self.url = reverse("mpesa-callback")

    def test_successful_callback_updates_transaction(self):
        payload = make_callback_payload("checkout-1", success=True)
        response = self.client.post(self.url, data=payload, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.txn.refresh_from_db()
        self.assertEqual(self.txn.status, Transaction.STATUS_SUCCESS)
        self.assertEqual(self.txn.mpesa_receipt_number, "NLJ7RT61SV")
        self.assertIsNotNone(self.txn.raw_callback_payload)

    def test_failed_callback_updates_transaction(self):
        payload = make_callback_payload("checkout-1", success=False)
        response = self.client.post(self.url, data=payload, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.txn.refresh_from_db()
        self.assertEqual(self.txn.status, Transaction.STATUS_FAILED)

    def test_unknown_checkout_request_id_is_safely_ignored(self):
        payload = make_callback_payload("does-not-exist", success=True)
        response = self.client.post(self.url, data=payload, content_type="application/json")
        self.assertEqual(response.status_code, 200)

    def test_duplicate_callback_is_idempotent(self):
        payload = make_callback_payload("checkout-1", success=True, receipt="FIRST")
        self.client.post(self.url, data=payload, content_type="application/json")

        replay_payload = make_callback_payload("checkout-1", success=True, receipt="SECOND")
        response = self.client.post(self.url, data=replay_payload, content_type="application/json")

        self.assertEqual(response.status_code, 200)
        self.txn.refresh_from_db()
        # First write wins; replay must not overwrite an already-resolved transaction.
        self.assertEqual(self.txn.mpesa_receipt_number, "FIRST")

    def test_malformed_body_does_not_500(self):
        response = self.client.post(self.url, data="not-json", content_type="application/json")
        self.assertEqual(response.status_code, 200)


class TransactionListViewTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(username="alice", password="pw")
        self.bob = User.objects.create_user(username="bob", password="pw")
        self.url = reverse("mpesa-transaction-list")

    def test_login_required(self):
        response = self.client.get(self.url)
        self.assertNotEqual(response.status_code, 200)

    def test_empty_state_message(self):
        self.client.force_login(self.alice)
        response = self.client.get(self.url)
        self.assertContains(response, "No transactions yet")

    def test_user_isolation(self):
        Transaction.objects.create(
            user=self.alice, amount=50, phone_number="254700000000",
            checkout_request_id="alice-1",
        )
        Transaction.objects.create(
            user=self.bob, amount=75, phone_number="254700000001",
            checkout_request_id="bob-1",
        )
        self.client.force_login(self.alice)
        response = self.client.get(self.url)
        self.assertEqual(len(response.context["transactions"]), 1)
        self.assertEqual(response.context["transactions"][0].user, self.alice)

    def test_status_filter(self):
        Transaction.objects.create(
            user=self.alice, amount=50, phone_number="254700000000",
            checkout_request_id="alice-success", status=Transaction.STATUS_SUCCESS,
        )
        Transaction.objects.create(
            user=self.alice, amount=50, phone_number="254700000000",
            checkout_request_id="alice-pending", status=Transaction.STATUS_PENDING,
        )
        self.client.force_login(self.alice)
        response = self.client.get(self.url, {"status": "SUCCESS"})
        results = response.context["transactions"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].checkout_request_id, "alice-success")

    def test_financial_goal_filter(self):
        goal = FinancialGoal.objects.create(user=self.alice, name="Trip", target_amount=1000)
        Transaction.objects.create(
            user=self.alice, amount=50, phone_number="254700000000",
            checkout_request_id="linked", financial_goal=goal,
        )
        Transaction.objects.create(
            user=self.alice, amount=50, phone_number="254700000000",
            checkout_request_id="unlinked",
        )
        self.client.force_login(self.alice)
        response = self.client.get(self.url, {"financial_goal": goal.pk})
        results = response.context["transactions"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].checkout_request_id, "linked")


class MpesaRoutingTests(TestCase):
    """Regression coverage for the missing mpesa-hub/deposit-page/
    transaction-status routes that previously 500'd the dashboard and
    every page that linked to M-Pesa (NoReverseMatch on render)."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="routes", email="routes@example.com", password="pw12345!"
        )
        self.client.force_login(self.user)

    def test_hub_page_resolves_and_renders(self):
        response = self.client.get(reverse("mpesa-hub"))
        self.assertEqual(response.status_code, 200)

    def test_deposit_page_resolves_and_renders(self):
        response = self.client.get(reverse("mpesa-deposit-page"))
        self.assertEqual(response.status_code, 200)

    def test_transaction_status_resolves(self):
        txn = Transaction.objects.create(
            user=self.user, amount=10, phone_number="254700000000",
            checkout_request_id="status-check",
        )
        response = self.client.get(reverse("mpesa-transaction-status", args=[txn.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], Transaction.STATUS_PENDING)

    def test_dashboard_renders_with_mpesa_links(self):
        # The actual symptom reported: any logged-in page render crashed
        # with NoReverseMatch('mpesa-hub') because the dashboard template
        # links to it. This is the true end-to-end regression check.
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)


class TransactionExportTests(TestCase):
    def setUp(self):
        self.alice = get_user_model().objects.create_user(
            username="alice-export", email="alice-export@example.com", password="pw12345!"
        )
        self.bob = get_user_model().objects.create_user(
            username="bob-export", email="bob-export@example.com", password="pw12345!"
        )

    def test_export_is_user_scoped(self):
        Transaction.objects.create(
            user=self.alice, amount=20, phone_number="254700000000",
            checkout_request_id="alice-export-1", status=Transaction.STATUS_SUCCESS,
        )
        Transaction.objects.create(
            user=self.bob, amount=999, phone_number="254700000001",
            checkout_request_id="bob-export-1", status=Transaction.STATUS_SUCCESS,
        )
        self.client.force_login(self.alice)
        response = self.client.get(reverse("mpesa-transaction-export"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        body = response.content.decode()
        self.assertIn("254700000000", body)  # alice's row is present
        self.assertNotIn("999", body)

    def test_export_requires_login(self):
        response = self.client.get(reverse("mpesa-transaction-export"))
        self.assertEqual(response.status_code, 302)
