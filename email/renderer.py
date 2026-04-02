"""
Email Renderer — Populeaza template-urile HTML cu date reale via Jinja2
"""

from pathlib import Path
from datetime import datetime

from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=False,
)


def render_confirmare(prenume="", categorii=None, unsubscribe_url="#"):
    """Randeaza emailul de confirmare abonare."""
    template = env.get_template("01_confirmare_abonare.html")
    return template.render(
        prenume=prenume,
        categorii=categorii or [],
        unsubscribe_url=unsubscribe_url,
    )


def render_newsletter(offers, coduri_promo=None, prenume="", data=None):
    """Randeaza newsletter-ul saptamanal cu top oferte."""
    template = env.get_template("02_newsletter_saptamanal.html")
    return template.render(
        offers=offers[:6],
        coduri_promo=coduri_promo or [],
        prenume=prenume,
        data=data or datetime.now().strftime("%d %B %Y"),
    )


def render_flash_alert(offer, ore_ramase=24):
    """Randeaza alerta de reducere flash pentru un produs."""
    template = env.get_template("03_alerta_reducere_flash.html")
    return template.render(
        offer=offer,
        ore_ramase=ore_ramase,
    )


def render_digest(offers, prenume="", data=None, switch_to_weekly_url="#"):
    """Randeaza digest-ul zilnic."""
    template = env.get_template("04_digest_zilnic.html")
    return template.render(
        offers=offers[:3],
        prenume=prenume,
        data=data or datetime.now().strftime("%d.%m.%Y"),
        switch_to_weekly_url=switch_to_weekly_url,
    )


def render_reengagement(offers, prenume="", unsubscribe_url="#"):
    """Randeaza emailul de re-engagement."""
    template = env.get_template("05_reengagement.html")
    return template.render(
        offers=offers[:5],
        prenume=prenume,
        unsubscribe_url=unsubscribe_url,
    )
