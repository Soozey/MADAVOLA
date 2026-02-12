from decimal import Decimal, ROUND_HALF_UP


DTSPM_RATE = Decimal("0.05")
REDEVANCE_RATE = Decimal("0.03")
RISTOURNE_RATE = Decimal("0.02")

FNP_SHARE_OF_RISTOURNE = Decimal("0.10")
CTD_SHARE_OF_RISTOURNE = Decimal("0.90")
COMMUNE_SHARE_OF_CTD = Decimal("0.60")
REGION_SHARE_OF_CTD = Decimal("0.30")
PROVINCE_SHARE_OF_CTD = Decimal("0.10")


def _round_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _ratio(value: Decimal, base: Decimal) -> Decimal:
    if base == 0:
        return Decimal("0")
    return (value / base).quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP)


def compute_dtspm_breakdown(base_amount: Decimal, currency: str) -> dict:
    base = Decimal(str(base_amount))
    dtspm_total = _round_money(base * DTSPM_RATE)
    redevance_amount = _round_money(base * REDEVANCE_RATE)
    ristourne_amount = _round_money(base * RISTOURNE_RATE)

    fnp_amount = _round_money(ristourne_amount * FNP_SHARE_OF_RISTOURNE)
    ctd_amount = _round_money(ristourne_amount * CTD_SHARE_OF_RISTOURNE)
    commune_amount = _round_money(ctd_amount * COMMUNE_SHARE_OF_CTD)
    region_amount = _round_money(ctd_amount * REGION_SHARE_OF_CTD)
    province_amount = _round_money(ctd_amount * PROVINCE_SHARE_OF_CTD)

    return {
        "base_amount": base,
        "currency": currency,
        "dtspm_total_rate": DTSPM_RATE,
        "dtspm_total_amount": dtspm_total,
        "redevance": {
            "tax_type": "DTSPM_REDEVANCE",
            "rate": REDEVANCE_RATE,
            "amount": redevance_amount,
            "beneficiaries": [
                {
                    "beneficiary_level": "ETAT",
                    "allocation_share": Decimal("1"),
                    "rate_of_base": _ratio(redevance_amount, base),
                    "amount": redevance_amount,
                }
            ],
        },
        "ristourne": {
            "tax_type": "DTSPM_RISTOURNE",
            "rate": RISTOURNE_RATE,
            "amount": ristourne_amount,
            "beneficiaries": [
                {
                    "beneficiary_level": "FNP",
                    "allocation_share": FNP_SHARE_OF_RISTOURNE,
                    "rate_of_base": _ratio(fnp_amount, base),
                    "amount": fnp_amount,
                },
                {
                    "beneficiary_level": "COMMUNE",
                    "allocation_share": CTD_SHARE_OF_RISTOURNE * COMMUNE_SHARE_OF_CTD,
                    "rate_of_base": _ratio(commune_amount, base),
                    "amount": commune_amount,
                },
                {
                    "beneficiary_level": "REGION",
                    "allocation_share": CTD_SHARE_OF_RISTOURNE * REGION_SHARE_OF_CTD,
                    "rate_of_base": _ratio(region_amount, base),
                    "amount": region_amount,
                },
                {
                    "beneficiary_level": "PROVINCE",
                    "allocation_share": CTD_SHARE_OF_RISTOURNE * PROVINCE_SHARE_OF_CTD,
                    "rate_of_base": _ratio(province_amount, base),
                    "amount": province_amount,
                },
            ],
            "ctd": {
                "share_of_ristourne": CTD_SHARE_OF_RISTOURNE,
                "amount": ctd_amount,
                "split": {
                    "COMMUNE": COMMUNE_SHARE_OF_CTD,
                    "REGION": REGION_SHARE_OF_CTD,
                    "PROVINCE": PROVINCE_SHARE_OF_CTD,
                },
            },
        },
    }
