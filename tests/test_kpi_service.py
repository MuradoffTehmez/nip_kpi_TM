"""Unit tests for KPI service."""

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session
from services.kpi_service import KpiService
from models.kpi import Evaluation, EvaluationStatus, Question, Answer
from models.user import User


class TestKpiService:
    """Test cases for KPI service functions."""

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
    def mock_question(self):
        """Mock question object."""
        question = MagicMock(spec=Question)
        question.id = 1
        question.text = "Test question"
        question.weight = 1.0
        return question

    @pytest.fixture
    def mock_evaluation(self, mock_user, mock_question):
        """Mock evaluation object."""
        evaluation = MagicMock(spec=Evaluation)
        evaluation.id = 1
        evaluation.evaluated_user_id = mock_user.id
        evaluation.evaluator_user_id = mock_user.id
        evaluation.status = EvaluationStatus.PENDING
        
        # Mock answer
        answer = MagicMock(spec=Answer)
        answer.question = mock_question
        answer.score = 4
        answer.author_role = 'employee'
        
        evaluation.answers = [answer]
        return evaluation

    def test_calculate_evaluation_score(self, mock_db_session, mock_evaluation):
        """Test calculation of evaluation score with weighted questions."""
        # Arrange
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_evaluation
        
        # Act
        result = KpiService.calculate_evaluation_score(mock_db_session, mock_evaluation.id)
        
        # Assert
        assert result is not None
        # With one question with weight 1.0 and score 4, the result should be 4.0
        assert result == 4.0

    def test_submit_evaluation_as_employee(self, mock_db_session, mock_evaluation, mock_user):
        """Test employee submission of evaluation."""
        # Arrange
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_evaluation
        mock_evaluation.status = EvaluationStatus.PENDING
        
        # Act
        result = KpiService.submit_evaluation_as_employee(mock_db_session, mock_evaluation.id, mock_user.id)
        
        # Assert
        assert result is True
        assert mock_evaluation.status == EvaluationStatus.SELF_EVAL_COMPLETED
        mock_db_session.commit.assert_called_once()

    def test_submit_evaluation_as_manager(self, mock_db_session, mock_evaluation, mock_user):
        """Test manager submission of evaluation."""
        # Arrange
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_evaluation
        mock_evaluation.status = EvaluationStatus.SELF_EVAL_COMPLETED
        
        # Act
        result = KpiService.submit_evaluation_as_manager(mock_db_session, mock_evaluation.id, mock_user.id)
        
        # Assert
        assert result is True
        assert mock_evaluation.status == EvaluationStatus.FINALIZED
        mock_db_session.commit.assert_called_once()

    def test_permission_denied_for_evaluation(self, mock_db_session, mock_evaluation, mock_user):
        """Test that unauthorized users cannot submit evaluations."""
        # Arrange
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_evaluation
        # Set evaluator user to a different user
        mock_evaluation.evaluator_user_id = 999
        
        # Act & Assert
        with pytest.raises(PermissionError):
            KpiService.submit_evaluation_as_employee(mock_db_session, mock_evaluation.id, mock_user.id)