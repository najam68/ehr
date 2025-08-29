import json
from django.test import TestCase
from datetime import date

from apps.claims.models import Claim, Denial, DenialStatusHistory
from apps.patients.models import Patient

API_KEY = "secret123"


class DenialStatusTests(TestCase):
    def setUp(self):
        # Minimal Patient with required fields
        self.patient = Patient.objects.create(
            first_name="Test",
            last_name="Patient",
            date_of_birth=date(2000, 1, 1),   # <-- added to satisfy NOT NULL
        )

        self.claim = Claim.objects.create(
            patient_id=self.patient.id,
            # If the next run errors about another NOT NULL field (e.g. payer_name),
            # we’ll add that here with a dummy value.
        )

        self.denial = Denial.objects.create(
            claim=self.claim,
            status="NEW",
            reason="Init",
        )

        self.url = f"/api/claims/denials/{self.denial.id}/status/"
        self.history_url = f"/api/claims/denials/{self.denial.id}/history/"
        self.detail_url = f"/api/claims/denials/{self.denial.id}/detail/"

    def _post(self, body, api_key=API_KEY):
        return self.client.post(
            self.url,
            data=json.dumps(body),
            content_type="application/json",
            **({"HTTP_X_API_KEY": api_key} if api_key else {}),
        )

    def test_update_status_and_history_created(self):
        r = self._post({"status": "WORKING", "note": "called payer"})
        self.assertEqual(r.status_code, 200, r.content)
        self.denial.refresh_from_db()
        self.assertEqual(self.denial.status, "WORKING")
        hist = DenialStatusHistory.objects.filter(denial=self.denial).first()
        self.assertIsNotNone(hist)
        self.assertEqual(hist.from_status, "NEW")
        self.assertEqual(hist.to_status, "WORKING")
        self.assertEqual(hist.note, "called payer")

    def test_missing_status_returns_400(self):
        r = self._post({"note": "missing"}, api_key=API_KEY)
        self.assertEqual(r.status_code, 400)

    def test_bad_api_key_returns_401(self):
        r = self._post({"status": "WORKING"}, api_key="nope")
        self.assertEqual(r.status_code, 401)

    def test_history_endpoint_lists_changes(self):
        self._post({"status": "WORKING", "note": "step1"})
        self._post({"status": "IN_PROGRESS", "note": "step2"})
        r = self.client.get(self.history_url, **{"HTTP_X_API_KEY": API_KEY})
        self.assertEqual(r.status_code, 200)
        payload = r.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["denial_id"], self.denial.id)
        history = payload["history"]
        self.assertGreaterEqual(len(history), 2)
        # newest first
        self.assertEqual(history[0]["to_status"], "IN_PROGRESS")
        self.assertEqual(history[0]["note"], "step2")
        self.assertEqual(history[1]["to_status"], "WORKING")
        self.assertEqual(history[1]["note"], "step1")

    def test_detail_endpoint_returns_latest_history(self):
        # Two changes so there is a clear "latest"
        self._post({"status": "WORKING", "note": "step1"})
        self._post({"status": "IN_PROGRESS", "note": "step2"})
        r = self.client.get(self.detail_url, **{"HTTP_X_API_KEY": API_KEY})
        self.assertEqual(r.status_code, 200, r.content)
        data = r.json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["denial"]["id"], self.denial.id)
        self.assertEqual(data["denial"]["status"], "IN_PROGRESS")
        latest = data["latest_history"]
        self.assertIsNotNone(latest)
        self.assertEqual(latest["to_status"], "IN_PROGRESS")
        self.assertEqual(latest["note"], "step2")

    def test_claim_denials_list_returns_items_with_latest_history(self):
        # make two history entries on the existing denial
        self._post({"status": "WORKING", "note": "step1"})
        self._post({"status": "IN_PROGRESS", "note": "step2"})

        # create a second denial on the same claim
        d2 = Denial.objects.create(
            claim=self.claim,
            status="NEW",
            reason="Second denial",
        )
        # add a history entry to the second denial via the endpoint
        url2 = f"/api/claims/denials/{d2.id}/status/"
        self.client.post(
            url2,
            data=json.dumps({"status": "WORKING", "note": "d2-note"}),
            content_type="application/json",
            **{"HTTP_X_API_KEY": API_KEY},
        )

        # call the list endpoint for this claim
        list_url = f"/api/claims/{self.claim.id}/denials/"
        r = self.client.get(list_url, **{"HTTP_X_API_KEY": API_KEY})
        self.assertEqual(r.status_code, 200, r.content)

        payload = r.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["claim_id"], self.claim.id)
        self.assertGreaterEqual(payload["count"], 2)
        self.assertIn("results", payload)
        self.assertGreaterEqual(len(payload["results"]), 2)

        # newest first (by id desc). verify shape & latest_history presence
        first_item = payload["results"][0]
        self.assertIn("id", first_item)
        self.assertIn("status", first_item)
        self.assertIn("latest_history", first_item)
        # latest_history may be None if no history yet, but here we added one above
        self.assertIsNotNone(first_item["latest_history"])
        self.assertIn("to_status", first_item["latest_history"])
        self.assertIn("created_at", first_item["latest_history"])