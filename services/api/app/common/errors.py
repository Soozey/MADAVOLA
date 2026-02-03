from fastapi import HTTPException


def bad_request(message: str, details: dict | None = None) -> HTTPException:
    """Erreur 400 Bad Request standardisée"""
    payload = {"message": message}
    if details:
        payload["details"] = details
    return HTTPException(status_code=400, detail=payload)


def unauthorized(message: str = "non_autorise", details: dict | None = None) -> HTTPException:
    """Erreur 401 Unauthorized"""
    payload = {"message": message}
    if details:
        payload["details"] = details
    return HTTPException(status_code=401, detail=payload)


def forbidden(message: str = "acces_refuse", details: dict | None = None) -> HTTPException:
    """Erreur 403 Forbidden"""
    payload = {"message": message}
    if details:
        payload["details"] = details
    return HTTPException(status_code=403, detail=payload)


def not_found(message: str = "ressource_introuvable", details: dict | None = None) -> HTTPException:
    """Erreur 404 Not Found"""
    payload = {"message": message}
    if details:
        payload["details"] = details
    return HTTPException(status_code=404, detail=payload)


def conflict(message: str = "conflit", details: dict | None = None) -> HTTPException:
    """Erreur 409 Conflict"""
    payload = {"message": message}
    if details:
        payload["details"] = details
    return HTTPException(status_code=409, detail=payload)


def unprocessable_entity(message: str = "donnees_invalides", details: dict | None = None) -> HTTPException:
    """Erreur 422 Unprocessable Entity"""
    payload = {"message": message}
    if details:
        payload["details"] = details
    return HTTPException(status_code=422, detail=payload)
