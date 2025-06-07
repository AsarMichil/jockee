# models/transition_feedback.py
class TransitionFeedback(Base):
    __tablename__ = "transition_feedback"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    transition_id = Column(UUID, ForeignKey("mix_transitions.id"))
    user_id = Column(UUID, ForeignKey("users.id"))
    
    # Feedback
    rating = Column(Integer)  # 1-5 stars
    worked_well = Column(Boolean)
    feedback_type = Column(String)  # "too_abrupt", "perfect", "energy_mismatch", etc.
    
    # Context
    track_a_genre = Column(String)
    track_b_genre = Column(String)
    transition_strategy = Column(String)
    compatibility_score = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)

# services/learning_service.py
class TransitionLearningService:
    """Learns from user feedback to improve transitions"""
    
    def record_feedback(self, transition_id: str, rating: int, feedback_type: str):
        """Record user feedback on a transition"""
        # Store feedback in database
        
    def get_strategy_performance(self, genre_a: str, genre_b: str) -> Dict[str, float]:
        """Get performance stats for different strategies between genre pairs"""
        # Query feedback data and return success rates
        
    def adjust_transition_parameters(self, base_transition: UniversalTransition) -> UniversalTransition:
        """Adjust transition based on learned preferences"""
        # Use feedback data to modify transition parameters