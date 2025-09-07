"""Unit tests for Competency service."""

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session
from services.competency_service import CompetencyService
from models.competency import Competency
from models.kpi import Question as KPIQuestion
from models.degree360 import Degree360Question


class TestCompetencyService:
    """Test cases for Competency service functions."""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return MagicMock(spec=Session)

    @pytest.fixture
    def mock_competency(self):
        """Mock competency object."""
        competency = MagicMock(spec=Competency)
        competency.id = 1
        competency.name = "Leadership"
        competency.description = "Leadership skills"
        competency.category = "Management"
        return competency

    @pytest.fixture
    def mock_kpi_question(self):
        """Mock KPI question object."""
        question = MagicMock(spec=KPIQuestion)
        question.id = 1
        question.text = "Demonstrates leadership skills"
        question.competencies = []
        return question

    @pytest.fixture
    def mock_360_question(self):
        """Mock 360-degree question object."""
        question = MagicMock(spec=Degree360Question)
        question.id = 1
        question.text = "How would you rate this person's leadership skills?"
        question.competencies = []
        return question

    def test_create_competency(self, mock_db_session, mock_competency):
        """Test creation of a new competency."""
        # Arrange
        mock_db_session.add.side_effect = lambda x: setattr(x, 'id', 1)
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_competency
        
        # Act
        service = CompetencyService(mock_db_session)
        result = service.create_competency(
            name="Leadership",
            description="Leadership skills",
            category="Management"
        )
        
        # Assert
        assert result is not None
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    def test_get_competency_by_id(self, mock_db_session, mock_competency):
        """Test retrieving a competency by ID."""
        # Arrange
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_competency
        
        # Act
        service = CompetencyService(mock_db_session)
        result = service.get_competency_by_id(mock_competency.id)
        
        # Assert
        assert result is not None
        assert result.id == mock_competency.id
        assert result.name == mock_competency.name

    def test_get_competency_by_name(self, mock_db_session, mock_competency):
        """Test retrieving a competency by name."""
        # Arrange
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_competency
        
        # Act
        service = CompetencyService(mock_db_session)
        result = service.get_competency_by_name(mock_competency.name)
        
        # Assert
        assert result is not None
        assert result.name == mock_competency.name

    def test_update_competency(self, mock_db_session, mock_competency):
        """Test updating a competency."""
        # Arrange
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_competency
        
        # Act
        service = CompetencyService(mock_db_session)
        new_name = "Updated Leadership"
        result = service.update_competency(
            competency_id=mock_competency.id,
            name=new_name
        )
        
        # Assert
        assert result is not None
        assert result.name == new_name
        mock_db_session.commit.assert_called_once()

    def test_delete_competency(self, mock_db_session, mock_competency):
        """Test deleting a competency."""
        # Arrange
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_competency
        
        # Act
        service = CompetencyService(mock_db_session)
        result = service.delete_competency(mock_competency.id)
        
        # Assert
        assert result is True
        mock_db_session.delete.assert_called_once_with(mock_competency)
        mock_db_session.commit.assert_called_once()

    def test_associate_kpi_question(self, mock_db_session, mock_competency, mock_kpi_question):
        """Test associating a KPI question with a competency."""
        # Arrange
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            mock_competency, mock_kpi_question
        ]
        # Mock the competencies list
        mock_kpi_question.competencies = []
        
        # Act
        service = CompetencyService(mock_db_session)
        result = service.associate_kpi_question(
            competency_id=mock_competency.id,
            question_id=mock_kpi_question.id
        )
        
        # Assert
        assert result is True
        # Check that the competency was added to the question's competencies list
        assert mock_competency in mock_kpi_question.competencies
        mock_db_session.commit.assert_called_once()

    def test_associate_360_question(self, mock_db_session, mock_competency, mock_360_question):
        """Test associating a 360-degree question with a competency."""
        # Arrange
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            mock_competency, mock_360_question
        ]
        # Mock the competencies list
        mock_360_question.competencies = []
        
        # Act
        service = CompetencyService(mock_db_session)
        result = service.associate_360_question(
            competency_id=mock_competency.id,
            question_id=mock_360_question.id
        )
        
        # Assert
        assert result is True
        # Check that the competency was added to the question's competencies list
        assert mock_competency in mock_360_question.competencies
        mock_db_session.commit.assert_called_once()

    def test_get_performance_by_competency(self, mock_db_session, mock_competency):
        """Test calculating performance by competency."""
        # Arrange
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_competency
        # Mock some scores for testing
        mock_competency.kpi_questions = []
        mock_competency.degree360_questions = []
        
        # Act
        service = CompetencyService(mock_db_session)
        result = service.get_performance_by_competency(
            user_id=1,
            competency_id=mock_competency.id
        )
        
        # Assert
        # Since we have no questions/scores, result should be None
        assert result is None