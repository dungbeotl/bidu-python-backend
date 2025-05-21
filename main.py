import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import json
from bson import ObjectId
from fastapi.responses import JSONResponse

from app.core import settings
from app.core.openapi import setup_openapi, tags_metadata
from app.api import auth, export, users  # Import từ app/api/__init__.py
from app.db import connect_to_mongo, close_mongo_connection  # Import từ app/db/__init__.py
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from app.utils.serialization import MongoJSONEncoder
from app.api.errors.http_error import (
    http_error_handler,
    validation_error_handler,
    pydantic_error_handler,
    database_error_handler,
    security_error_handler,
    not_found_error_handler,
    forbidden_error_handler,
    redis_error_handler,
    elasticsearch_error_handler,
    input_error_handler,
    rate_limit_error_handler,
)
from app.core.exceptions import (
    DatabaseException,
    UnauthorizedException,
    NotFoundException,
    ForbiddenException,
    RedisException,
    ElasticsearchException,
    BadRequestException,
    RateLimitException,
)


# Định nghĩa lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Kết nối với MongoDB
    await connect_to_mongo()
    yield
    # Shutdown: Đóng kết nối MongoDB
    await close_mongo_connection()


# Tạo custom JSONResponse sử dụng encoder trên
class CustomJSONResponse(JSONResponse):
    media_type = "application/json"

    def render(self, content) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
            cls=MongoJSONEncoder,
        ).encode("utf-8")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API Backend cho hệ thống thương mại điện tử Bidu sử dụng FastAPI, MongoDB, Redis và Elasticsearch",
    docs_url=None,  # Tắt docs mặc định để sử dụng custom docs
    redoc_url="/redoc",
    openapi_tags=tags_metadata,
    contact={
        "name": "Bidu E-commerce Support",
        "url": "https://bidu-ecommerce.com/support",
        "email": "support@bidu-ecommerce.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    terms_of_service="https://bidu-ecommerce.com/terms/",
    lifespan=lifespan,
    openapi_url=None,  # Tắt openapi_url mặc định để sử dụng custom endpoint
    default_response_class=CustomJSONResponse,  # Sử dụng custom JSONResponse
)

# Mount thư mục static nếu cần
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except:
    # Bỏ qua nếu chưa có thư mục static
    pass

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Thiết lập OpenAPI và Swagger UI
setup_openapi(app)

# Include routers
app.include_router(auth.router, prefix="/api/admin/auth", tags=["Admin Authentication"])
app.include_router(users.router, prefix="/api/admin/users", tags=["Admin Users"])
app.include_router(export.router, prefix="/api/admin/export", tags=["Admin Export"])

# Exception handlers
app.add_exception_handler(Exception, http_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(ValidationError, pydantic_error_handler)
app.add_exception_handler(DatabaseException, database_error_handler)
app.add_exception_handler(UnauthorizedException, security_error_handler)
app.add_exception_handler(NotFoundException, not_found_error_handler)
app.add_exception_handler(ForbiddenException, forbidden_error_handler)
app.add_exception_handler(RedisException, redis_error_handler)
app.add_exception_handler(ElasticsearchException, elasticsearch_error_handler)
app.add_exception_handler(BadRequestException, input_error_handler)
app.add_exception_handler(RateLimitException, rate_limit_error_handler)


@app.get("/", tags=["Root"])
async def root():
    return {"message": f"Chào mừng đến với {settings.APP_NAME} API"}


if __name__ == "__main__":
    # KHUYẾN NGHỊ: Thay vì chạy trực tiếp file này, nên sử dụng lệnh:
    # uvicorn main:app --reload
    #
    # Tuy nhiên, chúng ta vẫn giữ code này để tương thích ngược với các script
    # và tài liệu hiện có.
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
