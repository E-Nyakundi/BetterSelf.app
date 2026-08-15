from django.db import models
from django.conf import settings


class FinancialGoal(models.Model):
    """A savings/spending target the user is tracking.

    Phase 4.0 scope only: this is goal *targets*, no transaction data yet.
    `current_amount` is a manually-updated running figure for now — it
    becomes a real, auto-updated rollup once Phase 4.1+ lands a
    `Transaction` model and Phase 4.4 wires up reconciliation. Don't
    retrofit this model to hold transactions directly; that's explicitly
    a separate model per the roadmap.
    """

    CATEGORY_CHOICES = [
        ('savings', 'Savings'),
        ('investment', 'Investment'),
        ('debt_payoff', 'Debt Payoff'),
        ('emergency_fund', 'Emergency Fund'),
        ('purchase', 'Major Purchase'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='financial_goals',
    )
    name = models.CharField(max_length=100)
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        null=True,
        blank=True,
    )
    target_amount = models.DecimalField(max_digits=12, decimal_places=2)
    current_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    target_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def progress_percentage(self):
        """% of target_amount saved so far, capped at 100.

        Returns None (not 0) when target_amount is 0 -- same "honest empty
        state, not a misleading number" rule Goals.progress_percentage()
        already follows on the dashboard.
        """
        if not self.target_amount:
            return None
        pct = float(self.current_amount) / float(self.target_amount) * 100
        return round(min(pct, 100))

    def remaining_amount(self):
        remaining = self.target_amount - self.current_amount
        return remaining if remaining > 0 else 0
