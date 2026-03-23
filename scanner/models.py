from django.db import models


class ScannedLink(models.Model):
    """
    Stores information about each scanned URL.

    Once a URL is scanned for the first time, later users can be warned
    immediately using the stored status instead of re-analysing every time.
    """

    url = models.URLField(unique=True)
    is_safe = models.BooleanField(default=True)
    risk_score = models.FloatField(default=0.0)

    company_name = models.CharField(max_length=255, blank=True)
    company_email = models.EmailField(blank=True)

    times_seen = models.PositiveIntegerField(default=0)
    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)

    reported_to_company = models.BooleanField(default=False)
    last_reported_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.url} ({'SAFE' if self.is_safe else 'UNSAFE'})"
