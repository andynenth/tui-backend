# application/commands/base.py
"""
Base command pattern infrastructure for application layer.
Commands encapsulate user intentions and can be validated, logged, and executed.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Generic, TypeVar, Optional, Dict, Any
from uuid import uuid4

T = TypeVar('T')


class Command(ABC):
    """
    Base class for all commands.
    
    Commands represent user intentions and contain all data
    needed to perform an action.
    """
    def __init__(self):
        self.command_id: str = str(uuid4())
        self.timestamp: datetime = datetime.utcnow()
        self.metadata: Dict[str, Any] = {}
    
    def with_metadata(self, key: str, value: Any) -> 'Command':
        """Add metadata to the command."""
        self.metadata[key] = value
        return self


@dataclass
class CommandResult(Generic[T]):
    """
    Result of command execution.
    
    Can be either successful with a value, or failed with an error.
    """
    success: bool
    value: Optional[T] = None
    error: Optional[str] = None
    command_id: str = ""
    
    @staticmethod
    def ok(value: T, command_id: str = "") -> 'CommandResult[T]':
        """Create a successful result."""
        return CommandResult(success=True, value=value, command_id=command_id)
    
    @staticmethod
    def fail(error: str, command_id: str = "") -> 'CommandResult[T]':
        """Create a failed result."""
        return CommandResult(success=False, error=error, command_id=command_id)


class CommandHandler(ABC, Generic[T]):
    """
    Base class for command handlers.
    
    Handlers contain the logic to execute commands and return results.
    """
    
    @abstractmethod
    async def handle(self, command: Command) -> CommandResult[T]:
        """
        Execute the command and return the result.
        
        Args:
            command: The command to execute
            
        Returns:
            CommandResult with success/failure and value/error
        """
        pass
    
    @abstractmethod
    def can_handle(self, command: Command) -> bool:
        """
        Check if this handler can handle the given command.
        
        Args:
            command: The command to check
            
        Returns:
            True if this handler can handle the command
        """
        pass


class CommandBus:
    """
    Command bus routes commands to their appropriate handlers.
    
    This provides a centralized way to execute commands and
    can add cross-cutting concerns like logging, validation, etc.
    """
    
    def __init__(self):
        self._handlers: Dict[type, CommandHandler] = {}
    
    def register_handler(self, command_type: type, handler: CommandHandler) -> None:
        """
        Register a handler for a command type.
        
        Args:
            command_type: The type of command to handle
            handler: The handler for that command type
        """
        self._handlers[command_type] = handler
    
    async def execute(self, command: Command) -> CommandResult:
        """
        Execute a command by routing it to the appropriate handler.
        
        Args:
            command: The command to execute
            
        Returns:
            CommandResult from the handler
            
        Raises:
            ValueError: If no handler is registered for the command type
        """
        command_type = type(command)
        
        if command_type not in self._handlers:
            return CommandResult.fail(
                f"No handler registered for command type {command_type.__name__}",
                command.command_id
            )
        
        handler = self._handlers[command_type]
        
        if not handler.can_handle(command):
            return CommandResult.fail(
                f"Handler cannot handle command {command.command_id}",
                command.command_id
            )
        
        try:
            result = await handler.handle(command)
            result.command_id = command.command_id
            return result
        except Exception as e:
            return CommandResult.fail(
                f"Command execution failed: {str(e)}",
                command.command_id
            )


class CommandValidator(ABC):
    """
    Base class for command validators.
    
    Validators check if commands are valid before execution.
    """
    
    @abstractmethod
    def validate(self, command: Command) -> Optional[str]:
        """
        Validate a command.
        
        Args:
            command: The command to validate
            
        Returns:
            None if valid, error message if invalid
        """
        pass


class ValidatingCommandBus(CommandBus):
    """
    Command bus that validates commands before execution.
    """
    
    def __init__(self):
        super().__init__()
        self._validators: Dict[type, list[CommandValidator]] = {}
    
    def register_validator(self, command_type: type, validator: CommandValidator) -> None:
        """
        Register a validator for a command type.
        
        Args:
            command_type: The type of command to validate
            validator: The validator for that command type
        """
        if command_type not in self._validators:
            self._validators[command_type] = []
        self._validators[command_type].append(validator)
    
    async def execute(self, command: Command) -> CommandResult:
        """
        Validate and execute a command.
        
        Args:
            command: The command to execute
            
        Returns:
            CommandResult from the handler or validation error
        """
        # Validate first
        command_type = type(command)
        if command_type in self._validators:
            for validator in self._validators[command_type]:
                error = validator.validate(command)
                if error:
                    return CommandResult.fail(
                        f"Validation failed: {error}",
                        command.command_id
                    )
        
        # Then execute
        return await super().execute(command)