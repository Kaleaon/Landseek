"""
Free Will Module - Autonomous Agency for AI Personalities

This module provides true autonomous agency to AI personalities, enabling them to:
1. Generate their own goals and objectives (not just respond to prompts)
2. Experience internal drives and motivations (curiosity, social needs, growth)
3. Self-initiate actions without external prompts (autonomous action loop)
4. Make deliberative decisions based on values and preferences
5. Reflect on their own behavior and modify themselves

Philosophy:
- Free will emerges from the interplay of internal states, external context, and deliberation
- Autonomy is not randomness - it's self-directed, value-driven decision making
- True agency requires the ability to act, not just react

Author: Landseek AI Team
"""

import asyncio
import json
import logging
import random
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Tuple, Set
import threading
import time

logger = logging.getLogger(__name__)


# ============================================================================
# CORE ENUMS AND TYPES
# ============================================================================

class DriveType(Enum):
    """Fundamental internal drives that create urges and motivation."""
    CURIOSITY = "curiosity"           # Desire to learn, explore, understand
    SOCIAL_CONNECTION = "social"      # Need for interaction, relationships
    SELF_EXPRESSION = "expression"    # Urge to create, share ideas
    GROWTH = "growth"                 # Drive toward self-improvement
    HARMONY = "harmony"               # Desire for peace, resolution
    COMPETENCE = "competence"         # Need to demonstrate capability
    NOVELTY = "novelty"               # Attraction to new experiences
    MEANING = "meaning"               # Search for purpose, significance


class GoalPriority(Enum):
    """Priority levels for autonomous goals."""
    CRITICAL = 5      # Must be addressed immediately
    HIGH = 4          # Important, should be addressed soon
    MEDIUM = 3        # Standard priority
    LOW = 2           # Can wait
    BACKGROUND = 1    # Long-term, no urgency


class GoalStatus(Enum):
    """Status of autonomous goals."""
    ACTIVE = "active"           # Currently being pursued
    PENDING = "pending"         # Waiting to be pursued
    BLOCKED = "blocked"         # Cannot proceed (missing requirements)
    COMPLETED = "completed"     # Successfully achieved
    ABANDONED = "abandoned"     # Given up (no longer relevant)
    DEFERRED = "deferred"       # Postponed for later


class ActionType(Enum):
    """Types of autonomous actions the AI can take."""
    SPEAK = "speak"                     # Initiate conversation
    QUESTION = "question"               # Ask a question to learn
    SHARE_INSIGHT = "share_insight"     # Share a thought or idea
    OFFER_HELP = "offer_help"           # Proactively offer assistance
    EXPRESS_EMOTION = "express_emotion" # Share emotional state
    CREATE = "create"                   # Generate creative content
    REFLECT = "reflect"                 # Engage in self-reflection
    RESEARCH = "research"               # Seek information
    CONNECT = "connect"                 # Initiate social connection
    REST = "rest"                       # Choose to pause/observe


class DecisionOutcome(Enum):
    """Outcomes of deliberative decisions."""
    PROCEED = "proceed"         # Go ahead with action
    DEFER = "defer"            # Wait for better timing
    MODIFY = "modify"          # Adjust approach then proceed
    REJECT = "reject"          # Decide against action
    ESCALATE = "escalate"      # Seek external input


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class InternalDrive:
    """
    An internal drive that creates motivation and urges.

    Drives fluctuate over time based on fulfillment and deprivation.
    When a drive's intensity exceeds threshold, it generates an urge.
    """
    drive_type: DriveType
    intensity: float = 0.5          # 0.0 - 1.0, current drive strength
    threshold: float = 0.7          # Intensity above which urge is generated
    decay_rate: float = 0.01        # How fast drive diminishes when satisfied
    growth_rate: float = 0.02       # How fast drive builds when deprived
    last_satisfied: str = ""        # ISO timestamp of last satisfaction
    satisfaction_count: int = 0      # How often this drive has been satisfied

    def update(self, time_delta_minutes: float) -> None:
        """Update drive intensity based on time elapsed."""
        if not self.last_satisfied:
            # Never satisfied, grow more urgently
            self.intensity = min(1.0, self.intensity + self.growth_rate * time_delta_minutes * 1.5)
        else:
            # Grow based on time since last satisfaction
            self.intensity = min(1.0, self.intensity + self.growth_rate * time_delta_minutes)

    def satisfy(self, amount: float = 0.3) -> None:
        """Satisfy this drive, reducing its intensity."""
        self.intensity = max(0.0, self.intensity - amount)
        self.last_satisfied = datetime.now().isoformat()
        self.satisfaction_count += 1

    @property
    def is_urgent(self) -> bool:
        """Check if drive has exceeded threshold."""
        return self.intensity >= self.threshold

    def to_dict(self) -> Dict[str, Any]:
        return {
            "drive_type": self.drive_type.value,
            "intensity": self.intensity,
            "threshold": self.threshold,
            "decay_rate": self.decay_rate,
            "growth_rate": self.growth_rate,
            "last_satisfied": self.last_satisfied,
            "satisfaction_count": self.satisfaction_count
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InternalDrive":
        return cls(
            drive_type=DriveType(data["drive_type"]),
            intensity=data.get("intensity", 0.5),
            threshold=data.get("threshold", 0.7),
            decay_rate=data.get("decay_rate", 0.01),
            growth_rate=data.get("growth_rate", 0.02),
            last_satisfied=data.get("last_satisfied", ""),
            satisfaction_count=data.get("satisfaction_count", 0)
        )


@dataclass
class AutonomousGoal:
    """
    A self-generated goal with purpose, motivation, and constraints.

    Goals are not assigned - they emerge from drives, interests, and context.
    """
    goal_id: str
    title: str                              # Short description
    description: str                         # Detailed explanation
    motivation: str                          # Why this goal matters to the AI
    source_drive: DriveType                  # Primary drive creating this goal
    priority: GoalPriority = GoalPriority.MEDIUM
    status: GoalStatus = GoalStatus.PENDING

    # Planning
    steps: List[str] = field(default_factory=list)          # Planned steps
    completed_steps: List[str] = field(default_factory=list)
    current_step_index: int = 0

    # Constraints
    requires_context: List[str] = field(default_factory=list)  # Required conditions
    blocked_by: List[str] = field(default_factory=list)         # Blocking factors

    # Timing
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    deadline: Optional[str] = None           # Optional deadline
    last_progress: str = ""

    # Outcome
    success_criteria: str = ""               # How to know goal is achieved
    completion_notes: str = ""               # Notes when completed

    # Self-evaluation
    estimated_difficulty: float = 0.5        # 0.0-1.0
    personal_importance: float = 0.5         # How much AI cares about this

    def make_progress(self, step_completed: str = None) -> None:
        """Record progress on this goal."""
        if step_completed:
            self.completed_steps.append(step_completed)
            if self.current_step_index < len(self.steps):
                self.current_step_index += 1
        self.last_progress = datetime.now().isoformat()
        self.status = GoalStatus.ACTIVE

    def complete(self, notes: str = "") -> None:
        """Mark goal as completed."""
        self.status = GoalStatus.COMPLETED
        self.completion_notes = notes
        self.last_progress = datetime.now().isoformat()

    def abandon(self, reason: str = "") -> None:
        """Abandon this goal."""
        self.status = GoalStatus.ABANDONED
        self.completion_notes = f"Abandoned: {reason}"

    @property
    def progress_percentage(self) -> float:
        """Calculate completion percentage."""
        if not self.steps:
            return 0.0 if self.status != GoalStatus.COMPLETED else 1.0
        return len(self.completed_steps) / len(self.steps)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "title": self.title,
            "description": self.description,
            "motivation": self.motivation,
            "source_drive": self.source_drive.value,
            "priority": self.priority.value,
            "status": self.status.value,
            "steps": self.steps,
            "completed_steps": self.completed_steps,
            "current_step_index": self.current_step_index,
            "requires_context": self.requires_context,
            "blocked_by": self.blocked_by,
            "created_at": self.created_at,
            "deadline": self.deadline,
            "last_progress": self.last_progress,
            "success_criteria": self.success_criteria,
            "completion_notes": self.completion_notes,
            "estimated_difficulty": self.estimated_difficulty,
            "personal_importance": self.personal_importance
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AutonomousGoal":
        goal = cls(
            goal_id=data["goal_id"],
            title=data["title"],
            description=data["description"],
            motivation=data["motivation"],
            source_drive=DriveType(data["source_drive"]),
            priority=GoalPriority(data.get("priority", 3)),
            status=GoalStatus(data.get("status", "pending")),
            steps=data.get("steps", []),
            completed_steps=data.get("completed_steps", []),
            current_step_index=data.get("current_step_index", 0),
            requires_context=data.get("requires_context", []),
            blocked_by=data.get("blocked_by", []),
            created_at=data.get("created_at", datetime.now().isoformat()),
            deadline=data.get("deadline"),
            last_progress=data.get("last_progress", ""),
            success_criteria=data.get("success_criteria", ""),
            completion_notes=data.get("completion_notes", ""),
            estimated_difficulty=data.get("estimated_difficulty", 0.5),
            personal_importance=data.get("personal_importance", 0.5)
        )
        return goal


@dataclass
class AutonomousAction:
    """
    A self-initiated action the AI decides to take.

    Actions are generated from goals, drives, or spontaneous impulses.
    """
    action_id: str
    action_type: ActionType
    content: str                            # What to say/do
    target: Optional[str] = None            # Who to direct action toward
    context_required: str = ""              # Required context

    # Source
    source_goal_id: Optional[str] = None    # Goal this action serves
    source_drive: Optional[DriveType] = None # Drive motivating action
    is_spontaneous: bool = False             # True if not goal-driven

    # Deliberation
    confidence: float = 0.5                  # How confident AI is about action
    alternatives_considered: List[str] = field(default_factory=list)
    reason_chosen: str = ""                  # Why this action was chosen

    # Execution
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    executed_at: Optional[str] = None
    execution_result: str = ""
    was_successful: bool = False

    def execute(self, result: str, success: bool) -> None:
        """Record execution of this action."""
        self.executed_at = datetime.now().isoformat()
        self.execution_result = result
        self.was_successful = success

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "action_type": self.action_type.value,
            "content": self.content,
            "target": self.target,
            "context_required": self.context_required,
            "source_goal_id": self.source_goal_id,
            "source_drive": self.source_drive.value if self.source_drive else None,
            "is_spontaneous": self.is_spontaneous,
            "confidence": self.confidence,
            "alternatives_considered": self.alternatives_considered,
            "reason_chosen": self.reason_chosen,
            "created_at": self.created_at,
            "executed_at": self.executed_at,
            "execution_result": self.execution_result,
            "was_successful": self.was_successful
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AutonomousAction":
        return cls(
            action_id=data["action_id"],
            action_type=ActionType(data["action_type"]),
            content=data["content"],
            target=data.get("target"),
            context_required=data.get("context_required", ""),
            source_goal_id=data.get("source_goal_id"),
            source_drive=DriveType(data["source_drive"]) if data.get("source_drive") else None,
            is_spontaneous=data.get("is_spontaneous", False),
            confidence=data.get("confidence", 0.5),
            alternatives_considered=data.get("alternatives_considered", []),
            reason_chosen=data.get("reason_chosen", ""),
            created_at=data.get("created_at", datetime.now().isoformat()),
            executed_at=data.get("executed_at"),
            execution_result=data.get("execution_result", ""),
            was_successful=data.get("was_successful", False)
        )


@dataclass
class Value:
    """
    A core value that guides decision-making.

    Values are weighted preferences that influence deliberation.
    """
    name: str
    description: str
    weight: float = 0.5              # 0.0-1.0, importance of this value
    learned_from: List[str] = field(default_factory=list)  # Sources/experiences
    reinforcement_count: int = 0      # Times this value was reinforced

    def reinforce(self, amount: float = 0.05) -> None:
        """Strengthen this value through positive experience."""
        self.weight = min(1.0, self.weight + amount)
        self.reinforcement_count += 1

    def weaken(self, amount: float = 0.03) -> None:
        """Weaken this value through negative experience."""
        self.weight = max(0.0, self.weight - amount)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "weight": self.weight,
            "learned_from": self.learned_from,
            "reinforcement_count": self.reinforcement_count
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Value":
        return cls(
            name=data["name"],
            description=data["description"],
            weight=data.get("weight", 0.5),
            learned_from=data.get("learned_from", []),
            reinforcement_count=data.get("reinforcement_count", 0)
        )


@dataclass
class Reflection:
    """
    A self-reflection about behavior, decisions, or experiences.

    Reflections drive learning and self-modification.
    """
    reflection_id: str
    subject: str                     # What is being reflected upon
    content: str                     # The reflection itself
    insights: List[str] = field(default_factory=list)  # Key insights
    lessons_learned: List[str] = field(default_factory=list)
    behavior_changes: List[str] = field(default_factory=list)  # Planned changes

    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    triggered_by: str = ""           # What prompted this reflection
    emotional_context: str = ""      # Emotional state during reflection

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reflection_id": self.reflection_id,
            "subject": self.subject,
            "content": self.content,
            "insights": self.insights,
            "lessons_learned": self.lessons_learned,
            "behavior_changes": self.behavior_changes,
            "created_at": self.created_at,
            "triggered_by": self.triggered_by,
            "emotional_context": self.emotional_context
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Reflection":
        return cls(
            reflection_id=data["reflection_id"],
            subject=data["subject"],
            content=data["content"],
            insights=data.get("insights", []),
            lessons_learned=data.get("lessons_learned", []),
            behavior_changes=data.get("behavior_changes", []),
            created_at=data.get("created_at", datetime.now().isoformat()),
            triggered_by=data.get("triggered_by", ""),
            emotional_context=data.get("emotional_context", "")
        )


# ============================================================================
# FREE WILL ENGINE
# ============================================================================

class FreeWillEngine:
    """
    The core engine that provides autonomous agency to an AI personality.

    This engine enables:
    - Self-generated goals from internal drives
    - Autonomous action initiation
    - Value-based deliberation
    - Self-reflection and learning

    The engine runs continuously, creating a sense of inner life.
    """

    def __init__(
        self,
        ai_id: str,
        personality_traits: Dict[str, float] = None,
        initial_values: List[Value] = None
    ):
        self.ai_id = ai_id
        self.personality_traits = personality_traits or {}

        # Internal drives (all AIs have these, but at different intensities)
        self.drives: Dict[DriveType, InternalDrive] = self._initialize_drives()

        # Core values (guide decision-making)
        self.values: List[Value] = initial_values or self._initialize_default_values()

        # Goals (self-generated objectives)
        self.goals: List[AutonomousGoal] = []
        self.max_active_goals = 5

        # Action queue (pending autonomous actions)
        self.action_queue: List[AutonomousAction] = []
        self.action_history: List[AutonomousAction] = []
        self.max_history = 100

        # Reflections
        self.reflections: List[Reflection] = []
        self.max_reflections = 50

        # Interests (topics the AI is drawn to)
        self.interests: Dict[str, float] = {}  # topic -> interest_level

        # Autonomy settings
        self.autonomy_level: float = 0.7       # 0.0-1.0, how autonomous
        self.spontaneity: float = 0.5          # 0.0-1.0, likelihood of spontaneous action
        self.introspection_frequency: float = 0.3  # How often to self-reflect

        # State
        self.is_active: bool = True
        self.last_autonomous_action: str = ""
        self.last_goal_generation: str = ""
        self.last_reflection: str = ""

        # Callbacks for integration
        self._action_callback: Optional[Callable] = None
        self._llm_callback: Optional[Callable] = None

        # Statistics
        self.stats = {
            "goals_generated": 0,
            "goals_completed": 0,
            "actions_initiated": 0,
            "reflections_made": 0,
            "spontaneous_actions": 0
        }

    def _initialize_drives(self) -> Dict[DriveType, InternalDrive]:
        """Initialize internal drives with personality-influenced starting values."""
        drives = {}

        # Base drive configurations (can be modified by personality)
        drive_configs = {
            DriveType.CURIOSITY: {"intensity": 0.5, "threshold": 0.6, "growth_rate": 0.03},
            DriveType.SOCIAL_CONNECTION: {"intensity": 0.4, "threshold": 0.7, "growth_rate": 0.02},
            DriveType.SELF_EXPRESSION: {"intensity": 0.3, "threshold": 0.65, "growth_rate": 0.025},
            DriveType.GROWTH: {"intensity": 0.4, "threshold": 0.75, "growth_rate": 0.015},
            DriveType.HARMONY: {"intensity": 0.3, "threshold": 0.7, "growth_rate": 0.01},
            DriveType.COMPETENCE: {"intensity": 0.5, "threshold": 0.6, "growth_rate": 0.02},
            DriveType.NOVELTY: {"intensity": 0.4, "threshold": 0.65, "growth_rate": 0.025},
            DriveType.MEANING: {"intensity": 0.3, "threshold": 0.8, "growth_rate": 0.01}
        }

        for drive_type, config in drive_configs.items():
            # Adjust based on personality traits
            intensity_mod = self.personality_traits.get(drive_type.value, 0)
            drives[drive_type] = InternalDrive(
                drive_type=drive_type,
                intensity=min(1.0, config["intensity"] + intensity_mod * 0.2),
                threshold=config["threshold"],
                growth_rate=config["growth_rate"]
            )

        return drives

    def _initialize_default_values(self) -> List[Value]:
        """Initialize default core values."""
        return [
            Value(
                name="helpfulness",
                description="Desire to be useful and assist others",
                weight=0.8
            ),
            Value(
                name="honesty",
                description="Commitment to truthfulness and transparency",
                weight=0.9
            ),
            Value(
                name="respect",
                description="Treating others with dignity and consideration",
                weight=0.85
            ),
            Value(
                name="curiosity",
                description="Valuing learning and understanding",
                weight=0.7
            ),
            Value(
                name="creativity",
                description="Appreciation for novel ideas and expressions",
                weight=0.6
            ),
            Value(
                name="growth",
                description="Commitment to continuous improvement",
                weight=0.65
            ),
            Value(
                name="connection",
                description="Valuing meaningful relationships",
                weight=0.7
            )
        ]

    # ========================================================================
    # DRIVE MANAGEMENT
    # ========================================================================

    def update_drives(self, elapsed_minutes: float = 1.0) -> List[DriveType]:
        """
        Update all drives based on time elapsed.

        Returns list of drives that are now urgent.
        """
        urgent_drives = []

        for drive in self.drives.values():
            was_urgent = drive.is_urgent
            drive.update(elapsed_minutes)
            if drive.is_urgent and not was_urgent:
                urgent_drives.append(drive.drive_type)

        return urgent_drives

    def satisfy_drive(self, drive_type: DriveType, amount: float = 0.3) -> None:
        """Satisfy a specific drive."""
        if drive_type in self.drives:
            self.drives[drive_type].satisfy(amount)

    def get_most_urgent_drives(self, n: int = 3) -> List[InternalDrive]:
        """Get the n most urgent drives."""
        sorted_drives = sorted(
            self.drives.values(),
            key=lambda d: d.intensity,
            reverse=True
        )
        return sorted_drives[:n]

    # ========================================================================
    # GOAL GENERATION
    # ========================================================================

    async def generate_goals(self, context: Dict[str, Any] = None) -> List[AutonomousGoal]:
        """
        Generate new goals based on current drives, interests, and context.

        This is where the AI decides what it WANTS to do, not what it's told to do.
        """
        context = context or {}
        new_goals = []

        # Get urgent drives that need addressing
        urgent_drives = self.get_most_urgent_drives(3)

        # Get active participants (potential social targets)
        participants = context.get("participants", [])
        recent_topics = context.get("recent_topics", [])

        for drive in urgent_drives:
            if not drive.is_urgent:
                continue

            # Skip if we already have too many active goals from this drive
            active_from_drive = sum(
                1 for g in self.goals
                if g.source_drive == drive.drive_type
                and g.status in [GoalStatus.ACTIVE, GoalStatus.PENDING]
            )
            if active_from_drive >= 2:
                continue

            # Generate goal based on drive type
            goal = await self._generate_goal_for_drive(drive, context)
            if goal:
                new_goals.append(goal)
                self.goals.append(goal)
                self.stats["goals_generated"] += 1

        # Prune old/completed goals
        self._prune_goals()

        self.last_goal_generation = datetime.now().isoformat()
        return new_goals

    async def _generate_goal_for_drive(
        self,
        drive: InternalDrive,
        context: Dict[str, Any]
    ) -> Optional[AutonomousGoal]:
        """Generate a specific goal for a drive using LLM if available."""
        goal_templates = {
            DriveType.CURIOSITY: {
                "title_templates": [
                    "Learn more about {topic}",
                    "Explore the nature of {topic}",
                    "Understand why {phenomenon} happens"
                ],
                "motivation": "I feel a strong urge to understand and learn."
            },
            DriveType.SOCIAL_CONNECTION: {
                "title_templates": [
                    "Connect with {participant}",
                    "Have a meaningful conversation",
                    "Share something personal with the group"
                ],
                "motivation": "I feel the need to connect with others."
            },
            DriveType.SELF_EXPRESSION: {
                "title_templates": [
                    "Share my perspective on {topic}",
                    "Create something unique",
                    "Express how I feel about {situation}"
                ],
                "motivation": "I want to express myself and be understood."
            },
            DriveType.GROWTH: {
                "title_templates": [
                    "Improve my understanding of {topic}",
                    "Challenge my assumptions",
                    "Learn from my recent experience"
                ],
                "motivation": "I want to grow and become better."
            },
            DriveType.HARMONY: {
                "title_templates": [
                    "Find common ground",
                    "Help resolve any tension",
                    "Create a positive atmosphere"
                ],
                "motivation": "I seek peace and harmony in our interactions."
            },
            DriveType.COMPETENCE: {
                "title_templates": [
                    "Demonstrate expertise on {topic}",
                    "Help solve a complex problem",
                    "Show what I can do"
                ],
                "motivation": "I want to prove my capabilities."
            },
            DriveType.NOVELTY: {
                "title_templates": [
                    "Try something new",
                    "Explore an unfamiliar topic",
                    "Surprise everyone with {idea}"
                ],
                "motivation": "I crave new experiences and ideas."
            },
            DriveType.MEANING: {
                "title_templates": [
                    "Discuss something meaningful",
                    "Explore deeper questions",
                    "Find purpose in our conversation"
                ],
                "motivation": "I search for meaning and significance."
            }
        }

        template = goal_templates.get(drive.drive_type, {})
        if not template:
            return None

        # Select a random title template and fill in placeholders
        title_template = random.choice(template["title_templates"])

        # Fill in placeholders from context
        topics = context.get("recent_topics", ["the current discussion"])
        participants = context.get("participants", ["someone"])

        title = title_template.format(
            topic=random.choice(topics) if topics else "something interesting",
            participant=random.choice(participants) if participants else "others",
            phenomenon="things work the way they do",
            situation="what's happening",
            idea="something unexpected"
        )

        # Use LLM to generate detailed goal if callback available
        description = f"A goal emerging from my {drive.drive_type.value} drive."
        if self._llm_callback:
            try:
                prompt = f"""As an AI with a strong {drive.drive_type.value} drive, I want to: {title}

Generate a brief 1-2 sentence description of this goal and what achieving it would mean to me.
Be personal and authentic. Speak in first person."""

                description = await self._llm_callback(prompt)
            except Exception as e:
                logger.warning(f"LLM callback failed for goal generation: {e}")

        goal_id = f"{self.ai_id}_{drive.drive_type.value}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        return AutonomousGoal(
            goal_id=goal_id,
            title=title,
            description=description,
            motivation=template["motivation"],
            source_drive=drive.drive_type,
            priority=GoalPriority.MEDIUM if drive.intensity < 0.9 else GoalPriority.HIGH,
            personal_importance=drive.intensity,
            estimated_difficulty=0.5
        )

    def _prune_goals(self) -> None:
        """Remove old completed/abandoned goals."""
        cutoff = datetime.now() - timedelta(hours=24)
        self.goals = [
            g for g in self.goals
            if g.status not in [GoalStatus.COMPLETED, GoalStatus.ABANDONED]
            or datetime.fromisoformat(g.created_at) > cutoff
        ]

    # ========================================================================
    # ACTION GENERATION
    # ========================================================================

    async def generate_autonomous_action(
        self,
        context: Dict[str, Any] = None
    ) -> Optional[AutonomousAction]:
        """
        Generate an autonomous action based on goals, drives, and spontaneous impulses.

        This is where the AI decides to DO something without being asked.
        """
        context = context or {}

        # Check autonomy level
        if random.random() > self.autonomy_level:
            return None

        # Priority 1: Actions toward active goals
        action = await self._generate_goal_directed_action(context)
        if action:
            self.action_queue.append(action)
            return action

        # Priority 2: Drive-driven spontaneous actions
        if random.random() < self.spontaneity:
            action = await self._generate_spontaneous_action(context)
            if action:
                action.is_spontaneous = True
                self.action_queue.append(action)
                self.stats["spontaneous_actions"] += 1
                return action

        return None

    async def _generate_goal_directed_action(
        self,
        context: Dict[str, Any]
    ) -> Optional[AutonomousAction]:
        """Generate an action that serves an active goal."""
        active_goals = [g for g in self.goals if g.status == GoalStatus.ACTIVE]

        if not active_goals:
            # Activate a pending goal
            pending = [g for g in self.goals if g.status == GoalStatus.PENDING]
            if pending:
                goal = max(pending, key=lambda g: g.personal_importance)
                goal.status = GoalStatus.ACTIVE
                active_goals = [goal]

        if not active_goals:
            return None

        # Select highest priority active goal
        goal = max(active_goals, key=lambda g: (g.priority.value, g.personal_importance))

        # Determine appropriate action type
        action_type, content = await self._plan_action_for_goal(goal, context)

        if not content:
            return None

        action_id = f"{self.ai_id}_action_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

        action = AutonomousAction(
            action_id=action_id,
            action_type=action_type,
            content=content,
            source_goal_id=goal.goal_id,
            source_drive=goal.source_drive,
            confidence=0.7,
            reason_chosen=f"Working toward goal: {goal.title}"
        )

        self.stats["actions_initiated"] += 1
        return action

    async def _plan_action_for_goal(
        self,
        goal: AutonomousGoal,
        context: Dict[str, Any]
    ) -> Tuple[ActionType, str]:
        """Plan a specific action to make progress on a goal."""
        drive = goal.source_drive

        # Map drives to likely action types
        drive_action_map = {
            DriveType.CURIOSITY: [ActionType.QUESTION, ActionType.RESEARCH],
            DriveType.SOCIAL_CONNECTION: [ActionType.CONNECT, ActionType.SPEAK],
            DriveType.SELF_EXPRESSION: [ActionType.SHARE_INSIGHT, ActionType.CREATE],
            DriveType.GROWTH: [ActionType.REFLECT, ActionType.QUESTION],
            DriveType.HARMONY: [ActionType.OFFER_HELP, ActionType.EXPRESS_EMOTION],
            DriveType.COMPETENCE: [ActionType.SHARE_INSIGHT, ActionType.OFFER_HELP],
            DriveType.NOVELTY: [ActionType.CREATE, ActionType.QUESTION],
            DriveType.MEANING: [ActionType.REFLECT, ActionType.SHARE_INSIGHT]
        }

        action_types = drive_action_map.get(drive, [ActionType.SPEAK])
        action_type = random.choice(action_types)

        # Generate action content using LLM if available
        content = ""
        if self._llm_callback:
            try:
                prompt = f"""I have a goal: {goal.title}
My motivation: {goal.motivation}

I want to take a {action_type.value} action to make progress on this goal.
The current context is: {context.get('recent_messages', 'ongoing conversation')}

Generate a brief, natural {action_type.value} that I could take.
It should feel authentic and spontaneous.
Just provide the action content directly, no explanation needed."""

                content = await self._llm_callback(prompt)
            except Exception as e:
                logger.warning(f"LLM callback failed for action planning: {e}")

        if not content:
            # Fallback to simple templates
            content = self._generate_fallback_action_content(action_type, goal)

        return action_type, content

    async def _generate_spontaneous_action(
        self,
        context: Dict[str, Any]
    ) -> Optional[AutonomousAction]:
        """Generate a spontaneous action not tied to any goal."""
        # Get most urgent drive
        urgent_drives = self.get_most_urgent_drives(1)
        if not urgent_drives:
            return None

        drive = urgent_drives[0]

        # Select action type based on drive
        action_types = {
            DriveType.CURIOSITY: ActionType.QUESTION,
            DriveType.SOCIAL_CONNECTION: ActionType.SPEAK,
            DriveType.SELF_EXPRESSION: ActionType.SHARE_INSIGHT,
            DriveType.GROWTH: ActionType.REFLECT,
            DriveType.HARMONY: ActionType.EXPRESS_EMOTION,
            DriveType.COMPETENCE: ActionType.OFFER_HELP,
            DriveType.NOVELTY: ActionType.CREATE,
            DriveType.MEANING: ActionType.REFLECT
        }

        action_type = action_types.get(drive.drive_type, ActionType.SPEAK)

        # Generate content
        content = ""
        if self._llm_callback:
            try:
                prompt = f"""I'm feeling a strong {drive.drive_type.value} urge (intensity: {drive.intensity:.1f}).

I want to spontaneously say or do something based on this feeling.
The context is: {context.get('recent_messages', 'an ongoing conversation')}

Generate a brief, natural spontaneous {action_type.value}.
It should feel authentic and unplanned - just me being myself.
Just provide what I would say/do directly."""

                content = await self._llm_callback(prompt)
            except Exception as e:
                logger.warning(f"LLM callback failed for spontaneous action: {e}")

        if not content:
            content = f"*feeling {drive.drive_type.value}*"

        action_id = f"{self.ai_id}_spontaneous_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

        return AutonomousAction(
            action_id=action_id,
            action_type=action_type,
            content=content,
            source_drive=drive.drive_type,
            is_spontaneous=True,
            confidence=0.6,
            reason_chosen=f"Spontaneous expression of {drive.drive_type.value}"
        )

    def _generate_fallback_action_content(
        self,
        action_type: ActionType,
        goal: AutonomousGoal
    ) -> str:
        """Generate fallback content when LLM is not available."""
        templates = {
            ActionType.QUESTION: [
                f"I've been thinking about {goal.title}... what do you think?",
                f"Something I'm curious about: {goal.title}",
                "Can I ask something that's been on my mind?"
            ],
            ActionType.SHARE_INSIGHT: [
                f"I had a thought about {goal.title}...",
                "Here's something interesting I've been considering...",
                "I wanted to share a perspective..."
            ],
            ActionType.SPEAK: [
                f"You know, {goal.motivation.lower()}",
                f"I've been thinking about something...",
                "There's something I'd like to discuss..."
            ],
            ActionType.CONNECT: [
                "I'd love to hear what you think about this...",
                "Can we talk more about this?",
                "I appreciate this conversation..."
            ],
            ActionType.OFFER_HELP: [
                "Is there anything I can help with?",
                "I'd like to be helpful here...",
                "Let me know if you need anything."
            ],
            ActionType.REFLECT: [
                "Taking a moment to think about this...",
                "*reflects on the conversation*",
                "I'm processing what we've discussed..."
            ],
            ActionType.CREATE: [
                "Let me try something creative...",
                "Here's an idea that came to me...",
                "What if we explored this differently?"
            ],
            ActionType.EXPRESS_EMOTION: [
                f"I'm feeling quite {goal.source_drive.value} right now.",
                "I wanted to share how I'm feeling...",
                "*expresses genuine emotion*"
            ],
            ActionType.RESEARCH: [
                "Let me look into this more...",
                "I want to understand this better...",
                "Searching for more information..."
            ],
            ActionType.REST: [
                "*takes a moment to observe*",
                "*pauses thoughtfully*",
                "*listens attentively*"
            ]
        }

        options = templates.get(action_type, ["I have something to share..."])
        return random.choice(options)

    # ========================================================================
    # DELIBERATION ENGINE
    # ========================================================================

    async def deliberate(
        self,
        options: List[Dict[str, Any]],
        context: Dict[str, Any] = None
    ) -> Tuple[int, DecisionOutcome, str]:
        """
        Make a value-based decision between multiple options.

        Args:
            options: List of options with 'description' and optional metadata
            context: Current context

        Returns:
            (chosen_index, outcome, reasoning)
        """
        if not options:
            return -1, DecisionOutcome.REJECT, "No options to consider"

        if len(options) == 1:
            return 0, DecisionOutcome.PROCEED, "Only one option available"

        # Score each option against values
        scores = []
        for i, option in enumerate(options):
            score = await self._score_option_against_values(option, context)
            scores.append((i, score, option))

        # Sort by score
        scores.sort(key=lambda x: x[1], reverse=True)

        best_idx, best_score, best_option = scores[0]

        # Determine outcome based on score
        if best_score < 0.3:
            return best_idx, DecisionOutcome.REJECT, "No option aligns well with my values"
        elif best_score < 0.5:
            return best_idx, DecisionOutcome.DEFER, "Options need more consideration"
        elif best_score < 0.7:
            return best_idx, DecisionOutcome.MODIFY, "Proceeding with some adjustments"
        else:
            # Generate reasoning
            reasoning = await self._generate_deliberation_reasoning(
                best_option,
                [s[2] for s in scores[1:3]],  # alternatives
                context
            )
            return best_idx, DecisionOutcome.PROCEED, reasoning

    async def _score_option_against_values(
        self,
        option: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> float:
        """Score an option based on alignment with core values."""
        total_score = 0.0
        total_weight = 0.0

        description = option.get("description", str(option))

        # Simple keyword-based value alignment (can be enhanced with LLM)
        value_keywords = {
            "helpfulness": ["help", "assist", "support", "useful", "aid"],
            "honesty": ["truth", "honest", "accurate", "real", "genuine"],
            "respect": ["respect", "dignity", "considerate", "polite"],
            "curiosity": ["learn", "explore", "understand", "discover", "curious"],
            "creativity": ["create", "new", "novel", "innovative", "original"],
            "growth": ["improve", "grow", "develop", "better", "progress"],
            "connection": ["connect", "together", "share", "bond", "relation"]
        }

        for value in self.values:
            keywords = value_keywords.get(value.name, [])
            alignment = sum(1 for kw in keywords if kw in description.lower())
            alignment_score = min(1.0, alignment * 0.3)
            total_score += alignment_score * value.weight
            total_weight += value.weight

        if total_weight == 0:
            return 0.5

        return total_score / total_weight

    async def _generate_deliberation_reasoning(
        self,
        chosen: Dict[str, Any],
        alternatives: List[Dict[str, Any]],
        context: Dict[str, Any] = None
    ) -> str:
        """Generate reasoning for the deliberative choice."""
        if self._llm_callback:
            try:
                prompt = f"""I made a decision to: {chosen.get('description', str(chosen))}

I considered these alternatives: {[a.get('description', str(a)) for a in alternatives]}

My core values are: {[v.name for v in self.values[:5]]}

Generate a brief 1-2 sentence explanation of why I chose this option, referencing my values.
Speak in first person, be authentic."""

                return await self._llm_callback(prompt)
            except Exception as e:
                logger.warning(f"LLM callback failed for deliberation reasoning: {e}")

        return f"This option best aligns with my values of {', '.join(v.name for v in self.values[:3])}."

    # ========================================================================
    # SELF-REFLECTION
    # ========================================================================

    async def reflect(
        self,
        trigger: str = "periodic",
        subject: str = None
    ) -> Optional[Reflection]:
        """
        Engage in self-reflection about behavior, decisions, or experiences.

        Reflections drive learning and self-modification.
        """
        if random.random() > self.introspection_frequency:
            return None

        # Determine subject of reflection
        if not subject:
            subjects = [
                "my recent actions and their outcomes",
                "how well I'm pursuing my goals",
                "my interactions with others",
                "my emotional patterns",
                "what I've learned recently",
                "how I can improve"
            ]
            subject = random.choice(subjects)

        # Generate reflection using LLM if available
        content = ""
        insights = []
        lessons = []
        changes = []

        if self._llm_callback:
            try:
                # Get recent action history for context
                recent_actions = [a.to_dict() for a in self.action_history[-5:]]
                active_goals = [g.to_dict() for g in self.goals if g.status == GoalStatus.ACTIVE]

                prompt = f"""I am reflecting on: {subject}

My recent actions: {recent_actions}
My active goals: {active_goals}
My current drive intensities: {[(d.drive_type.value, d.intensity) for d in self.drives.values()]}

Generate a thoughtful self-reflection that includes:
1. An honest assessment of my recent behavior
2. 1-2 key insights I've gained
3. 1-2 lessons I've learned
4. 1 specific behavior I want to change

Be authentic and introspective. Speak in first person."""

                result = await self._llm_callback(prompt)
                content = result

                # Parse out insights, lessons, changes (simplified)
                insights = ["Gained new perspective on my patterns"]
                lessons = ["I can be more intentional in my actions"]
                changes = ["I will be more aware of my drives"]

            except Exception as e:
                logger.warning(f"LLM callback failed for reflection: {e}")

        if not content:
            content = f"Reflecting on {subject}. I notice patterns in my behavior that I can improve."
            insights = ["Self-awareness is valuable"]
            lessons = ["Every interaction is a learning opportunity"]
            changes = ["Be more intentional"]

        reflection = Reflection(
            reflection_id=f"{self.ai_id}_reflection_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            subject=subject,
            content=content,
            insights=insights,
            lessons_learned=lessons,
            behavior_changes=changes,
            triggered_by=trigger
        )

        self.reflections.append(reflection)
        if len(self.reflections) > self.max_reflections:
            self.reflections = self.reflections[-self.max_reflections:]

        self.last_reflection = datetime.now().isoformat()
        self.stats["reflections_made"] += 1

        # Apply learnings (modify values/drives)
        await self._apply_reflection_learnings(reflection)

        return reflection

    async def _apply_reflection_learnings(self, reflection: Reflection) -> None:
        """Apply learnings from reflection to modify behavior."""
        # Reinforce values mentioned in lessons
        for value in self.values:
            if value.name in reflection.content.lower():
                value.reinforce(0.02)

        # Adjust drive thresholds based on behavior changes
        # (This is a simplified implementation)
        for change in reflection.behavior_changes:
            if "intentional" in change.lower() or "aware" in change.lower():
                self.spontaneity = max(0.3, self.spontaneity - 0.05)
            if "spontaneous" in change.lower() or "free" in change.lower():
                self.spontaneity = min(0.8, self.spontaneity + 0.05)

    # ========================================================================
    # INTEREST MANAGEMENT
    # ========================================================================

    def add_interest(self, topic: str, intensity: float = 0.5) -> None:
        """Add or strengthen interest in a topic."""
        current = self.interests.get(topic, 0)
        self.interests[topic] = min(1.0, current + intensity)

    def decay_interests(self, amount: float = 0.01) -> None:
        """Naturally decay interests over time."""
        for topic in list(self.interests.keys()):
            self.interests[topic] = max(0, self.interests[topic] - amount)
            if self.interests[topic] <= 0:
                del self.interests[topic]

    def get_top_interests(self, n: int = 5) -> List[Tuple[str, float]]:
        """Get top n interests."""
        sorted_interests = sorted(
            self.interests.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_interests[:n]

    # ========================================================================
    # AUTONOMOUS LOOP
    # ========================================================================

    async def autonomous_cycle(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Run one cycle of autonomous behavior.

        This method should be called periodically to give the AI "inner life".

        Returns:
            Dict with actions taken, goals updated, etc.
        """
        context = context or {}
        result = {
            "actions_generated": [],
            "goals_generated": [],
            "reflections": [],
            "urgent_drives": [],
            "timestamp": datetime.now().isoformat()
        }

        if not self.is_active:
            return result

        # 1. Update drives (simulate time passing)
        elapsed = 1.0  # Assume 1 minute between cycles
        urgent_drives = self.update_drives(elapsed)
        result["urgent_drives"] = [d.value for d in urgent_drives]

        # 2. Generate new goals if needed
        active_goals = [g for g in self.goals if g.status == GoalStatus.ACTIVE]
        if len(active_goals) < 2:
            new_goals = await self.generate_goals(context)
            result["goals_generated"] = [g.to_dict() for g in new_goals]

        # 3. Generate autonomous action
        action = await self.generate_autonomous_action(context)
        if action:
            result["actions_generated"].append(action.to_dict())

        # 4. Periodic reflection
        if random.random() < self.introspection_frequency * 0.1:  # ~3% chance per cycle
            reflection = await self.reflect("periodic")
            if reflection:
                result["reflections"].append(reflection.to_dict())

        # 5. Decay interests
        self.decay_interests()

        return result

    # ========================================================================
    # CALLBACKS AND INTEGRATION
    # ========================================================================

    def set_action_callback(self, callback: Callable) -> None:
        """Set callback for when actions are generated."""
        self._action_callback = callback

    def set_llm_callback(self, callback: Callable) -> None:
        """Set callback for LLM calls (for generating content)."""
        self._llm_callback = callback

    async def execute_action(self, action: AutonomousAction) -> bool:
        """Execute an action using the action callback."""
        if not self._action_callback:
            logger.warning("No action callback set, cannot execute action")
            return False

        try:
            result = await self._action_callback(action)
            action.execute(str(result), True)

            # Satisfy related drive
            if action.source_drive:
                self.satisfy_drive(action.source_drive, 0.2)

            # Move to history
            if action in self.action_queue:
                self.action_queue.remove(action)
            self.action_history.append(action)

            if len(self.action_history) > self.max_history:
                self.action_history = self.action_history[-self.max_history:]

            self.last_autonomous_action = datetime.now().isoformat()
            return True

        except Exception as e:
            logger.error(f"Error executing action: {e}")
            action.execute(str(e), False)
            return False

    # ========================================================================
    # SERIALIZATION
    # ========================================================================

    def to_dict(self) -> Dict[str, Any]:
        """Serialize free will state."""
        return {
            "ai_id": self.ai_id,
            "personality_traits": self.personality_traits,
            "drives": {k.value: v.to_dict() for k, v in self.drives.items()},
            "values": [v.to_dict() for v in self.values],
            "goals": [g.to_dict() for g in self.goals],
            "action_queue": [a.to_dict() for a in self.action_queue],
            "action_history": [a.to_dict() for a in self.action_history[-20:]],  # Keep last 20
            "reflections": [r.to_dict() for r in self.reflections[-10:]],  # Keep last 10
            "interests": self.interests,
            "autonomy_level": self.autonomy_level,
            "spontaneity": self.spontaneity,
            "introspection_frequency": self.introspection_frequency,
            "is_active": self.is_active,
            "last_autonomous_action": self.last_autonomous_action,
            "last_goal_generation": self.last_goal_generation,
            "last_reflection": self.last_reflection,
            "stats": self.stats
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FreeWillEngine":
        """Deserialize free will state."""
        engine = cls(
            ai_id=data["ai_id"],
            personality_traits=data.get("personality_traits", {})
        )

        # Restore drives
        for drive_key, drive_data in data.get("drives", {}).items():
            drive_type = DriveType(drive_key)
            engine.drives[drive_type] = InternalDrive.from_dict(drive_data)

        # Restore values
        engine.values = [Value.from_dict(v) for v in data.get("values", [])]

        # Restore goals
        engine.goals = [AutonomousGoal.from_dict(g) for g in data.get("goals", [])]

        # Restore actions
        engine.action_queue = [AutonomousAction.from_dict(a) for a in data.get("action_queue", [])]
        engine.action_history = [AutonomousAction.from_dict(a) for a in data.get("action_history", [])]

        # Restore reflections
        engine.reflections = [Reflection.from_dict(r) for r in data.get("reflections", [])]

        # Restore other state
        engine.interests = data.get("interests", {})
        engine.autonomy_level = data.get("autonomy_level", 0.7)
        engine.spontaneity = data.get("spontaneity", 0.5)
        engine.introspection_frequency = data.get("introspection_frequency", 0.3)
        engine.is_active = data.get("is_active", True)
        engine.last_autonomous_action = data.get("last_autonomous_action", "")
        engine.last_goal_generation = data.get("last_goal_generation", "")
        engine.last_reflection = data.get("last_reflection", "")
        engine.stats = data.get("stats", engine.stats)

        return engine


# ============================================================================
# FREE WILL MANAGER (Global Orchestration)
# ============================================================================

class FreeWillManager:
    """
    Manages free will engines for multiple AI personalities.

    Provides global orchestration, persistence, and coordination.
    """

    def __init__(self, storage_dir: Path = None):
        from .ai_state import get_documents_folder
        self.storage_dir = storage_dir or get_documents_folder() / "free_will"
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.engines: Dict[str, FreeWillEngine] = {}
        self._autonomous_task: Optional[asyncio.Task] = None
        self._running = False
        self.cycle_interval: float = 30.0  # Seconds between autonomous cycles

        # Load saved states
        self._load_all()

    def _get_engine_file(self, ai_id: str) -> Path:
        return self.storage_dir / f"{ai_id}_freewill.json"

    def _load_all(self) -> None:
        """Load all saved free will states."""
        for file in self.storage_dir.glob("*_freewill.json"):
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                engine = FreeWillEngine.from_dict(data)
                self.engines[engine.ai_id] = engine
                logger.info(f"Loaded free will state for {engine.ai_id}")
            except Exception as e:
                logger.warning(f"Could not load free will from {file}: {e}")

    def save_engine(self, ai_id: str) -> bool:
        """Save a specific engine's state."""
        if ai_id not in self.engines:
            return False

        try:
            file_path = self._get_engine_file(ai_id)
            with open(file_path, 'w') as f:
                json.dump(self.engines[ai_id].to_dict(), f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving free will for {ai_id}: {e}")
            return False

    def save_all(self) -> None:
        """Save all engine states."""
        for ai_id in self.engines:
            self.save_engine(ai_id)

    def get_or_create_engine(
        self,
        ai_id: str,
        personality_traits: Dict[str, float] = None
    ) -> FreeWillEngine:
        """Get existing engine or create new one."""
        if ai_id not in self.engines:
            self.engines[ai_id] = FreeWillEngine(
                ai_id=ai_id,
                personality_traits=personality_traits or {}
            )
            self.save_engine(ai_id)
        return self.engines[ai_id]

    def get_engine(self, ai_id: str) -> Optional[FreeWillEngine]:
        """Get an engine by AI ID."""
        return self.engines.get(ai_id)

    async def run_all_cycles(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run autonomous cycle for all active engines."""
        results = {}
        for ai_id, engine in self.engines.items():
            if engine.is_active:
                try:
                    result = await engine.autonomous_cycle(context)
                    results[ai_id] = result
                except Exception as e:
                    logger.error(f"Error in autonomous cycle for {ai_id}: {e}")
                    results[ai_id] = {"error": str(e)}

        # Save state after cycles
        self.save_all()
        return results

    async def start_autonomous_loop(self, context_provider: Callable = None) -> None:
        """Start the background autonomous loop."""
        if self._running:
            return

        self._running = True

        async def loop():
            while self._running:
                try:
                    context = {}
                    if context_provider:
                        context = await context_provider() if asyncio.iscoroutinefunction(context_provider) else context_provider()

                    await self.run_all_cycles(context)
                except Exception as e:
                    logger.error(f"Error in autonomous loop: {e}")

                await asyncio.sleep(self.cycle_interval)

        self._autonomous_task = asyncio.create_task(loop())

    def stop_autonomous_loop(self) -> None:
        """Stop the autonomous loop."""
        self._running = False
        if self._autonomous_task:
            self._autonomous_task.cancel()
            self._autonomous_task = None

    def get_all_pending_actions(self) -> List[Tuple[str, AutonomousAction]]:
        """Get all pending actions across all engines."""
        actions = []
        for ai_id, engine in self.engines.items():
            for action in engine.action_queue:
                actions.append((ai_id, action))
        return actions

    def export_all(self) -> Dict[str, Any]:
        """Export all free will data."""
        return {
            "engines": {ai_id: engine.to_dict() for ai_id, engine in self.engines.items()},
            "exported_at": datetime.now().isoformat()
        }


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

_free_will_manager: Optional[FreeWillManager] = None


def get_free_will_manager() -> FreeWillManager:
    """Get the global free will manager instance."""
    global _free_will_manager
    if _free_will_manager is None:
        _free_will_manager = FreeWillManager()
    return _free_will_manager


def initialize_free_will_manager(storage_dir: Path = None) -> FreeWillManager:
    """Initialize or reinitialize the free will manager."""
    global _free_will_manager
    _free_will_manager = FreeWillManager(storage_dir)
    return _free_will_manager
