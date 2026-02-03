"""
Validation helpers pour les données d'entrée
"""
import re

from app.common.errors import bad_request


def validate_phone(phone: str) -> str:
    """Valide un numéro de téléphone malgache"""
    if not phone:
        raise bad_request("telephone_obligatoire")
    # Format: 034xxxxxxxx (10 chiffres, commence par 03)
    phone_clean = re.sub(r"\D", "", phone)
    if not re.match(r"^03\d{8}$", phone_clean):
        raise bad_request("telephone_invalide", {"format_attendu": "03XXXXXXXX"})
    return phone_clean


def validate_email(email: str) -> str:
    """Valide un email"""
    if not email:
        raise bad_request("email_obligatoire")
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_pattern, email):
        raise bad_request("email_invalide")
    return email.lower().strip()


def validate_quantity(quantity: float, min_value: float = 0.0) -> float:
    """Valide une quantité"""
    if quantity is None:
        raise bad_request("quantite_obligatoire")
    if quantity < min_value:
        raise bad_request("quantite_invalide", {"min": min_value})
    return quantity


def validate_coordinates(lat: float, lon: float) -> tuple[float, float]:
    """Valide des coordonnées GPS"""
    if lat is None or lon is None:
        raise bad_request("coordonnees_obligatoires")
    if not (-90 <= lat <= 90):
        raise bad_request("latitude_invalide", {"range": "[-90, 90]"})
    if not (-180 <= lon <= 180):
        raise bad_request("longitude_invalide", {"range": "[-180, 180]"})
    return lat, lon


def validate_status(status: str, allowed: set[str]) -> str:
    """Valide un statut"""
    if status not in allowed:
        raise bad_request("statut_invalide", {"statuts_autorises": sorted(allowed)})
    return status
