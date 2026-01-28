from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from datetime import datetime, timedelta
import json
from pathlib import Path


class ScoreCategory(str, Enum):
    """Categories for agent scoring."""
    CORRECTNESS = "correctness"     # Did output meet requirements?
    EFFICIENCY = "efficiency"       # Resource usage, speed
    COMPLIANCE = "compliance"       # Followed contracts, standards
    COST = "cost"                   # Token/API costs
    STABILITY = "stability"         # Consistency over time


@dataclass
class ScoreEntry:
    """A single score entry for an agent."""
    category: ScoreCategory
    score: float  # 0.0 to 100.0
    timestamp: datetime = field(default_factory=datetime.now)
    task_id: Optional[str] = None
    notes: str = ""
    
    def to_dict(self) -> dict:
        return {
            "category": self.category.value,
            "score": self.score,
            "timestamp": self.timestamp.isoformat(),
            "task_id": self.task_id,
            "notes": self.notes
        }


@dataclass
class AgentScorecard:
    """Scorecard tracking an agent's performance."""
    agent_name: str
    scores: dict[str, list[ScoreEntry]] = field(default_factory=dict)
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    escalations: int = 0
    autonomy_level: float = 1.0  # 0.0=no autonomy, 1.0=full
    
    def add_score(self, category: ScoreCategory, score: float, task_id: str = None, notes: str = "") -> None:
        """Add a score entry."""
        if category.value not in self.scores:
            self.scores[category.value] = []
        
        self.scores[category.value].append(ScoreEntry(
            category=category,
            score=score,
            task_id=task_id,
            notes=notes
        ))
    
    def get_average(self, category: ScoreCategory, days: int = 30) -> float:
        """Get average score for a category over recent days."""
        if category.value not in self.scores:
            return 50.0  # Default neutral score
        
        cutoff = datetime.now() - timedelta(days=days)
        recent = [s for s in self.scores[category.value] if s.timestamp > cutoff]
        
        if not recent:
            return 50.0
        
        return sum(s.score for s in recent) / len(recent)
    
    def get_overall_score(self) -> float:
        """Get weighted overall score."""
        weights = {
            ScoreCategory.CORRECTNESS: 0.35,
            ScoreCategory.EFFICIENCY: 0.15,
            ScoreCategory.COMPLIANCE: 0.25,
            ScoreCategory.COST: 0.10,
            ScoreCategory.STABILITY: 0.15
        }
        
        total = 0.0
        total_weight = 0.0
        
        for category, weight in weights.items():
            avg = self.get_average(category)
            total += avg * weight
            total_weight += weight
        
        return total / total_weight if total_weight > 0 else 50.0
    
    def get_success_rate(self) -> float:
        """Get task success rate."""
        if self.total_tasks == 0:
            return 1.0
        return self.successful_tasks / self.total_tasks
    
    def record_success(self) -> None:
        """Record a successful task."""
        self.total_tasks += 1
        self.successful_tasks += 1
    
    def record_failure(self) -> None:
        """Record a failed task."""
        self.total_tasks += 1
        self.failed_tasks += 1
    
    def record_escalation(self) -> None:
        """Record an escalation."""
        self.escalations += 1
    
    def adjust_autonomy(self) -> None:
        """Adjust autonomy based on performance."""
        overall = self.get_overall_score()
        success_rate = self.get_success_rate()
        
        # High performers get more autonomy
        if overall >= 80 and success_rate >= 0.9:
            self.autonomy_level = min(1.0, self.autonomy_level + 0.1)
        # Poor performers lose autonomy
        elif overall < 50 or success_rate < 0.7:
            self.autonomy_level = max(0.2, self.autonomy_level - 0.2)
    
    def to_dict(self) -> dict:
        return {
            "agent_name": self.agent_name,
            "overall_score": self.get_overall_score(),
            "success_rate": self.get_success_rate(),
            "total_tasks": self.total_tasks,
            "successful_tasks": self.successful_tasks,
            "failed_tasks": self.failed_tasks,
            "escalations": self.escalations,
            "autonomy_level": self.autonomy_level,
            "category_scores": {
                cat.value: self.get_average(cat)
                for cat in ScoreCategory
            }
        }


class EvaluationSystem:
    """
    System for evaluating and tracking agent performance.
    
    Features:
    - Multi-dimensional scoring
    - Performance history
    - Autonomy adjustment
    - Contract strictness adjustment
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path(".macds/evaluation")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._scorecards: dict[str, AgentScorecard] = {}
        self._load()
    
    def _load(self) -> None:
        """Load scorecards from disk."""
        scores_file = self.storage_path / "scorecards.json"
        if scores_file.exists():
            try:
                with open(scores_file) as f:
                    data = json.load(f)
                    for name, card_data in data.get("scorecards", {}).items():
                        self._scorecards[name] = AgentScorecard(
                            agent_name=name,
                            total_tasks=card_data.get("total_tasks", 0),
                            successful_tasks=card_data.get("successful_tasks", 0),
                            failed_tasks=card_data.get("failed_tasks", 0),
                            escalations=card_data.get("escalations", 0),
                            autonomy_level=card_data.get("autonomy_level", 1.0)
                        )
            except Exception:
                pass
    
    def _save(self) -> None:
        """Save scorecards to disk."""
        scores_file = self.storage_path / "scorecards.json"
        data = {
            "version": "1.0",
            "saved_at": datetime.now().isoformat(),
            "scorecards": {
                name: card.to_dict()
                for name, card in self._scorecards.items()
            }
        }
        with open(scores_file, "w") as f:
            json.dump(data, f, indent=2)
    
    def get_scorecard(self, agent_name: str) -> AgentScorecard:
        """Get or create scorecard for an agent."""
        if agent_name not in self._scorecards:
            self._scorecards[agent_name] = AgentScorecard(agent_name=agent_name)
        return self._scorecards[agent_name]
    
    def record_task_result(
        self,
        agent_name: str,
        success: bool,
        scores: dict[ScoreCategory, float],
        task_id: Optional[str] = None
    ) -> None:
        """Record the result of a task execution."""
        scorecard = self.get_scorecard(agent_name)
        
        if success:
            scorecard.record_success()
        else:
            scorecard.record_failure()
        
        for category, score in scores.items():
            scorecard.add_score(category, score, task_id)
        
        scorecard.adjust_autonomy()
        self._save()
    
    def record_build_result(
        self,
        agent_name: str,
        build_success: bool,
        test_coverage: float,
        test_passed: int,
        test_failed: int
    ) -> None:
        """Record build/test results."""
        scorecard = self.get_scorecard(agent_name)
        
        # Calculate scores from build results
        correctness = 100.0 if build_success else 0.0
        if test_passed + test_failed > 0:
            correctness = (correctness + (test_passed / (test_passed + test_failed)) * 100) / 2
        
        scorecard.add_score(ScoreCategory.CORRECTNESS, correctness)
        
        # Coverage contributes to compliance
        if test_coverage >= 0:
            scorecard.add_score(ScoreCategory.COMPLIANCE, min(100, test_coverage))
        
        if build_success and test_failed == 0:
            scorecard.record_success()
        else:
            scorecard.record_failure()
        
        scorecard.adjust_autonomy()
        self._save()
    
    def record_review_result(
        self,
        reviewer_name: str,
        reviewed_agent: str,
        violations: int,
        severity_score: float
    ) -> None:
        """Record code review results."""
        # Score the implementation agent
        impl_scorecard = self.get_scorecard(reviewed_agent)
        compliance_score = max(0, 100 - (violations * 10) - severity_score)
        impl_scorecard.add_score(ScoreCategory.COMPLIANCE, compliance_score)
        
        # Score the reviewer for doing their job
        reviewer_scorecard = self.get_scorecard(reviewer_name)
        reviewer_scorecard.add_score(ScoreCategory.CORRECTNESS, 100.0)  # Completed review
        
        self._save()
    
    def get_recommendations(self, agent_name: str) -> list[str]:
        """Get improvement recommendations for an agent."""
        scorecard = self.get_scorecard(agent_name)
        recommendations = []
        
        for category in ScoreCategory:
            avg = scorecard.get_average(category)
            if avg < 60:
                recommendations.append(
                    f"Improve {category.value}: Current average {avg:.1f}%"
                )
        
        if scorecard.get_success_rate() < 0.8:
            recommendations.append(
                f"Low success rate ({scorecard.get_success_rate():.0%}): Consider additional validation"
            )
        
        if scorecard.escalations > 5:
            recommendations.append(
                f"High escalation count ({scorecard.escalations}): Review authority scope"
            )
        
        return recommendations
    
    def get_all_scores(self) -> dict[str, dict]:
        """Get all agent scorecards."""
        return {
            name: card.to_dict()
            for name, card in self._scorecards.items()
        }
    
    def get_leaderboard(self) -> list[tuple[str, float]]:
        """Get agents ranked by overall score."""
        scores = [
            (name, card.get_overall_score())
            for name, card in self._scorecards.items()
        ]
        return sorted(scores, key=lambda x: x[1], reverse=True)


# ==================== Execution Feedback Integration ====================

@dataclass
class ExecutionFeedback:
    """Feedback from code execution."""
    build_success: bool
    test_success: bool
    test_passed: int = 0
    test_failed: int = 0
    test_skipped: int = 0
    coverage_percent: float = 0.0
    execution_time_ms: int = 0
    memory_usage_mb: float = 0.0
    security_issues: list[dict] = field(default_factory=list)
    performance_metrics: dict = field(default_factory=dict)
    
    def to_scores(self) -> dict[ScoreCategory, float]:
        """Convert execution feedback to scores."""
        scores = {}
        
        # Correctness from tests
        total_tests = self.test_passed + self.test_failed
        if total_tests > 0:
            scores[ScoreCategory.CORRECTNESS] = (self.test_passed / total_tests) * 100
        elif self.build_success:
            scores[ScoreCategory.CORRECTNESS] = 70.0
        else:
            scores[ScoreCategory.CORRECTNESS] = 0.0
        
        # Compliance from coverage and security
        compliance = self.coverage_percent
        if self.security_issues:
            compliance -= len(self.security_issues) * 10
        scores[ScoreCategory.COMPLIANCE] = max(0, min(100, compliance))
        
        # Efficiency from execution time (subjective baseline)
        if self.execution_time_ms < 5000:
            scores[ScoreCategory.EFFICIENCY] = 90.0
        elif self.execution_time_ms < 30000:
            scores[ScoreCategory.EFFICIENCY] = 70.0
        else:
            scores[ScoreCategory.EFFICIENCY] = 50.0
        
        return scores


class FeedbackProcessor:
    """Processes execution feedback and updates evaluations."""
    
    def __init__(self, evaluation_system: EvaluationSystem):
        self.evaluation = evaluation_system
    
    def process_feedback(
        self,
        agent_name: str,
        feedback: ExecutionFeedback,
        task_id: Optional[str] = None
    ) -> dict:
        """Process feedback and update scores."""
        scores = feedback.to_scores()
        success = feedback.build_success and feedback.test_success
        
        self.evaluation.record_task_result(
            agent_name=agent_name,
            success=success,
            scores=scores,
            task_id=task_id
        )
        
        return {
            "agent": agent_name,
            "success": success,
            "scores": {k.value: v for k, v in scores.items()},
            "recommendations": self.evaluation.get_recommendations(agent_name)
        }
