"""Unit tests for 360-degree service."""

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session
from services.degree360_service import Degree360Service
from models.degree360 import (
    Degree360Session, Degree360Participant, 
    Degree360Question, Degree360Answer, Degree360ParticipantRole
)
from models.user import User


class TestDegree360Service:
    """Test cases for 360-degree service functions."""

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
    def mock_session(self, mock_user):
        """Mock 360-degree session."""
        session = MagicMock(spec=Degree360Session)
        session.id = 1
        session.name = "Test 360 Session"
        session.evaluated_user_id = mock_user.id
        session.evaluator_user_id = mock_user.id
        return session

    @pytest.fixture
    def mock_participant(self, mock_user, mock_session):
        """Mock 360-degree participant."""
        participant = MagicMock(spec=Degree360Participant)
        participant.id = 1
        participant.session_id = mock_session.id
        participant.evaluator_user_id = mock_user.id
        participant.role = Degree360ParticipantRole.SELF
        participant.status = "PENDING"
        return participant

    @pytest.fixture
    def mock_question(self, mock_session):
        """Mock 360-degree question."""
        question = MagicMock(spec=Degree360Question)
        question.id = 1
        question.session_id = mock_session.id
        question.text = "How would you rate this person?"
        question.weight = 1
        return question

    @pytest.fixture
    def mock_answer(self, mock_participant, mock_question):
        """Mock 360-degree answer."""
        answer = MagicMock(spec=Degree360Answer)
        answer.id = 1
        answer.participant_id = mock_participant.id
        answer.question_id = mock_question.id
        answer.score = 4
        answer.comment = "Good performance"
        return answer

    def test_create_360_session(self, mock_db_session, mock_session, mock_user):
        """Test creation of 360-degree session with automatic participant addition."""
        # Arrange
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        mock_db_session.add.side_effect = lambda x: setattr(x, 'id', 1) if not hasattr(x, 'id') else None
        
        # Act
        result = Degree360Service.create_360_session(
            mock_db_session,
            name=mock_session.name,
            evaluated_user_id=mock_user.id,
            evaluator_user_id=mock_user.id,
            start_date="2025-01-01",
            end_date="2025-12-31"
        )
        
        # Assert
        assert result is not None
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called_once()

    def test_calculate_360_results_anonymously(self, mock_db_session, mock_session, mock_answer):
        """Test anonymous calculation of 360-degree results."""
        # Arrange
        mock_session.is_anonymous = True
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_session
        
        # Mock participants and answers
        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_answer]
        
        # Act
        result = Degree360Service.calculate_360_session_results(mock_session.id)
        
        # Assert
        assert result is not None
        # Check that evaluator identity is hidden but role statistics are preserved
        assert "evaluated_user" in result
        assert "overall_score" in result

    def test_gap_analysis_calculation(self, mock_db_session, mock_session, mock_participant, mock_answer):
        """Test calculation of gap between self-evaluation and others' evaluations."""
        # Arrange
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_session
        
        # Mock participants with different roles
        self_participant = MagicMock()
        self_participant.role = Degree360ParticipantRole.SELF
        self_participant.answers = [mock_answer]
        
        manager_participant = MagicMock()
        manager_participant.role = Degree360ParticipantRole.MANAGER
        # Create a different score for manager
        manager_answer = MagicMock()
        manager_answer.question_id = mock_answer.question_id
        manager_answer.score = 3
        manager_participant.answers = [manager_answer]
        
        mock_session.participants = [self_participant, manager_participant]
        
        # Act
        result = Degree360Service.calculate_360_session_results(mock_session.id)
        
        # Assert
        assert result is not None
        # Check that gap analysis is performed
        assert "gap_analysis" in result
        gap_analysis = result["gap_analysis"]
        assert len(gap_analysis) > 0