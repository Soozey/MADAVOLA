from fastapi import HTTPException


def bad_request(message: str, details: dict | None = None) -> HTTPException:
    payload = {"message": message}
    if details:
        payload["details"] = details
    return HTTPException(status_code=400, detail=payload)
