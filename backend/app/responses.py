"""Unified JSON response envelope helpers."""


def success_response(data: object = None, message: str = "success", code: int = 200) -> dict:
    """Build a unified success response envelope."""
    return {"code": code, "message": message, "data": data}


def error_response(message: str, code: int = 500, data: object = None) -> dict:
    """Build a unified error response envelope."""
    return {"code": code, "message": message, "data": data}
