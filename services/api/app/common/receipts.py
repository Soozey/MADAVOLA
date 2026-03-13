from datetime import datetime, timezone


def build_receipt_number(prefix: str, entity_id: int) -> str:
    now = datetime.now(timezone.utc)
    return f"{prefix}-{now.strftime('%Y%m%d')}-{entity_id:08d}"


def build_qr_value(kind: str, identifier: str) -> str:
    return f"MADAVOLA:{kind}:{identifier}"


def build_simple_pdf(
    title: str,
    lines: list[str],
    *,
    page_width_pt: int = 595,
    page_height_pt: int = 842,
    start_x: int = 50,
    start_y: int = 780,
    line_height: int = 18,
    font_size: int = 12,
) -> bytes:
    # Minimal single-page PDF (Helvetica) to store a printable receipt/card.
    text = [title] + lines
    text_ops = ["BT", f"/F1 {font_size} Tf", f"{start_x} {start_y} Td"]
    for idx, line in enumerate(text):
        safe = (
            str(line)
            .replace("\\", "\\\\")
            .replace("(", "\\(")
            .replace(")", "\\)")
        )
        if idx > 0:
            text_ops.append(f"0 -{line_height} Td")
        text_ops.append(f"({safe}) Tj")
    text_ops.append("ET")
    stream_data = "\n".join(text_ops).encode("utf-8")

    objects: list[bytes] = []
    objects.append(b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n")
    objects.append(b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n")
    objects.append(
        f"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 {page_width_pt} {page_height_pt}] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n".encode("utf-8")
    )
    objects.append(
        b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
    )
    objects.append(
        f"5 0 obj << /Length {len(stream_data)} >> stream\n".encode("utf-8")
        + stream_data
        + b"\nendstream endobj\n"
    )

    header = b"%PDF-1.4\n"
    body = b""
    offsets = [0]
    current = len(header)
    for obj in objects:
        offsets.append(current)
        body += obj
        current += len(obj)

    xref_start = len(header) + len(body)
    xref = [b"xref\n", f"0 {len(offsets)}\n".encode("utf-8"), b"0000000000 65535 f \n"]
    for off in offsets[1:]:
        xref.append(f"{off:010d} 00000 n \n".encode("utf-8"))
    trailer = (
        b"trailer\n"
        + f"<< /Size {len(offsets)} /Root 1 0 R >>\n".encode("utf-8")
        + b"startxref\n"
        + f"{xref_start}\n".encode("utf-8")
        + b"%%EOF\n"
    )
    return header + body + b"".join(xref) + trailer
