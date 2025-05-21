from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse
from typing import Dict, Any
from app.core.config import settings

# Tags cho OpenAPI
tags_metadata = [
    {
        "name": "Authentication",
        "description": "Đăng nhập, đăng ký và quản lý token",
    },
    {
        "name": "Users",
        "description": "Quản lý người dùng, cập nhật thông tin",
    },
    {
        "name": "Root",
        "description": "Thông tin API chính",
    },
]


def setup_openapi(app: FastAPI):
    """Thiết lập tất cả các cấu hình và routes liên quan đến OpenAPI và Swagger UI"""

    # Tắt openapi_url mặc định
    app.openapi_url = None

    # Custom Swagger UI endpoint
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        """Tạo trang Swagger UI tùy chỉnh"""
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title=f"{settings.APP_NAME} - Swagger UI",
            oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
            swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@4/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@4/swagger-ui.css",
            swagger_favicon_url=None,
            swagger_ui_parameters={
                "persistAuthorization": True,
                "defaultModelsExpandDepth": -1,
                "displayRequestDuration": True,
                "docExpansion": "list",
                "filter": True,
            },
        )

    # Custom OpenAPI schema endpoint
    @app.get("/openapi.json", include_in_schema=False)
    async def custom_openapi():
        # Tạo schema từ đầu
        openapi: Dict[str, Any] = {
            "openapi": "3.0.0",
            "info": {
                "title": settings.APP_NAME,
                "version": settings.APP_VERSION,
                "description": "API Backend cho hệ thống thương mại điện tử Bidu",
                "termsOfService": "https://bidu-ecommerce.com/terms/",
                "contact": {
                    "name": "Bidu E-commerce Support",
                    "url": "https://bidu-ecommerce.com/support",
                    "email": "support@bidu-ecommerce.com",
                },
                "license": {
                    "name": "MIT License",
                    "url": "https://opensource.org/licenses/MIT",
                },
            },
            "paths": {},
            "components": {
                "securitySchemes": {
                    "bearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT",
                        "description": "Nhập JWT token với định dạng: Bearer {token}",
                    },
                    "OAuth2PasswordBearer": {
                        "type": "oauth2",
                        "flows": {
                            "password": {"tokenUrl": "/api/auth/login", "scopes": {}}
                        },
                    },
                }
            },
            "tags": tags_metadata,
        }

        # Lấy schema đã tạo bởi FastAPI nhưng không sử dụng phiên bản của nó
        from fastapi.openapi.utils import get_openapi

        original_schema = get_openapi(
            title=settings.APP_NAME,
            version=settings.APP_VERSION,
            description="API Backend cho hệ thống thương mại điện tử Bidu",
            routes=app.routes,
            tags=tags_metadata,
        )

        # Sao chép paths và schemas từ schema gốc
        openapi["paths"] = original_schema.get("paths", {})

        if (
            "components" in original_schema
            and "schemas" in original_schema["components"]
        ):
            openapi["components"]["schemas"] = original_schema["components"]["schemas"]

        return JSONResponse(content=openapi)
