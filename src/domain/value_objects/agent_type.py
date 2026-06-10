from enum import Enum


class AgentType(str, Enum):
    CUSTOMER_SUPPORT = "customer_support"
    RESUME_SCREENING = "resume_screening"
    SQL = "sql"
    RESEARCH = "research"
    CODING = "coding"
    RAG = "rag"
    CUSTOM = "custom"


class AgentFramework(str, Enum):
    LANGGRAPH = "langgraph"
    LANGCHAIN = "langchain"
    AUTOGEN = "autogen"
    CREWAI = "crewai"
    CUSTOM = "custom"
