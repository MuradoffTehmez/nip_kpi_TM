"""Service layer for competency management."""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from models.competency import Competency
from models.kpi import Question as KPIQuestion
from models.degree360 import Degree360Question
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CompetencyService:
    """Service class for managing competencies and their relationships."""
    
    def __init__(self, db_session: Session):
        """
        Initialize the competency service.
        
        Args:
            db_session: Database session
        """
        self.db = db_session
    
    def create_competency(self, name: str, description: Optional[str] = None, 
                         category: Optional[str] = None) -> Competency:
        """
        Create a new competency.
        
        Args:
            name: Name of the competency
            description: Description of the competency
            category: Category of the competency
            
        Returns:
            Created competency object
            
        Raises:
            SQLAlchemyError: If there's an error creating the competency
        """
        try:
            competency = Competency(
                name=name,
                description=description,
                category=category
            )
            self.db.add(competency)
            self.db.commit()
            self.db.refresh(competency)
            logger.info(f"Created competency: {name}")
            return competency
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error creating competency {name}: {str(e)}")
            raise
    
    def get_competency_by_id(self, competency_id: int) -> Optional[Competency]:
        """
        Get a competency by its ID.
        
        Args:
            competency_id: ID of the competency
            
        Returns:
            Competency object or None if not found
        """
        return self.db.query(Competency).filter(Competency.id == competency_id).first()
    
    def get_competency_by_name(self, name: str) -> Optional[Competency]:
        """
        Get a competency by its name.
        
        Args:
            name: Name of the competency
            
        Returns:
            Competency object or None if not found
        """
        return self.db.query(Competency).filter(Competency.name == name).first()
    
    def get_all_competencies(self, category: Optional[str] = None) -> List[Competency]:
        """
        Get all competencies, optionally filtered by category.
        
        Args:
            category: Optional category to filter by
            
        Returns:
            List of competency objects
        """
        query = self.db.query(Competency)
        if category:
            query = query.filter(Competency.category == category)
        return query.all()
    
    def update_competency(self, competency_id: int, name: Optional[str] = None,
                         description: Optional[str] = None, category: Optional[str] = None) -> Optional[Competency]:
        """
        Update a competency.
        
        Args:
            competency_id: ID of the competency to update
            name: New name (optional)
            description: New description (optional)
            category: New category (optional)
            
        Returns:
            Updated competency object or None if not found
            
        Raises:
            SQLAlchemyError: If there's an error updating the competency
        """
        try:
            competency = self.get_competency_by_id(competency_id)
            if not competency:
                return None
            
            if name is not None:
                competency.name = name
            if description is not None:
                competency.description = description
            if category is not None:
                competency.category = category
                
            self.db.commit()
            self.db.refresh(competency)
            logger.info(f"Updated competency ID {competency_id}")
            return competency
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating competency ID {competency_id}: {str(e)}")
            raise
    
    def delete_competency(self, competency_id: int) -> bool:
        """
        Delete a competency.
        
        Args:
            competency_id: ID of the competency to delete
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            SQLAlchemyError: If there's an error deleting the competency
        """
        try:
            competency = self.get_competency_by_id(competency_id)
            if not competency:
                return False
            
            self.db.delete(competency)
            self.db.commit()
            logger.info(f"Deleted competency ID {competency_id}")
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error deleting competency ID {competency_id}: {str(e)}")
            raise
    
    def associate_kpi_question(self, competency_id: int, question_id: int) -> bool:
        """
        Associate a KPI question with a competency.
        
        Args:
            competency_id: ID of the competency
            question_id: ID of the KPI question
            
        Returns:
            True if associated, False if either entity not found
            
        Raises:
            SQLAlchemyError: If there's an error creating the association
        """
        try:
            competency = self.get_competency_by_id(competency_id)
            question = self.db.query(KPIQuestion).filter(KPIQuestion.id == question_id).first()
            
            if not competency or not question:
                return False
            
            # Check if already associated
            if competency not in question.competencies:
                question.competencies.append(competency)
                self.db.commit()
                logger.info(f"Associated KPI question {question_id} with competency {competency_id}")
            
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error associating KPI question {question_id} with competency {competency_id}: {str(e)}")
            raise
    
    def dissociate_kpi_question(self, competency_id: int, question_id: int) -> bool:
        """
        Dissociate a KPI question from a competency.
        
        Args:
            competency_id: ID of the competency
            question_id: ID of the KPI question
            
        Returns:
            True if dissociated, False if either entity not found or not associated
            
        Raises:
            SQLAlchemyError: If there's an error removing the association
        """
        try:
            competency = self.get_competency_by_id(competency_id)
            question = self.db.query(KPIQuestion).filter(KPIQuestion.id == question_id).first()
            
            if not competency or not question:
                return False
            
            # Check if associated
            if competency in question.competencies:
                question.competencies.remove(competency)
                self.db.commit()
                logger.info(f"Dissociated KPI question {question_id} from competency {competency_id}")
            
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error dissociating KPI question {question_id} from competency {competency_id}: {str(e)}")
            raise
    
    def associate_360_question(self, competency_id: int, question_id: int) -> bool:
        """
        Associate a 360-degree question with a competency.
        
        Args:
            competency_id: ID of the competency
            question_id: ID of the 360-degree question
            
        Returns:
            True if associated, False if either entity not found
            
        Raises:
            SQLAlchemyError: If there's an error creating the association
        """
        try:
            competency = self.get_competency_by_id(competency_id)
            question = self.db.query(Degree360Question).filter(Degree360Question.id == question_id).first()
            
            if not competency or not question:
                return False
            
            # Check if already associated
            if competency not in question.competencies:
                question.competencies.append(competency)
                self.db.commit()
                logger.info(f"Associated 360 question {question_id} with competency {competency_id}")
            
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error associating 360 question {question_id} with competency {competency_id}: {str(e)}")
            raise
    
    def dissociate_360_question(self, competency_id: int, question_id: int) -> bool:
        """
        Dissociate a 360-degree question from a competency.
        
        Args:
            competency_id: ID of the competency
            question_id: ID of the 360-degree question
            
        Returns:
            True if dissociated, False if either entity not found or not associated
            
        Raises:
            SQLAlchemyError: If there's an error removing the association
        """
        try:
            competency = self.get_competency_by_id(competency_id)
            question = self.db.query(Degree360Question).filter(Degree360Question.id == question_id).first()
            
            if not competency or not question:
                return False
            
            # Check if associated
            if competency in question.competencies:
                question.competencies.remove(competency)
                self.db.commit()
                logger.info(f"Dissociated 360 question {question_id} from competency {competency_id}")
            
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error dissociating 360 question {question_id} from competency {competency_id}: {str(e)}")
            raise
    
    def get_performance_by_competency(self, user_id: int, competency_id: int) -> Optional[float]:
        """
        Calculate the average score for a user in a specific competency.
        
        This function looks at both KPI and 360-degree evaluations to calculate
        the average performance for a given competency.
        
        Args:
            user_id: ID of the user
            competency_id: ID of the competency
            
        Returns:
            Average score for the competency or None if no data
        """
        try:
            # Get all questions associated with this competency
            competency = self.get_competency_by_id(competency_id)
            if not competency:
                return None
            
            # Get scores from KPI evaluations
            kpi_scores = []
            for question in competency.kpi_questions:
                # Find answers for this user and question
                answers = self.db.query(KPIQuestion).join(KPIQuestion.answers).filter(
                    KPIQuestion.id == question.id
                ).all()
                kpi_scores.extend([answer.score for answer in answers])
            
            # Get scores from 360-degree evaluations
            degree360_scores = []
            for question in competency.degree360_questions:
                # Find answers for this user and question
                answers = self.db.query(Degree360Question).join(Degree360Question.answers).filter(
                    Degree360Question.id == question.id
                ).all()
                degree360_scores.extend([answer.score for answer in answers])
            
            # Combine all scores
            all_scores = kpi_scores + degree360_scores
            
            if not all_scores:
                return None
            
            # Calculate average
            average_score = sum(all_scores) / len(all_scores)
            logger.info(f"Calculated performance for user {user_id} in competency {competency_id}: {average_score}")
            return average_score
        except Exception as e:
            logger.error(f"Error calculating performance for user {user_id} in competency {competency_id}: {str(e)}")
            return None