class DomainException(Exception):
    """Base class for all domain exceptions."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class AgentNotFoundError(DomainException):
    def __init__(self, agent_id: str) -> None:
        super().__init__(f"Agent '{agent_id}' not found")
        self.agent_id = agent_id


class AgentRunNotFoundError(DomainException):
    def __init__(self, run_id: str) -> None:
        super().__init__(f"AgentRun '{run_id}' not found")
        self.run_id = run_id


class InvalidAgentStateError(DomainException):
    def __init__(self, agent_id: str, current: str, attempted: str) -> None:
        super().__init__(
            f"Agent '{agent_id}': cannot transition from '{current}' to '{attempted}'"
        )


class InvalidRunTransitionError(DomainException):
    def __init__(self, run_id: str, current: str, attempted: str) -> None:
        super().__init__(
            f"Run '{run_id}': cannot transition from '{current}' to '{attempted}'"
        )


class DuplicateAgentError(DomainException):
    def __init__(self, name: str) -> None:
        super().__init__(f"Agent with name '{name}' already exists")
        self.name = name
