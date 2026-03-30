def api_success(data=None, message="OK"):
    return {
        "success": True,
        "message": message,
        "data": data or {},
        "errors": None,
    }


def api_error(message="Request failed", errors=None):
    return {
        "success": False,
        "message": message,
        "data": {},
        "errors": errors or {},
    }
