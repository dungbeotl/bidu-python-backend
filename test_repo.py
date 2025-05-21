import asyncio
from app.db.repositories.ecategory import ECategoryRepository

async def test():
    repo = ECategoryRepository()
    print("Đang truy vấn categories...")
    res = await repo.get_all_categories()
    print(f'Đã lấy được {len(res)} categories')
    if len(res) > 0:
        print(f'Category đầu tiên: {res[0].id} - {res[0].name}')

if __name__ == "__main__":
    asyncio.run(test()) 