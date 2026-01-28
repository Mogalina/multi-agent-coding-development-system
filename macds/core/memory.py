"""
Memory System for MACDS.

Implements structured memory with decay for agents.
Memory scopes: Working, Project, Skill, Failure
"""

from dataclasses import dataclass, field
from typing import Any, Optional
from enum import Enum
from datetime import datetime, timedelta
import json
from pathlib import Path
import hashlib


class MemoryScope(str, Enum):
    """Memory scope types with different decay rates."""
    WORKING = "working"      # Current task, fast decay
    PROJECT = "project"      # This project, slow decay
    SKILL = "skill"          # Learned patterns, very slow decay
    FAILURE = "failure"      # Past mistakes, medium decay


class DecayPolicy(str, Enum):
    """Decay policy for memory entries."""
    FAST = "fast"           # 1 hour half-life
    MEDIUM = "medium"       # 24 hour half-life
    SLOW = "slow"           # 7 day half-life
    VERY_SLOW = "very_slow" # 30 day half-life
    PERMANENT = "permanent" # Never decays


# Decay half-life in seconds
DECAY_RATES = {
    DecayPolicy.FAST: 3600,          # 1 hour
    DecayPolicy.MEDIUM: 86400,       # 24 hours
    DecayPolicy.SLOW: 604800,        # 7 days
    DecayPolicy.VERY_SLOW: 2592000,  # 30 days
    DecayPolicy.PERMANENT: float('inf')
}

# Default decay policy per scope
SCOPE_DECAY_DEFAULTS = {
    MemoryScope.WORKING: DecayPolicy.FAST,
    MemoryScope.PROJECT: DecayPolicy.SLOW,
    MemoryScope.SKILL: DecayPolicy.VERY_SLOW,
    MemoryScope.FAILURE: DecayPolicy.MEDIUM
}


@dataclass
class MemoryEntry:
    """A single memory entry with metadata."""
    id: str
    content: Any
    scope: MemoryScope
    source: str  # Agent or system that created this
    confidence: float = 1.0  # 0.0 to 1.0
    decay_policy: DecayPolicy = DecayPolicy.MEDIUM
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    tags: list[str] = field(default_factory=list)
    related_entries: list[str] = field(default_factory=list)
    
    def get_current_strength(self) -> float:
        """Calculate current memory strength based on decay."""
        if self.decay_policy == DecayPolicy.PERMANENT:
            return self.confidence
        
        elapsed = (datetime.now() - self.last_accessed).total_seconds()
        half_life = DECAY_RATES[self.decay_policy]
        decay_factor = 0.5 ** (elapsed / half_life)
        
        # Boost from access count (max 2x)
        access_boost = min(2.0, 1.0 + (self.access_count * 0.1))
        
        return min(1.0, self.confidence * decay_factor * access_boost)
    
    def access(self) -> None:
        """Record an access to this memory."""
        self.last_accessed = datetime.now()
        self.access_count += 1
    
    def is_expired(self, threshold: float = 0.1) -> bool:
        """Check if memory has decayed below threshold."""
        return self.get_current_strength() < threshold
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "scope": self.scope.value,
            "source": self.source,
            "confidence": self.confidence,
            "decay_policy": self.decay_policy.value,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "access_count": self.access_count,
            "tags": self.tags,
            "related_entries": self.related_entries,
            "current_strength": self.get_current_strength()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "MemoryEntry":
        return cls(
            id=data["id"],
            content=data["content"],
            scope=MemoryScope(data["scope"]),
            source=data["source"],
            confidence=data.get("confidence", 1.0),
            decay_policy=DecayPolicy(data.get("decay_policy", "medium")),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_accessed=datetime.fromisoformat(data["last_accessed"]),
            access_count=data.get("access_count", 0),
            tags=data.get("tags", []),
            related_entries=data.get("related_entries", [])
        )


class MemoryStore:
    """
    Persistent memory store for agents.
    
    Supports:
    - Scoped memory (working, project, skill, failure)
    - Decay over time
    - Semantic search (basic)
    - Persistence to disk
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path(".macds/memory")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._entries: dict[str, MemoryEntry] = {}
        self._load()
    
    def _generate_id(self, content: Any) -> str:
        """Generate unique ID for content."""
        content_str = json.dumps(content, sort_keys=True, default=str)
        return hashlib.sha256(content_str.encode()).hexdigest()[:16]
    
    def _load(self) -> None:
        """Load memories from disk."""
        memory_file = self.storage_path / "memories.json"
        if memory_file.exists():
            try:
                with open(memory_file) as f:
                    data = json.load(f)
                    for entry_data in data.get("entries", []):
                        entry = MemoryEntry.from_dict(entry_data)
                        if not entry.is_expired():
                            self._entries[entry.id] = entry
            except Exception:
                pass  # Start fresh if load fails
    
    def _save(self) -> None:
        """Persist memories to disk."""
        memory_file = self.storage_path / "memories.json"
        data = {
            "version": "1.0",
            "saved_at": datetime.now().isoformat(),
            "entries": [e.to_dict() for e in self._entries.values()]
        }
        with open(memory_file, "w") as f:
            json.dump(data, f, indent=2)
    
    def store(
        self,
        content: Any,
        scope: MemoryScope,
        source: str,
        confidence: float = 1.0,
        decay_policy: Optional[DecayPolicy] = None,
        tags: Optional[list[str]] = None
    ) -> str:
        """
        Store a new memory entry.
        
        Returns the entry ID.
        """
        entry_id = self._generate_id(content)
        
        # Use default decay policy for scope if not specified
        if decay_policy is None:
            decay_policy = SCOPE_DECAY_DEFAULTS.get(scope, DecayPolicy.MEDIUM)
        
        entry = MemoryEntry(
            id=entry_id,
            content=content,
            scope=scope,
            source=source,
            confidence=confidence,
            decay_policy=decay_policy,
            tags=tags or []
        )
        
        self._entries[entry_id] = entry
        self._save()
        return entry_id
    
    def retrieve(
        self,
        entry_id: Optional[str] = None,
        scope: Optional[MemoryScope] = None,
        source: Optional[str] = None,
        tags: Optional[list[str]] = None,
        min_strength: float = 0.1,
        limit: int = 100
    ) -> list[MemoryEntry]:
        """
        Retrieve memory entries matching criteria.
        
        Results are sorted by strength (descending).
        """
        results = []
        
        for entry in self._entries.values():
            # Filter by ID
            if entry_id and entry.id != entry_id:
                continue
            
            # Filter by scope
            if scope and entry.scope != scope:
                continue
            
            # Filter by source
            if source and entry.source != source:
                continue
            
            # Filter by tags
            if tags and not any(t in entry.tags for t in tags):
                continue
            
            # Filter by strength
            if entry.get_current_strength() < min_strength:
                continue
            
            # Record access
            entry.access()
            results.append(entry)
        
        # Sort by strength
        results.sort(key=lambda e: e.get_current_strength(), reverse=True)
        
        self._save()  # Save access updates
        return results[:limit]
    
    def search(
        self,
        query: str,
        scope: Optional[MemoryScope] = None,
        limit: int = 10
    ) -> list[MemoryEntry]:
        """
        Search memories by content (basic substring match).
        
        For production, replace with vector similarity search.
        """
        query_lower = query.lower()
        results = []
        
        for entry in self._entries.values():
            if scope and entry.scope != scope:
                continue
            
            if entry.is_expired():
                continue
            
            # Basic content matching
            content_str = json.dumps(entry.content, default=str).lower()
            if query_lower in content_str:
                entry.access()
                results.append(entry)
        
        results.sort(key=lambda e: e.get_current_strength(), reverse=True)
        self._save()
        return results[:limit]
    
    def forget(self, entry_id: str) -> bool:
        """Explicitly remove a memory entry."""
        if entry_id in self._entries:
            del self._entries[entry_id]
            self._save()
            return True
        return False
    
    def cleanup(self, threshold: float = 0.1) -> int:
        """Remove expired memories. Returns count removed."""
        expired = [
            eid for eid, entry in self._entries.items()
            if entry.is_expired(threshold)
        ]
        for eid in expired:
            del self._entries[eid]
        
        if expired:
            self._save()
        return len(expired)
    
    def get_stats(self) -> dict:
        """Get memory store statistics."""
        stats = {
            "total_entries": len(self._entries),
            "by_scope": {},
            "by_source": {},
            "avg_strength": 0.0
        }
        
        total_strength = 0.0
        for entry in self._entries.values():
            scope_name = entry.scope.value
            stats["by_scope"][scope_name] = stats["by_scope"].get(scope_name, 0) + 1
            stats["by_source"][entry.source] = stats["by_source"].get(entry.source, 0) + 1
            total_strength += entry.get_current_strength()
        
        if self._entries:
            stats["avg_strength"] = total_strength / len(self._entries)
        
        return stats


# ==================== Agent-Specific Memory Helpers ====================

class AgentMemory:
    """Memory interface for a specific agent."""
    
    def __init__(self, agent_name: str, store: MemoryStore):
        self.agent_name = agent_name
        self.store = store
    
    def remember(
        self,
        content: Any,
        scope: MemoryScope = MemoryScope.WORKING,
        confidence: float = 1.0,
        tags: Optional[list[str]] = None
    ) -> str:
        """Store a memory as this agent."""
        return self.store.store(
            content=content,
            scope=scope,
            source=self.agent_name,
            confidence=confidence,
            tags=tags
        )
    
    def recall(
        self,
        scope: Optional[MemoryScope] = None,
        tags: Optional[list[str]] = None,
        limit: int = 50
    ) -> list[MemoryEntry]:
        """Recall memories relevant to this agent."""
        return self.store.retrieve(
            source=self.agent_name,
            scope=scope,
            tags=tags,
            limit=limit
        )
    
    def recall_all(
        self,
        scope: Optional[MemoryScope] = None,
        limit: int = 100
    ) -> list[MemoryEntry]:
        """Recall all memories (not just from this agent)."""
        return self.store.retrieve(scope=scope, limit=limit)
    
    def learn_from_failure(self, failure_info: dict) -> str:
        """Store a failure memory for learning."""
        return self.remember(
            content=failure_info,
            scope=MemoryScope.FAILURE,
            confidence=1.0,
            tags=["failure", "learning"]
        )
    
    def learn_skill(self, skill_info: dict) -> str:
        """Store a skill memory for long-term retention."""
        return self.remember(
            content=skill_info,
            scope=MemoryScope.SKILL,
            confidence=1.0,
            tags=["skill", "pattern"]
        )
