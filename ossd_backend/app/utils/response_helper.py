from typing import Dict, Any

def success_response(message: str, data: Any = None) -> Dict[str, Any]:
    """
    成功响应
    """
    response = {
        "success": True,
        "message": message
    }
    if data is not None:
        response["data"] = data
    return response

def error_response(message: str, data: Any = None) -> Dict[str, Any]:
    """
    错误响应
    """
    response = {
        "success": False,
        "message": message
    }
    if data is not None:
        response["data"] = data
    return response 