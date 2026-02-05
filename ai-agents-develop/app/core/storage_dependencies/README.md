# Storage Dependencies - Dual Async/Sync Repository Pattern

This module provides a clean, type-safe implementation of the repository pattern that supports both **async** and **sync** database operations. The design follows the **Single Responsibility Principle** by providing separate interfaces for async and sync operations, avoiding the complexity of mixed async/sync signatures.

## 🏗️ Architecture Overview

### Core Components

1. **Base Interfaces**: Separate abstract base classes for async and sync repositories
2. **Repository Implementations**: Concrete implementations for each backend (PostgreSQL, SQLite, Redis)
3. **Providers**: Factory classes that create appropriate repositories based on backend type
4. **Storage Dependencies**: Context managers for managing database connections and sessions

### Key Benefits

- ✅ **Clean Separation**: Async and sync code paths are completely separate
- ✅ **Type Safety**: Each path has proper typing without confusing mixed signatures
- ✅ **Minimal Changes**: Existing async code remains unchanged
- ✅ **Consistent API**: Same provider pattern for both sync and async
- ✅ **Performance**: No overhead from async/sync conversion wrappers
- ✅ **Maintainability**: Clear, explicit interfaces that are easy to test and debug

## 📁 File Structure

```
storage_dependencies/
├── repositories/
│   ├── base.py                    # Base async and sync repository interfaces
│   ├── providers.py               # Provider protocols and implementations
│   ├── postgres_repo.py           # PostgreSQL async and sync repositories
│   ├── sqlite_repo.py             # SQLite async and sync repositories
│   └── redis_repo.py              # Redis async and sync repositories
├── storage_dependencies.py        # Async storage dependencies
├── sync_storage_dependencies.py   # Sync storage dependencies
├── __main__.py                    # Async demo script
├── sync_demo.py                   # Sync demo script
├── usage_examples.py              # Comprehensive usage examples
└── README.md                      # This file
```

## 🚀 Quick Start

### Async Usage (Existing Pattern)

```python
from app.core.storage_dependencies.storage_dependencies import get_provider
from app.core.models.models import ActionExecution

async def async_example():
    async with get_provider("postgres") as provider:
        repo = provider.get_repository(ActionExecution)
        action = await repo.create(ActionExecution(...))
        retrieved = await repo.get(action.id)
        await repo.update(action)
        await repo.delete(action.id)
```

### Sync Usage (New Pattern)

```python
from app.core.storage_dependencies.sync_storage_dependencies import get_sync_provider
from app.core.models.models import ActionExecution

def sync_example():
    with get_sync_provider("postgres") as provider:
        repo = provider.get_repository(ActionExecution)
        action = repo.create(ActionExecution(...))
        retrieved = repo.get(action.id)
        repo.update(action)
        repo.delete(action.id)
```

## 🔧 Backend Support

### Supported Backends

| Backend | Async Support | Sync Support | Driver |
|---------|---------------|--------------|---------|
| PostgreSQL | ✅ | ✅ | asyncpg / psycopg2 |
| SQLite | ✅ | ✅ | aiosqlite / sqlite3 |
| Redis | ✅ | ✅ | redis.asyncio / redis |

### Environment Variables

```bash
# PostgreSQL
POSTGRES_DATABASE_URL="postgresql+asyncpg://user:pass@host:port/db"

# SQLite
SQLITE_DATABASE_URL="sqlite+aiosqlite:///./database.db"

# Redis
REDIS_URL="redis://localhost:6379"

# Backend Selection
STORAGE_BACKEND="postgres"  # or "sqlite", "redis"
```

## 📚 API Reference

### Base Repository Interfaces

#### Async Interface (`BaseRepository`)

```python
class BaseRepository(Generic[T], ABC):
    @abstractmethod
    async def get(self, id: Any) -> Optional[T]: ...

    @abstractmethod
    async def create(self, model: T) -> T: ...

    @abstractmethod
    async def update(self, model: T) -> T: ...

    @abstractmethod
    async def delete(self, id: Any) -> bool: ...

    @abstractmethod
    async def list(self) -> List[T]: ...
```

#### Sync Interface (`BaseSyncRepository`)

```python
class BaseSyncRepository(Generic[T], ABC):
    @abstractmethod
    def get(self, id: Any) -> Optional[T]: ...

    @abstractmethod
    def create(self, model: T) -> T: ...

    @abstractmethod
    def update(self, model: T) -> T: ...

    @abstractmethod
    def delete(self, id: Any) -> bool: ...

    @abstractmethod
    def list(self) -> List[T]: ...
```

### Provider Protocols

#### Async Provider (`RepositoryProvider`)

```python
class RepositoryProvider(Protocol):
    def get_repository(self, model_cls: Type[T]) -> BaseRepository[T]: ...
```

#### Sync Provider (`SyncRepositoryProvider`)

```python
class SyncRepositoryProvider(Protocol):
    def get_repository(self, model_cls: Type[T]) -> BaseSyncRepository[T]: ...
```

### Context Managers

#### Async Provider Context Manager

```python
@asynccontextmanager
async def get_provider(backend: str) -> AsyncIterator[RepositoryProvider]:
    # Returns async repository provider
```

#### Sync Provider Context Manager

```python
@contextmanager
def get_sync_provider(backend: str) -> Iterator[SyncRepositoryProvider]:
    # Returns sync repository provider
```

## 🔄 Migration Guide

### From Existing Async Code

Your existing async code will continue to work without any changes:

```python
# This continues to work exactly as before
async with get_provider(backend) as provider:
    repo = provider.get_repository(MyModel)
    result = await repo.create(my_model)
```

### Adding Sync Support

To add sync support to your codebase:

1. **Import sync dependencies**:
   ```python
   from app.core.storage_dependencies.sync_storage_dependencies import get_sync_provider
   ```

2. **Use sync context manager**:
   ```python
   with get_sync_provider(backend) as provider:
       repo = provider.get_repository(MyModel)
       result = repo.create(my_model)  # No await needed
   ```

3. **Update function signatures**:
   ```python
   # Before (async)
   async def my_function():
       async with get_provider(backend) as provider:
           # async operations

   # After (sync)
   def my_function():
       with get_sync_provider(backend) as provider:
           # sync operations
   ```

## 🧪 Testing

### Running Examples

```bash
# Run async demo
python -m app.core.storage_dependencies.__main__

# Run sync demo
python app/core/storage_dependencies/sync_demo.py

# Run comprehensive examples
python app/core/storage_dependencies/usage_examples.py
```

### Testing Both Patterns

```python
import pytest
from app.core.storage_dependencies.storage_dependencies import get_provider
from app.core.storage_dependencies.sync_storage_dependencies import get_sync_provider

@pytest.mark.asyncio
async def test_async_operations():
    async with get_provider("sqlite") as provider:
        repo = provider.get_repository(ActionExecution)
        # Test async operations

def test_sync_operations():
    with get_sync_provider("sqlite") as provider:
        repo = provider.get_repository(ActionExecution)
        # Test sync operations
```

## 🚨 Best Practices

### 1. Choose the Right Pattern

- **Use Async**: For web applications, API endpoints, and I/O-bound operations
- **Use Sync**: For CLI tools, scripts, and CPU-bound operations

### 2. Consistent Usage

- Don't mix async and sync patterns in the same function
- Use the same pattern throughout your application layer
- Consider your application's concurrency model

### 3. Error Handling

```python
# Async error handling
async def async_operation():
    try:
        async with get_provider(backend) as provider:
            repo = provider.get_repository(MyModel)
            return await repo.get(id)
    except Exception as e:
        logger.error(f"Async operation failed: {e}")
        raise

# Sync error handling
def sync_operation():
    try:
        with get_sync_provider(backend) as provider:
            repo = provider.get_repository(MyModel)
            return repo.get(id)
    except Exception as e:
        logger.error(f"Sync operation failed: {e}")
        raise
```

### 4. Performance Considerations

- **Async**: Better for concurrent operations and I/O-bound tasks
- **Sync**: Simpler for sequential operations and CPU-bound tasks
- **Connection Pooling**: Both patterns support connection pooling automatically

## 🔧 Configuration

### FastAPI Integration

```python
from fastapi import Depends
from app.core.storage_dependencies.storage_dependencies import get_repository_provider
from app.core.storage_dependencies.sync_storage_dependencies import get_sync_repository_provider

# Async endpoint
@app.get("/actions/{action_id}")
async def get_action(
    action_id: str,
    provider: RepositoryProvider = Depends(get_repository_provider)
):
    repo = provider.get_repository(ActionExecution)
    return await repo.get(action_id)

# Sync endpoint (if needed)
@app.get("/actions-sync/{action_id}")
def get_action_sync(
    action_id: str,
    provider: SyncRepositoryProvider = Depends(get_sync_repository_provider)
):
    repo = provider.get_repository(ActionExecution)
    return repo.get(action_id)
```

### Custom Configuration

```python
# Custom engine configuration
@lru_cache
def get_custom_postgres_engine(url: str):
    return create_async_engine(
        url,
        pool_size=20,
        max_overflow=30,
        pool_pre_ping=True,
        json_serializer=custom_json_serializer
    )
```

## 🤝 Contributing

When adding new backends or features:

1. **Implement both async and sync versions**
2. **Follow the existing naming conventions**
3. **Add comprehensive tests**
4. **Update this documentation**

### Adding a New Backend

1. Create repository implementations:
   ```python
   class NewBackendRepository(BaseRepository[T]):
       # Async implementation

   class SyncNewBackendRepository(BaseSyncRepository[T]):
       # Sync implementation
   ```

2. Update providers:
   ```python
   class NewBackendProvider:
       def get_repository(self, model_cls: Type[T]) -> NewBackendRepository[T]:
           return NewBackendRepository(...)

   class SyncNewBackendProvider:
       def get_repository(self, model_cls: Type[T]) -> SyncNewBackendRepository[T]:
           return SyncNewBackendRepository(...)
   ```

3. Update storage dependencies with new backend support

## 📄 License

This implementation follows the same license as the parent project.
