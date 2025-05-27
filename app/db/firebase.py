# app/db/firebase_db.py

import logging
from typing import Optional
import firebase_admin
from firebase_admin import credentials, firestore
from app.core.config import settings

logger = logging.getLogger(__name__)


class FirebaseDB:
    """Firebase Database connection manager với lazy loading."""

    def __init__(self):
        self.app: Optional[firebase_admin.App] = None
        self.firestore_client: Optional[firestore.Client] = None
        self._connected = False
        self._connection_attempted = False

    def _ensure_connection(self):
        """Đảm bảo Firebase đã được kết nối (lazy loading)."""
        if self._connected:
            return

        if self._connection_attempted:
            raise RuntimeError("Firebase connection failed. Check your configuration.")

        self._connection_attempted = True

        try:
            if not self._has_firebase_config():
                raise RuntimeError("Firebase configuration not found.")

            # Khởi tạo credentials
            if (
                hasattr(settings, "FIREBASE_CREDENTIALS_PATH")
                and settings.FIREBASE_CREDENTIALS_PATH
            ):
                cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
            elif (
                hasattr(settings, "FIREBASE_CREDENTIALS_DICT")
                and settings.FIREBASE_CREDENTIALS_DICT
            ):
                cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_DICT)
            else:
                cred = credentials.ApplicationDefault()

            # Khởi tạo Firebase app
            self.app = firebase_admin.initialize_app(cred)
            self.firestore_client = firestore.client(app=self.app)

            self._connected = True
            logger.info("Firebase connected successfully (lazy loading)")

        except Exception as e:
            logger.error(f"Error connecting to Firebase: {str(e)}")
            self._connected = False
            raise RuntimeError(f"Failed to connect to Firebase: {str(e)}")

    def _has_firebase_config(self) -> bool:
        """Kiểm tra xem có config Firebase không."""
        return (
            hasattr(settings, "FIREBASE_CREDENTIALS_PATH")
            and settings.FIREBASE_CREDENTIALS_PATH
        ) or (
            hasattr(settings, "FIREBASE_CREDENTIALS_DICT")
            and settings.FIREBASE_CREDENTIALS_DICT
        )

    @property
    def firestore(self) -> firestore.Client:
        """Lấy Firestore client (lazy loading)."""
        self._ensure_connection()
        return self.firestore_client

    @property
    def is_connected(self) -> bool:
        """Kiểm tra trạng thái kết nối."""
        return self._connected

    def is_available(self) -> bool:
        """Kiểm tra xem Firebase có sẵn để sử dụng không."""
        return self._has_firebase_config()

    async def disconnect(self):
        """Đóng kết nối Firebase."""
        try:
            if self.app:
                firebase_admin.delete_app(self.app)
                self.app = None
                self.firestore_client = None
                self._connected = False
                self._connection_attempted = False
                logger.info("Firebase connection closed")
        except Exception as e:
            logger.error(f"Error closing Firebase connection: {str(e)}")


# Global instance
firebase_db = FirebaseDB()


# Helper functions
async def close_firebase_connection():
    """Đóng kết nối Firebase."""
    await firebase_db.disconnect()
