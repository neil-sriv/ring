"""Unit of Work pattern implementation.

This module implements the Unit of Work pattern for managing database transactions
and domain events in the Ring application. It provides an abstract base class
that can be implemented for different database backends.
"""

# ruff: noqa
# pylint: disable=attribute-defined-outside-init
from __future__ import annotations
import abc


class AbstractUnitOfWork(abc.ABC):
    """Abstract base class for the Unit of Work pattern.

    This class defines the interface for managing database transactions and
    collecting domain events. It uses the context manager protocol to ensure
    proper transaction handling.

    Attributes:
        products (repository.AbstractRepository): Repository for accessing domain objects
    """

    products: repository.AbstractRepository

    def __enter__(self) -> AbstractUnitOfWork:
        """Enter the context manager.

        Returns:
            AbstractUnitOfWork: The UnitOfWork instance for use in a with statement
        """
        return self

    def __exit__(self, *args):
        """Exit the context manager, rolling back if necessary.

        Args:
            *args: Exception information if an error occurred during the transaction
        """
        self.rollback()

    def commit(self):
        """Commit the current transaction.

        This method commits all changes made during the current transaction.
        After a successful commit, the transaction is closed and a new one
        is started.
        """
        self._commit()

    def collect_new_events(self):
        """Collect and yield new domain events from products.

        This method iterates through all products that have been accessed
        during the current transaction and yields any domain events that
        have been generated.

        Yields:
            Event: Domain events that occurred during the transaction
        """
        for product in self.products.seen:
            while product.events:
                yield product.events.pop(0)

    @abc.abstractmethod
    def _commit(self):
        """Commit the current transaction.

        This method must be implemented by concrete classes to handle
        the actual database commit operation.

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self):
        """Rollback the current transaction.

        This method must be implemented by concrete classes to handle
        the actual database rollback operation.

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError


DEFAULT_SESSION_FACTORY = sessionmaker(
    bind=create_engine(
        config.get_postgres_uri(),
        isolation_level="REPEATABLE READ",
    )
)


# class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
#     def __init__(self, session_factory=DEFAULT_SESSION_FACTORY):
#         self.session_factory = session_factory

#     def __enter__(self):
#         self.session = self.session_factory()  # type: Session
#         self.products = repository.SqlAlchemyRepository(self.session)
#         return super().__enter__()

#     def __exit__(self, *args):
#         super().__exit__(*args)
#         self.session.close()

#     def _commit(self):
#         self.session.commit()

#     def rollback(self):
#         self.session.rollback()
