# Bidu E-commerce Backend API

Backend API cho hệ thống thương mại điện tử sử dụng FastAPI, MongoDB, Redis và Elasticsearch.

## Kiến trúc

Dự án được phát triển theo kiến trúc 3 lớp:

1. **API Layer** (`app/api`)
   - Xử lý HTTP requests/responses
   - Định nghĩa các endpoint
   - Xác thực và phân quyền
   - Validation request data

2. **Service Layer** (`app/services`)
   - Business logic
   - Gọi các repositories
   - Xử lý các rules nghiệp vụ
   - Tích hợp với các dịch vụ bên ngoài

3. **Data Access Layer** (`app/db`)
   - Repositories cho tương tác với database
   - Tách biệt logic database khỏi business logic

## Công nghệ sử dụng

- **FastAPI**: Web framework hiệu năng cao
- **MongoDB** + **Beanie ODM**: Cơ sở dữ liệu NoSQL với tích hợp Pydantic
- **Redis**: Cache và quản lý phiên
- **Elasticsearch**: Tìm kiếm và phân tích dữ liệu

## Tính năng và cải tiến mới

- **Xử lý ObjectId tự động**: Chuyển đổi vấn đề serialization MongoDB ObjectId tự động
- **Module hóa codebase**: Sử dụng `__init__.py` để export và tổ chức code tốt hơn
- **Tích hợp Beanie ODM**: Tận dụng khả năng tích hợp Pydantic với MongoDB
- **JSON serialization tự động**: Xử lý nhất quán dữ liệu từ MongoDB khi trả về API

## Cài đặt và chạy

### Yêu cầu

- Python 3.8+
- Docker và Docker Compose (tùy chọn)

### Cài đặt

1. Clone repository:
```bash
git clone https://github.com/yourusername/bidu-ecommerce-python-backend.git
cd bidu-ecommerce-python-backend
```

2. Tạo và kích hoạt môi trường ảo:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

4. Tạo file .env trong thư mục gốc và thiết lập các biến môi trường:
```
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=bidu_ecommerce
SECRET_KEY=your_secret_key_here
DEBUG=True
ENVIRONMENT=development
```

### Chạy ứng dụng

### Môi trường phát triển
```bash
make dev
```

#### Sử dụng Python:
```bash
python main.py
```

#### Sử dụng Docker:
```bash
docker-compose up
```

Ứng dụng sẽ chạy tại `http://localhost:8000`

## API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Cấu trúc dự án

```
app/
│
├── api/                 # API Layer
│   ├── routes/          # API endpoints
│   ├── errors/          # Error handlers
│   └── dependencies.py  # API dependencies
│
├── core/                # Core configuration
│   ├── config.py        # Settings and configuration
│   ├── security.py      # Security utilities
│   └── exceptions.py    # Custom exceptions
│
├── db/                  # Data Access Layer
│   ├── mongodb.py       # MongoDB connection
│   └── repositories/    # Data repositories
│
├── integrations/        # Third-party integrations
│   ├── elastic/         # Elasticsearch client
│   └── redis/           # Redis client
│
├── models/              # Data models (Beanie Documents)
│   ├── user.py
│   └── product.py
│
├── schemas/             # Pydantic schemas cho API
│
├── services/            # Service Layer
│   ├── base.py
│   └── user.py
│
└── utils/               # Utility functions
    ├── serialization.py # Xử lý MongoDB ObjectId serialization
    └── pagination.py    # Phân trang kết quả
```

## Module Imports

Codebase sử dụng mô hình module hóa để đơn giản hóa imports:

```python
# Không sử dụng
from app.models.user import User
from app.models.product import Product

# Thay vào đó sử dụng
from app.models import User, Product
```

Mỗi module có file `__init__.py` để export các classes và functions quan trọng.

## Các tính năng chính

- Xác thực và ủy quyền (JWT)
- CRUD cho người dùng và sản phẩm
- Tìm kiếm sản phẩm với Elasticsearch
- Cache với Redis
- Xử lý lỗi toàn diện
- Validation dữ liệu với Pydantic
- Xử lý ObjectId tự động