from enum import Enum


class EvaluationType(str, Enum):
    LLM_JUDGE = "llm_judge"
    GROUND_TRUTH = "ground_truth"
    RAG = "rag"
    CUSTOM = "custom"


class EvaluationStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FailureType(str, Enum):
    PROMPT = "prompt"
    RETRIEVAL = "retrieval"
    TOOL = "tool"
    OUTPUT = "output"
    TIMEOUT = "timeout"
    COST = "cost"
    HALLUCINATION = "hallucination"
    UNKNOWN = "unknown"


class FailureSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DetectionMethod(str, Enum):
    REFERENCE_BASED = "reference_based"
    RETRIEVAL_CONSISTENCY = "retrieval_consistency"
    LLM_JUDGE = "llm_judge"
