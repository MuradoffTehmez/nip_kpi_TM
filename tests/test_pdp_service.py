"""Unit tests for PDP (Personal Development Plan) service."""

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session
from services.pdp_service import PDPService
from models.pdp import DevelopmentPlan, PlanItem
from models.user import User
from models.notification import Notification


class TestPDPService:
    """Test cases for PDP service functions."""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return MagicMock(spec=Session)

    @pytest.fixture
    def mock_user(self):
        """Mock user object."""
        user = MagicMock(spec=User)
        user.id = 1
        user.username = "testuser"
        return user

    @pytest.fixture
    def mock_plan(self, mock_user):
        """Mock development plan."""
        plan = MagicMock(spec=DevelopmentPlan)
        plan.id = 1
        plan.user_id = mock_user.id
        plan.title = "Test Development Plan"
        plan.description = "Test plan for testing"
        return plan

    @pytest.fixture
    def mock_plan_item(self, mock_plan):
        """Mock plan item."""
        item = MagicMock(spec=PlanItem)
        item.id = 1
        item.plan_id = mock_plan.id
        item.title = "Test Goal"
        item.description = "Test goal description"
        item.progress = 50
        item.is_completed = False
        return item

    @pytest.fixture
    def mock_notification(self):
        """Mock notification."""
        notification = MagicMock(spec=Notification)
        notification.id = 1
        notification.user_id = 1
        notification.message = "Test notification"
        notification.is_read = False
        return notification

    def test_add_comment_to_plan_item(self, mock_db_session, mock_plan_item, mock_user):
        """Test adding comment to plan item and sending notification."""
        # Arrange
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_plan_item
        comment_text = "This is a test comment"
        
        # Mock the notification service
        with patch('services.notification_service.NotificationService.create_notification') as mock_create_notification:
            mock_create_notification.return_value = MagicMock()
            
            # Act
            result = PDPService.add_comment_to_plan_item(
                mock_db_session, 
                mock_plan_item.id, 
                comment_text, 
                mock_user.id
            )
            
            # Assert
            assert result is True
            mock_create_notification.assert_called_once()
            mock_db_session.commit.assert_called_once()

    def test_progress_update_marks_completed(self, mock_db_session, mock_plan_item, mock_plan):
        """Test that 100% progress marks item as completed."""
        # Arrange
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_plan_item
        mock_plan_item.progress = 90
        mock_plan_item.is_completed = False
        
        # Act
        result = PDPService.update_plan_item_progress(
            mock_db_session, 
            mock_plan_item.id, 
            100, 
            mock_user_id=1
        )
        
        # Assert
        assert result is True
        assert mock_plan_item.progress == 100
        assert mock_plan_item.is_completed is True
        mock_db_session.commit.assert_called_once()

    def test_progress_update_below_100_not_completed(self, mock_db_session, mock_plan_item):
        """Test that progress below 100% does not mark item as completed."""
        # Arrange
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_plan_item
        mock_plan_item.progress = 50
        mock_plan_item.is_completed = False
        
        # Act
        result = PDPService.update_plan_item_progress(
            mock_db_session, 
            mock_plan_item.id, 
            75, 
            mock_user_id=1
        )
        
        # Assert
        assert result is True
        assert mock_plan_item.progress == 75
        assert mock_plan_item.is_completed is False
        mock_db_session.commit.assert_called_once()