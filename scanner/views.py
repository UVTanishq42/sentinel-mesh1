from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import socket
from typing import Optional
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.core.mail import send_mail
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_GET, require_POST

from .models import ScannedLink


@dataclass
class LinkAnalysisResult:
    url: str
    is_safe: bool
    risk_score: float


SUSPICIOUS_KEYWORDS = [
    "urgent",
    "verify",
    "login",
    "reset",
    "update",
    "limited",
    "offer",
    "bonus",
    "prize",
    "winner",
    "job-offer",
    "internship-offer",
]

SUSPICIOUS_SHORTENERS = [
    "bit.ly",
    "tinyurl.com",
    "goo.gl",
    "t.co",
    "ow.ly",
]

SUSPICIOUS_TLDS = [
    ".xyz",
    ".top",
    ".click",
    ".info",
    ".work",
    ".online",
]


def _basic_url_analysis(url: str) -> LinkAnalysisResult:
    """
    Very simple heuristic analysis for demonstration purposes.

    In a real project you could plug in ML / NLP models here.
    """

    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path.lower()
    full = url.lower()

    score = 0.0

    if host.replace(".", "").isdigit():
        score += 0.3

    for shortener in SUSPICIOUS_SHORTENERS:
        if shortener in host:
            score += 0.3
            break

    if "-" in host and len(host) > 20:
        score += 0.2

    for tld in SUSPICIOUS_TLDS:
        if host.endswith(tld):
            score += 0.2
            break

    if len(parsed.query) > 120:
        score += 0.2

    for keyword in SUSPICIOUS_KEYWORDS:
        if keyword in full:
            score += 0.2
            break

    try:
        # Check if the domain actually resolves to a real IP address
        socket.gethostbyname(host)
    except socket.gaierror:
        # The domain does not exist or cannot be resolved.
        # This is highly suspicious (could be a typo or a dead scam link).
        # We cap the score at 1.0 so it gets flagged as "Danger" / "Unsafe".
        score = 1.0

    if score > 1.0:
        score = 1.0

    # Risk bands:
    # 0.00–0.10  -> safe
    # 0.11–0.50  -> low / medium risk (no email)
    # 0.51–1.00  -> high risk (suspicious, triggers email)
    is_safe = score <= 0.10
    return LinkAnalysisResult(url=url, is_safe=is_safe, risk_score=score)


def _send_impersonation_email(link: ScannedLink) -> Optional[str]:
    """
    Send warning email to the company. Returns None on success, or an error message.
    """
    if not link.company_email:
        return None

    subject = "Possible fake internship link detected"
    body = (
        f"Hello {link.company_name or 'team'},\n\n"
        "Our internship scam detector has identified a link that looks risky and "
        "appears to be using your company name without authorization:\n\n"
        f"{link.url}\n\n"
        "This may indicate that your company name is being misused in a fake or "
        "phishing internship/job offer.\n\n"
        "Please verify whether this link is legitimate. If it is not, consider "
        "taking action (for example, reporting the phishing page or informing "
        "your users).\n\n"
        "Sentinel Mesh – internship scam detector."
    )

    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=None,
            recipient_list=[link.company_email],
            fail_silently=False,
        )
        link.reported_to_company = True
        link.last_reported_at = datetime.utcnow()
        link.save(update_fields=["reported_to_company", "last_reported_at"])
        return None
    except Exception as e:
        return str(e)


@login_required
def home(request: HttpRequest) -> HttpResponse:
    recent_links = ScannedLink.objects.order_by("-last_seen_at")[:5]
    context = {"recent_links": recent_links}
    return render(request, "scanner/home.html", context)


@login_required
@require_POST
def scan_link(request: HttpRequest) -> HttpResponse:
    url = request.POST.get("url", "").strip()
    company_name = request.POST.get("company_name", "").strip()
    company_email = request.POST.get("company_email", "").strip()

    if not url:
        return render(
            request,
            "scanner/home.html",
            {
                "error": "Please paste a link to scan.",
                "recent_links": ScannedLink.objects.order_by("-last_seen_at")[:5],
            },
        )

    link, _created = ScannedLink.objects.get_or_create(url=url)

    # Always update company info from the latest form submission if provided.
    if company_name:
        link.company_name = company_name
    if company_email:
        link.company_email = company_email

    # (Re)analyse the URL on every scan so the latest risk score is used.
    analysis = _basic_url_analysis(url)
    link.is_safe = analysis.is_safe
    link.risk_score = analysis.risk_score

    # Classify into three bands for the UI and email rules.
    if analysis.risk_score <= 0.10:
        risk_band = "safe"
    elif analysis.risk_score <= 0.50:
        risk_band = "medium"
    else:
        risk_band = "high"

    link.times_seen += 1
    link.save()

    # If the link is high risk and we have a company email, send a notification.
    email_sent = False
    email_error = None
    if risk_band == "high" and link.company_email:
        email_error = _send_impersonation_email(link)
        email_sent = email_error is None

    recent_links = ScannedLink.objects.order_by("-last_seen_at")[:5]
    email_using_console = getattr(
        settings, "EMAIL_BACKEND", ""
    ) == "django.core.mail.backends.console.EmailBackend"
    context = {
        "url": url,
        "link": link,
        "recent_links": recent_links,
        "risk_band": risk_band,
        "email_sent": email_sent,
        "email_error": email_error,
        "email_using_console": email_using_console,
        "company_email": link.company_email if not link.is_safe else None,
    }
    return render(request, "scanner/home.html", context)


@require_GET
def api_check_link(request: HttpRequest) -> JsonResponse:
    url = request.GET.get("url", "").strip()
    if not url:
        return JsonResponse(
            {"ok": False, "error": "Missing 'url' query parameter."},
            status=400,
        )

    link, created = ScannedLink.objects.get_or_create(url=url)
    if created or link.times_seen == 0:
        analysis = _basic_url_analysis(url)
        link.is_safe = analysis.is_safe
        link.risk_score = analysis.risk_score

    link.times_seen += 1
    link.save()

    return JsonResponse(
        {
            "ok": True,
            "url": link.url,
            "is_safe": link.is_safe,
            "risk_score": link.risk_score,
            "times_seen": link.times_seen,
        }
    )

def signup(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {"form": form})

