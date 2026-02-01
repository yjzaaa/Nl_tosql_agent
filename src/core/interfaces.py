"""Core Interfaces Module

Provides interfaces for core components.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class ILLMProvider(ABC):
    """Interface for LLM providers"""

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text from LLM

        Args:
            prompt: Input prompt
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            Generated text
        """
        pass

    @abstractmethod
    def generate_chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        Generate chat completion

        Args:
            messages: List of message dictionaries (role, content)
            **kwargs: Additional parameters

        Returns:
            Generated response
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """
        Get model name

        Returns:
            Model name string
        """
        pass


class IDataSourceStrategy(ABC):
    """Interface for data source strategies"""

    @abstractmethod
    def load_data(self, **kwargs) -> Any:
        """
        Load data from data source

        Returns:
            Loaded data
        """
        pass

    @abstractmethod
    def execute_query(self, query: str, **kwargs) -> Any:
        """
        Execute a query

        Args:
            query: Query string
            **kwargs: Additional parameters

        Returns:
            Query result
        """
        pass

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get data source metadata

        Returns:
            Metadata dictionary
        """
        pass

    @abstractmethod
    def get_context(self) -> Dict[str, Any]:
        """
        Get data source context

        Returns:
            Context dictionary
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if data source is available

        Returns:
            Availability status
        """
        pass


class IAgent(ABC):
    """Interface for agents"""

    @abstractmethod
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process state and return updated state

        Args:
            state: Current agent state

        Returns:
            Updated state
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """
        Get agent name

        Returns:
            Agent name string
        """
        pass


class IWorkflow(ABC):
    """Interface for workflows"""

    @abstractmethod
    def execute(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute workflow with initial state

        Args:
            initial_state: Initial workflow state

        Returns:
            Final workflow state
        """
        pass

    @abstractmethod
    def get_graph(self) -> Any:
        """
        Get workflow graph

        Returns:
            Compiled workflow graph
        """
        pass


class ISkill(ABC):
    """Interface for skills"""

    @abstractmethod
    def get_name(self) -> str:
        """Get skill name"""
        pass

    @abstractmethod
    def get_version(self) -> str:
        """Get skill version"""
        pass

    @abstractmethod
    def get_description(self) -> str:
        """Get skill description"""
        pass

    @abstractmethod
    def get_prompt(self) -> str:
        """Get skill prompt template"""
        pass

    @abstractmethod
    def get_business_rules(self) -> List[str]:
        """Get business rules"""
        pass

    @abstractmethod
    def get_sql_templates(self) -> List[str]:
        """Get SQL templates"""
        pass


class ITool(ABC):
    """Interface for tools"""

    @abstractmethod
    def invoke(self, parameters: Dict[str, Any]) -> Any:
        """
        Invoke tool with parameters

        Args:
            parameters: Tool parameters

        Returns:
            Tool result
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get tool name"""
        pass

    @abstractmethod
    def get_description(self) -> str:
        """Get tool description"""
        pass

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """Get tool parameter schema"""
        pass
