from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

async def http_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Xử lý lỗi HTTP tổng quát.
    """
    return JSONResponse(
        status_code=getattr(exc, "status_code", status.HTTP_500_INTERNAL_SERVER_ERROR),
        content={"detail": getattr(exc, "detail", str(exc))},
    )

async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Xử lý lỗi validation từ FastAPI.
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "body": exc.body
        },
    )

async def pydantic_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """
    Xử lý lỗi validation từ Pydantic.
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )

# Xử lý lỗi database
async def database_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Xử lý lỗi từ cơ sở dữ liệu.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Lỗi cơ sở dữ liệu", "message": str(exc)},
    )

# Xử lý lỗi bảo mật
async def security_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Xử lý lỗi bảo mật.
    """
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "Lỗi xác thực", "message": str(exc)},
        headers={"WWW-Authenticate": "Bearer"},
    )

# Xử lý lỗi không tìm thấy
async def not_found_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Xử lý lỗi không tìm thấy tài nguyên.
    """
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": "Không tìm thấy tài nguyên", "message": str(exc)},
    )

# Xử lý lỗi cấm truy cập
async def forbidden_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Xử lý lỗi cấm truy cập.
    """
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": "Cấm truy cập", "message": str(exc)},
    )

# Xử lý lỗi Redis
async def redis_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Xử lý lỗi từ Redis.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Lỗi Redis cache", "message": str(exc)},
    )

# Xử lý lỗi Elasticsearch
async def elasticsearch_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Xử lý lỗi từ Elasticsearch.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Lỗi Elasticsearch", "message": str(exc)},
    )

# Xử lý lỗi đầu vào
async def input_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Xử lý lỗi đầu vào từ người dùng.
    """
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "Dữ liệu đầu vào không hợp lệ", "message": str(exc)},
    )

# Xử lý lỗi giới hạn truy cập
async def rate_limit_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Xử lý lỗi giới hạn truy cập.
    """
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": "Quá nhiều yêu cầu", "message": str(exc)},
    )