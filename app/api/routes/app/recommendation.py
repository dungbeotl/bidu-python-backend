from typing import Dict, List, Optional
import logging
from fastapi import APIRouter, Depends, Query, HTTPException, status

from app.api.dependencies import get_current_user
from app.integrations.aws.recommendation import RecommendationService

router = APIRouter()

logger = logging.getLogger(__name__)


@router.get(
    "/recommendations/for-you",
    summary="Lấy gợi ý sản phẩm dành cho người dùng",
    description="""
    Lấy danh sách gợi ý sản phẩm được cá nhân hóa cho người dùng cụ thể
    sử dụng AWS Personalize với recommender "For You".
    
    Trả về danh sách item IDs được sắp xếp theo độ liên quan giảm dần.
    """,
    response_model=Dict,
)
async def get_recommendations_for_you(
    user_id: str = Query(..., description="ID của người dùng"),
    num_results: int = Query(10, ge=1, le=50, description="Số lượng gợi ý tối đa"),
    # current_user: Dict = Depends(get_current_user)
):
    """
    Lấy gợi ý sản phẩm dành cho người dùng cụ thể.
    """
    try:
        recommendation_service = RecommendationService()
        recommendations = recommendation_service.get_recommendations_for_you(
            user_id=user_id, 
            num_results=num_results
        )
        
        return {
            "success": True,
            "message": f"Lấy {len(recommendations)} gợi ý cho người dùng {user_id} thành công",
            "data": {
                "user_id": user_id,
                "recommender_type": "for_you",
                "total_items": len(recommendations),
                "items": recommendations
            }
        }
    except Exception as e:
        logger.error(f"Error getting recommendations for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi lấy gợi ý sản phẩm: {str(e)}"
        )


@router.get(
    "/recommendations/most-viewed",
    summary="Lấy gợi ý sản phẩm được xem nhiều nhất",
    description="""
    Lấy danh sách gợi ý sản phẩm được xem nhiều nhất cho người dùng cụ thể
    sử dụng AWS Personalize với recommender "Most Viewed".
    
    Trả về danh sách item IDs được sắp xếp theo độ liên quan giảm dần.
    """,
    response_model=Dict,
)
async def get_recommendations_most_viewed(
    user_id: str = Query(..., description="ID của người dùng"),
    num_results: int = Query(10, ge=1, le=50, description="Số lượng gợi ý tối đa"),
    # current_user: Dict = Depends(get_current_user)
):
    """
    Lấy gợi ý sản phẩm được xem nhiều nhất cho người dùng cụ thể.
    """
    try:
        recommendation_service = RecommendationService()
        recommendations = recommendation_service.get_recommendations_most_viewed(
            user_id=user_id, 
            num_results=num_results
        )
        
        return {
            "success": True,
            "message": f"Lấy {len(recommendations)} sản phẩm được xem nhiều cho người dùng {user_id} thành công",
            "data": {
                "user_id": user_id,
                "recommender_type": "most_viewed",
                "total_items": len(recommendations),
                "items": recommendations
            }
        }
    except Exception as e:
        logger.error(f"Error getting most viewed recommendations for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi lấy sản phẩm được xem nhiều: {str(e)}"
        )


@router.get(
    "/recommendations/best-sellers",
    summary="Lấy gợi ý sản phẩm bán chạy nhất",
    description="""
    Lấy danh sách gợi ý sản phẩm bán chạy nhất cho người dùng cụ thể
    sử dụng AWS Personalize với recommender "Best Sellers".
    
    Trả về danh sách item IDs được sắp xếp theo độ liên quan giảm dần.
    """,
    response_model=Dict,
)
async def get_recommendations_best_sellers(
    user_id: str = Query(..., description="ID của người dùng"),
    num_results: int = Query(10, ge=1, le=50, description="Số lượng gợi ý tối đa"),
    # current_user: Dict = Depends(get_current_user)
):
    """
    Lấy gợi ý sản phẩm bán chạy nhất cho người dùng cụ thể.
    """
    try:
        recommendation_service = RecommendationService()
        recommendations = recommendation_service.get_recommendations_best_sellers(
            user_id=user_id, 
            num_results=num_results
        )
        
        return {
            "success": True,
            "message": f"Lấy {len(recommendations)} sản phẩm bán chạy cho người dùng {user_id} thành công",
            "data": {
                "user_id": user_id,
                "recommender_type": "best_sellers",
                "total_items": len(recommendations),
                "items": recommendations
            }
        }
    except Exception as e:
        logger.error(f"Error getting best seller recommendations for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi lấy sản phẩm bán chạy: {str(e)}"
        ) 