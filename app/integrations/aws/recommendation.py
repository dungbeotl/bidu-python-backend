import boto3
from app.core.config import settings


class RecommendationService:
    def __init__(self):

        self.region = settings.AWS_REGION
        self.AWS_ACCESS_KEY_ID = settings.AWS_ACCESS_KEY_ID
        self.AWS_SECRET_ACCESS_KEY = settings.AWS_SECRET_ACCESS_KEY
        self.RECOMMENDER_ARN_FOR_YOU = settings.AWS_RECOMMENDER_ARN_FOR_YOU
        self.RECOMMENDER_ARN_MOST_VIEWED = settings.AWS_RECOMMENDER_ARN_MOST_VIEWED
        self.RECOMMENDER_ARN_BEST_SELLERS = settings.AWS_RECOMMENDER_ARN_BEST_SELLERS

        self.client = boto3.client("personalize-runtime", region_name=self.region)

    def get_recommendations_for_you(self, user_id: str, num_results: int = 10):
        response = self.client.get_recommendations(
            userId=user_id,
            numResults=num_results,
            recommenderArn=self.RECOMMENDER_ARN_FOR_YOU,
        )
        return response.get("itemList", [])

    def get_recommendations_most_viewed(self, user_id: str, num_results: int = 10):
        response = self.client.get_recommendations(
            userId=user_id,
            numResults=num_results,
            recommenderArn=self.RECOMMENDER_ARN_MOST_VIEWED,
        )
        return response.get("itemList", [])

    def get_recommendations_best_sellers(self, user_id: str, num_results: int = 10):
        response = self.client.get_recommendations(
            userId=user_id,
            numResults=num_results,
            recommenderArn=self.RECOMMENDER_ARN_BEST_SELLERS,
        )
        return response.get("itemList", [])
