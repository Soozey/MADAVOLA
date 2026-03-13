from decimal import Decimal, ROUND_HALF_UP
import json
from typing import Any


DTSPM_RATE = Decimal("0.05")
REDEVANCE_RATE = Decimal("0.03")
RISTOURNE_RATE = Decimal("0.02")

FNP_SHARE_OF_RISTOURNE = Decimal("0.10")
CTD_SHARE_OF_RISTOURNE = Decimal("0.90")
COMMUNE_SHARE_OF_CTD = Decimal("0.60")
REGION_SHARE_OF_CTD = Decimal("0.30")
PROVINCE_SHARE_OF_CTD = Decimal("0.10")

TITRAGE_BUDGET_SHARE = Decimal("0.35")
TITRAGE_BGGLM_SHARE = Decimal("0.35")
TITRAGE_COM_SHARE = Decimal("0.30")

COLLECTOR_CARD_COMMUNE_SHARE = Decimal("0.50")
COLLECTOR_CARD_REGION_SHARE = Decimal("0.30")
COLLECTOR_CARD_COM_SHARE = Decimal("0.20")

DEFAULT_DTSPM_ABATEMENT = Decimal("0.30")

EVENT_EXPORT_DTSPM = "EXPORT_DTSPM"
EVENT_LOCAL_SALE_DTSPM = "LOCAL_SALE_DTSPM"
EVENT_TITRAGE_POINCONNAGE = "TITRAGE_POINCONNAGE"
EVENT_DROIT_CARTE_COLLECTEUR = "DROIT_CARTE_COLLECTEUR"

DEFAULT_LEGAL_BASIS: dict[str, list[str]] = {
    EVENT_EXPORT_DTSPM: [
        "Code minier (Loi n 2023-007) Art. 283: DTSPM total 5% = ristourne 2% + redevance 3%",
        "Code minier (Loi n 2023-007) Art. 284: assiette export = valeur FOB",
        "Code minier (Loi n 2023-007) Art. 290: ristourne 10% FNP + 90% CTD (60% commune, 30% region, 10% province)",
        "Code minier (Loi n 2023-007) Art. 291: redevance miniere au Budget General",
    ],
    EVENT_LOCAL_SALE_DTSPM: [
        "Code minier (Loi n 2023-007) Art. 289: assiette ventes locales = valeurs marchandes locales periodiques",
        "Code minier (Loi n 2023-007) Art. 283: DTSPM total 5% = ristourne 2% + redevance 3%",
        "Decret n 2024-1345 Art. 72: responsabilite DTSPM locale pour comptoir/bijoutier en cas d amont non acquitte",
    ],
    EVENT_TITRAGE_POINCONNAGE: [
        "Decret n 2024-1345 Art. 73: repartition titrage/poinconnage = Budget General 35%, BGGLM 35%, COM 30%",
    ],
    EVENT_DROIT_CARTE_COLLECTEUR: [
        "Decret n 2024-1345 Art. 46: repartition droit carte collecteur = Commune 50%, Region 30%, COM 20%",
    ],
}


def _round_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _ratio(value: Decimal, base: Decimal) -> Decimal:
    if base == 0:
        return Decimal("0")
    return (value / base).quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP)


def _as_decimal(value: Any, fallback: Decimal) -> Decimal:
    try:
        if value is None:
            return fallback
        return Decimal(str(value))
    except Exception:
        return fallback


def normalize_event_type(raw_event_type: str) -> str:
    token = (raw_event_type or "").strip().lower()
    aliases = {
        "export": EVENT_EXPORT_DTSPM,
        "export_declaration": EVENT_EXPORT_DTSPM,
        "export_dtspm": EVENT_EXPORT_DTSPM,
        "local_sale": EVENT_LOCAL_SALE_DTSPM,
        "local_sale_dtspm": EVENT_LOCAL_SALE_DTSPM,
        "vente_locale": EVENT_LOCAL_SALE_DTSPM,
        "titrage": EVENT_TITRAGE_POINCONNAGE,
        "poinconnage": EVENT_TITRAGE_POINCONNAGE,
        "titrage_poinconnage": EVENT_TITRAGE_POINCONNAGE,
        "collector_card_right": EVENT_DROIT_CARTE_COLLECTEUR,
        "droit_carte_collecteur": EVENT_DROIT_CARTE_COLLECTEUR,
    }
    if token in aliases:
        return aliases[token]
    if not token:
        return EVENT_EXPORT_DTSPM
    return token.upper()


def default_assiette_mode_for_event(event_type: str) -> str:
    if event_type == EVENT_EXPORT_DTSPM:
        return "fob_export"
    if event_type == EVENT_LOCAL_SALE_DTSPM:
        return "local_market_value"
    if event_type in {EVENT_TITRAGE_POINCONNAGE, EVENT_DROIT_CARTE_COLLECTEUR}:
        return "fixed_amount"
    return "manual"


def default_legal_key_for_event(event_type: str) -> str:
    if event_type in {EVENT_EXPORT_DTSPM, EVENT_LOCAL_SALE_DTSPM}:
        return "dtspm"
    if event_type == EVENT_TITRAGE_POINCONNAGE:
        return "titrage_poinconnage"
    if event_type == EVENT_DROIT_CARTE_COLLECTEUR:
        return "collector_card_right"
    return "dtspm"


def default_legal_basis_for_event(event_type: str) -> list[str]:
    return list(DEFAULT_LEGAL_BASIS.get(event_type, DEFAULT_LEGAL_BASIS[EVENT_EXPORT_DTSPM]))


def merge_rule_payload(raw_payload_json: str | None) -> dict[str, Any]:
    merged: dict[str, Any] = {
        "dtspm": {
            "total_rate": str(DTSPM_RATE),
            "redevance_rate": str(REDEVANCE_RATE),
            "ristourne_rate": str(RISTOURNE_RATE),
            "abatement_rate": str(DEFAULT_DTSPM_ABATEMENT),
        },
        "ristourne_split": {
            "fnp": str(FNP_SHARE_OF_RISTOURNE),
            "ctd": str(CTD_SHARE_OF_RISTOURNE),
            "commune": str(COMMUNE_SHARE_OF_CTD),
            "region": str(REGION_SHARE_OF_CTD),
            "province": str(PROVINCE_SHARE_OF_CTD),
        },
        "titrage_poinconnage_split": {
            "budget_general": str(TITRAGE_BUDGET_SHARE),
            "bgglm": str(TITRAGE_BGGLM_SHARE),
            "com": str(TITRAGE_COM_SHARE),
        },
        "collector_card_right_split": {
            "commune": str(COLLECTOR_CARD_COMMUNE_SHARE),
            "region": str(COLLECTOR_CARD_REGION_SHARE),
            "com": str(COLLECTOR_CARD_COM_SHARE),
        },
    }
    if not raw_payload_json:
        return merged
    try:
        payload = json.loads(raw_payload_json)
    except Exception:
        return merged
    if not isinstance(payload, dict):
        return merged
    for key, value in payload.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = {**merged[key], **value}
        else:
            merged[key] = value
    return merged


def _apply_abatement_to_rate(rate: Decimal, abatement_rate: Decimal) -> Decimal:
    factor = Decimal("1") - abatement_rate
    if factor < Decimal("0"):
        factor = Decimal("0")
    return (rate * factor).quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP)


def should_apply_dtspm_abatement(
    *,
    filiere: str,
    event_type: str,
    is_transformed: bool,
    transformation_origin: str | None,
    abatement_rate: Decimal,
) -> tuple[Decimal, str | None]:
    if event_type not in {EVENT_EXPORT_DTSPM, EVENT_LOCAL_SALE_DTSPM}:
        return Decimal("0"), None
    if not is_transformed:
        return Decimal("0"), None
    if filiere.upper() == "OR":
        origin = (transformation_origin or "").strip().lower()
        if origin != "national_refinery":
            return Decimal("0"), None
        return abatement_rate, "Decret n 2024-1345 Art. 74 (or raffinerie nationale)"
    return abatement_rate, "Code minier Art. 288 (abattement transformation)"


def _adjust_rounding_delta(rows: list[dict[str, Any]], expected_total: Decimal) -> None:
    current = sum((Decimal(str(r["amount"])) for r in rows), Decimal("0"))
    delta = _round_money(expected_total - current)
    if delta == 0:
        return
    if not rows:
        return
    rows[0]["amount"] = _round_money(Decimal(str(rows[0]["amount"])) + delta)


def _compute_split_component(
    *,
    tax_type: str,
    base: Decimal,
    currency: str,
    shares: dict[str, Decimal],
) -> dict[str, Any]:
    beneficiaries: list[dict[str, Any]] = []
    total_share = sum(shares.values(), Decimal("0"))
    total_amount = _round_money(base * total_share)
    for level, share in shares.items():
        amount = _round_money(base * share)
        beneficiaries.append(
            {
                "beneficiary_level": level,
                "allocation_share": share,
                "rate_of_base": _ratio(amount, base),
                "amount": amount,
            }
        )
    _adjust_rounding_delta(beneficiaries, total_amount)
    for item in beneficiaries:
        item["rate_of_base"] = _ratio(Decimal(str(item["amount"])), base)
    return {
        "tax_type": tax_type,
        "rate": _ratio(total_amount, base),
        "amount": total_amount,
        "currency": currency,
        "beneficiaries": beneficiaries,
    }


def compute_dtspm_breakdown(
    base_amount: Decimal,
    currency: str,
    *,
    redevance_rate: Decimal = REDEVANCE_RATE,
    ristourne_rate: Decimal = RISTOURNE_RATE,
    fnp_share: Decimal = FNP_SHARE_OF_RISTOURNE,
    ctd_share: Decimal = CTD_SHARE_OF_RISTOURNE,
    commune_share: Decimal = COMMUNE_SHARE_OF_CTD,
    region_share: Decimal = REGION_SHARE_OF_CTD,
    province_share: Decimal = PROVINCE_SHARE_OF_CTD,
    abatement_rate: Decimal = Decimal("0"),
    abatement_reason: str | None = None,
    event_type: str = EVENT_EXPORT_DTSPM,
    assiette_mode: str = "manual",
    assiette_reference: str | None = None,
    legal_basis: list[str] | None = None,
) -> dict[str, Any]:
    base = Decimal(str(base_amount))
    redevance_rate_eff = _apply_abatement_to_rate(Decimal(str(redevance_rate)), Decimal(str(abatement_rate)))
    ristourne_rate_eff = _apply_abatement_to_rate(Decimal(str(ristourne_rate)), Decimal(str(abatement_rate)))

    redevance_amount = _round_money(base * redevance_rate_eff)
    ristourne_amount = _round_money(base * ristourne_rate_eff)
    dtspm_total = _round_money(redevance_amount + ristourne_amount)

    fnp_amount = _round_money(ristourne_amount * Decimal(str(fnp_share)))
    ctd_amount = _round_money(ristourne_amount * Decimal(str(ctd_share)))
    commune_amount = _round_money(ctd_amount * Decimal(str(commune_share)))
    region_amount = _round_money(ctd_amount * Decimal(str(region_share)))
    province_amount = _round_money(ctd_amount * Decimal(str(province_share)))

    ristourne_beneficiaries = [
        {
            "beneficiary_level": "FNP",
            "allocation_share": Decimal(str(fnp_share)),
            "rate_of_base": _ratio(fnp_amount, base),
            "amount": fnp_amount,
        },
        {
            "beneficiary_level": "COMMUNE",
            "allocation_share": Decimal(str(ctd_share)) * Decimal(str(commune_share)),
            "rate_of_base": _ratio(commune_amount, base),
            "amount": commune_amount,
        },
        {
            "beneficiary_level": "REGION",
            "allocation_share": Decimal(str(ctd_share)) * Decimal(str(region_share)),
            "rate_of_base": _ratio(region_amount, base),
            "amount": region_amount,
        },
        {
            "beneficiary_level": "PROVINCE",
            "allocation_share": Decimal(str(ctd_share)) * Decimal(str(province_share)),
            "rate_of_base": _ratio(province_amount, base),
            "amount": province_amount,
        },
    ]
    _adjust_rounding_delta(ristourne_beneficiaries, ristourne_amount)
    for row in ristourne_beneficiaries:
        row["rate_of_base"] = _ratio(Decimal(str(row["amount"])), base)

    redevance_component = {
        "tax_type": "DTSPM_REDEVANCE",
        "rate": redevance_rate_eff,
        "amount": redevance_amount,
        "beneficiaries": [
            {
                "beneficiary_level": "ETAT",
                "allocation_share": Decimal("1"),
                "rate_of_base": _ratio(redevance_amount, base),
                "amount": redevance_amount,
            }
        ],
    }
    ristourne_component = {
        "tax_type": "DTSPM_RISTOURNE",
        "rate": ristourne_rate_eff,
        "amount": ristourne_amount,
        "beneficiaries": ristourne_beneficiaries,
        "ctd": {
            "share_of_ristourne": Decimal(str(ctd_share)),
            "amount": ctd_amount,
            "split": {
                "COMMUNE": Decimal(str(commune_share)),
                "REGION": Decimal(str(region_share)),
                "PROVINCE": Decimal(str(province_share)),
            },
        },
    }
    return {
        "event_type": event_type,
        "base_amount": base,
        "currency": currency,
        "assiette_mode": assiette_mode,
        "assiette_reference": assiette_reference,
        "dtspm_total_rate": _ratio(dtspm_total, base),
        "dtspm_total_amount": dtspm_total,
        "abatement_rate": Decimal(str(abatement_rate)),
        "abatement_reason": abatement_reason,
        "legal_basis": legal_basis or default_legal_basis_for_event(event_type),
        "redevance": redevance_component,
        "ristourne": ristourne_component,
        "components": [redevance_component, ristourne_component],
    }


def compute_tax_event_breakdown(
    *,
    event_type: str,
    base_amount: Decimal,
    currency: str,
    filiere: str = "OR",
    assiette_mode: str = "manual",
    assiette_reference: str | None = None,
    legal_rule_payload_json: str | None = None,
    legal_basis_override: list[str] | None = None,
    is_transformed: bool = False,
    transformation_origin: str | None = None,
) -> dict[str, Any]:
    normalized_event = normalize_event_type(event_type)
    rules = merge_rule_payload(legal_rule_payload_json)
    legal_basis = legal_basis_override or default_legal_basis_for_event(normalized_event)
    base = Decimal(str(base_amount))

    if normalized_event in {EVENT_EXPORT_DTSPM, EVENT_LOCAL_SALE_DTSPM}:
        dtspm = rules.get("dtspm", {}) if isinstance(rules.get("dtspm"), dict) else {}
        split = rules.get("ristourne_split", {}) if isinstance(rules.get("ristourne_split"), dict) else {}
        configured_abatement = _as_decimal(dtspm.get("abatement_rate"), DEFAULT_DTSPM_ABATEMENT)
        applied_abatement, reason = should_apply_dtspm_abatement(
            filiere=filiere,
            event_type=normalized_event,
            is_transformed=is_transformed,
            transformation_origin=transformation_origin,
            abatement_rate=configured_abatement,
        )
        return compute_dtspm_breakdown(
            base,
            currency,
            redevance_rate=_as_decimal(dtspm.get("redevance_rate"), REDEVANCE_RATE),
            ristourne_rate=_as_decimal(dtspm.get("ristourne_rate"), RISTOURNE_RATE),
            fnp_share=_as_decimal(split.get("fnp"), FNP_SHARE_OF_RISTOURNE),
            ctd_share=_as_decimal(split.get("ctd"), CTD_SHARE_OF_RISTOURNE),
            commune_share=_as_decimal(split.get("commune"), COMMUNE_SHARE_OF_CTD),
            region_share=_as_decimal(split.get("region"), REGION_SHARE_OF_CTD),
            province_share=_as_decimal(split.get("province"), PROVINCE_SHARE_OF_CTD),
            abatement_rate=applied_abatement,
            abatement_reason=reason,
            event_type=normalized_event,
            assiette_mode=assiette_mode,
            assiette_reference=assiette_reference,
            legal_basis=legal_basis,
        )

    if normalized_event == EVENT_TITRAGE_POINCONNAGE:
        split = rules.get("titrage_poinconnage_split", {}) if isinstance(rules.get("titrage_poinconnage_split"), dict) else {}
        component = _compute_split_component(
            tax_type="TITRAGE_POINCONNAGE",
            base=base,
            currency=currency,
            shares={
                "BUDGET_GENERAL": _as_decimal(split.get("budget_general"), TITRAGE_BUDGET_SHARE),
                "BGGLM": _as_decimal(split.get("bgglm"), TITRAGE_BGGLM_SHARE),
                "COM": _as_decimal(split.get("com"), TITRAGE_COM_SHARE),
            },
        )
        return {
            "event_type": normalized_event,
            "base_amount": base,
            "currency": currency,
            "assiette_mode": assiette_mode,
            "assiette_reference": assiette_reference,
            "dtspm_total_rate": None,
            "dtspm_total_amount": None,
            "abatement_rate": Decimal("0"),
            "abatement_reason": None,
            "legal_basis": legal_basis,
            "redevance": None,
            "ristourne": None,
            "components": [component],
        }

    if normalized_event == EVENT_DROIT_CARTE_COLLECTEUR:
        split = rules.get("collector_card_right_split", {}) if isinstance(rules.get("collector_card_right_split"), dict) else {}
        component = _compute_split_component(
            tax_type="DROIT_CARTE_COLLECTEUR",
            base=base,
            currency=currency,
            shares={
                "COMMUNE": _as_decimal(split.get("commune"), COLLECTOR_CARD_COMMUNE_SHARE),
                "REGION": _as_decimal(split.get("region"), COLLECTOR_CARD_REGION_SHARE),
                "COM": _as_decimal(split.get("com"), COLLECTOR_CARD_COM_SHARE),
            },
        )
        return {
            "event_type": normalized_event,
            "base_amount": base,
            "currency": currency,
            "assiette_mode": assiette_mode,
            "assiette_reference": assiette_reference,
            "dtspm_total_rate": None,
            "dtspm_total_amount": None,
            "abatement_rate": Decimal("0"),
            "abatement_reason": None,
            "legal_basis": legal_basis,
            "redevance": None,
            "ristourne": None,
            "components": [component],
        }

    return compute_dtspm_breakdown(
        base,
        currency,
        event_type=normalized_event,
        assiette_mode=assiette_mode,
        assiette_reference=assiette_reference,
        legal_basis=legal_basis,
    )
