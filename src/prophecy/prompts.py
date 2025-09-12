"""Prompts management for yes/no questions about Hebrew bible stories."""

from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel
import json
from pathlib import Path


class PromptType(str, Enum):
    """Types of prompts that can be asked."""
    CHARACTER = "character"
    PLOT = "plot"
    THEME = "theme"
    SETTING = "setting"
    MORAL = "moral"
    PROPHECY = "prophecy"
    MIRACLE = "miracle"
    GENEALOGY = "genealogy"


class PromptResponse(str, Enum):
    """Possible responses to a prompt."""
    YES = "yes"
    NO = "no"
    UNKNOWN = "unknown"


class Prompt(BaseModel):
    """Represents a yes/no prompt about biblical content."""
    id: str
    text: str
    prompt_type: PromptType
    book: Optional[str] = None
    chapter: Optional[int] = None
    verse_start: Optional[int] = None
    verse_end: Optional[int] = None
    expected_answer: Optional[PromptResponse] = None
    explanation: Optional[str] = None
    difficulty: Optional[str] = None  # easy, medium, hard
    
    def get_reference(self) -> str:
        """Get the biblical reference for this prompt."""
        if not self.book:
            return "General"
        
        ref = self.book
        if self.chapter:
            ref += f" {self.chapter}"
            if self.verse_start:
                if self.verse_end and self.verse_end != self.verse_start:
                    ref += f":{self.verse_start}-{self.verse_end}"
                else:
                    ref += f":{self.verse_start}"
        return ref


class PromptsManager:
    """Manages prompts for the agentic system."""
    
    def __init__(self, prompts_file: Optional[Path] = None):
        """Initialize the prompts manager.
        
        Args:
            prompts_file: Path to JSON file containing prompts.
                         Defaults to 'prompts.json' in the data directory.
        """
        if prompts_file is None:
            prompts_file = Path(__file__).parent.parent.parent / "data" / "prompts.json"
        self.prompts_file = Path(prompts_file)
        self.prompts: List[Prompt] = []
        self._loaded = False
    
    def load_prompts(self) -> None:
        """Load prompts from the JSON file."""
        if self.prompts_file.exists():
            try:
                with open(self.prompts_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.prompts = []
                for prompt_data in data.get('prompts', []):
                    prompt = Prompt(**prompt_data)
                    self.prompts.append(prompt)
                
                self._loaded = True
                print(f"Loaded {len(self.prompts)} prompts")
            except Exception as e:
                print(f"Error loading prompts: {e}")
                self._create_default_prompts()
        else:
            print("Prompts file not found, creating default prompts")
            self._create_default_prompts()
    
    def _create_default_prompts(self) -> None:
        """Create default prompts as examples."""
        default_prompts = [
            {
                "id": "adam_eve_garden",
                "text": "Did Adam and Eve live in the Garden of Eden?",
                "prompt_type": "setting",
                "book": "Genesis",
                "chapter": 2,
                "verse_start": 8,
                "expected_answer": "yes",
                "explanation": "Genesis 2:8 states that God planted a garden in Eden and put Adam there.",
                "difficulty": "easy"
            },
            {
                "id": "noah_ark_animals",
                "text": "Did Noah take two of every animal onto the ark?",
                "prompt_type": "plot",
                "book": "Genesis",
                "chapter": 7,
                "verse_start": 9,
                "expected_answer": "yes",
                "explanation": "Genesis 7:9 describes animals going into the ark two by two.",
                "difficulty": "easy"
            },
            {
                "id": "moses_burning_bush",
                "text": "Did Moses encounter a burning bush that was not consumed?",
                "prompt_type": "miracle",
                "book": "Exodus",
                "chapter": 3,
                "verse_start": 2,
                "expected_answer": "yes",
                "explanation": "Exodus 3:2 describes the angel of the Lord appearing in a burning bush that was not consumed.",
                "difficulty": "medium"
            },
            {
                "id": "david_goliath",
                "text": "Did David defeat Goliath with a sword?",
                "prompt_type": "plot",
                "book": "1 Samuel",
                "chapter": 17,
                "verse_start": 50,
                "expected_answer": "no",
                "explanation": "1 Samuel 17:50 states David defeated Goliath with a sling and stone, not a sword.",
                "difficulty": "medium"
            },
            {
                "id": "jonah_whale",
                "text": "Was Jonah swallowed by a whale?",
                "prompt_type": "miracle",
                "book": "Jonah",
                "chapter": 1,
                "verse_start": 17,
                "expected_answer": "no",
                "explanation": "Jonah 1:17 mentions a 'great fish', not specifically a whale.",
                "difficulty": "hard"
            },
            {
                "id": "jesus_birthplace",
                "text": "Was Jesus born in Bethlehem?",
                "prompt_type": "setting",
                "book": "Matthew",
                "chapter": 2,
                "verse_start": 1,
                "expected_answer": "yes",
                "explanation": "Matthew 2:1 states Jesus was born in Bethlehem of Judea.",
                "difficulty": "easy"
            }
        ]
        
        self.prompts = [Prompt(**prompt_data) for prompt_data in default_prompts]
        self._loaded = True
        
        # Save default prompts to file
        self.save_prompts()
    
    def save_prompts(self) -> None:
        """Save current prompts to the JSON file."""
        # Create directory if it doesn't exist
        self.prompts_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "prompts": [prompt.model_dump() for prompt in self.prompts]
        }
        
        with open(self.prompts_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def get_prompts_by_type(self, prompt_type: PromptType) -> List[Prompt]:
        """Get all prompts of a specific type."""
        if not self._loaded:
            self.load_prompts()
        return [p for p in self.prompts if p.prompt_type == prompt_type]
    
    def get_prompts_by_book(self, book: str) -> List[Prompt]:
        """Get all prompts for a specific book."""
        if not self._loaded:
            self.load_prompts()
        return [p for p in self.prompts if p.book and p.book.lower() == book.lower()]
    
    def get_prompts_by_difficulty(self, difficulty: str) -> List[Prompt]:
        """Get all prompts of a specific difficulty."""
        if not self._loaded:
            self.load_prompts()
        return [p for p in self.prompts if p.difficulty == difficulty]
    
    def get_prompt_by_id(self, prompt_id: str) -> Optional[Prompt]:
        """Get a specific prompt by ID."""
        if not self._loaded:
            self.load_prompts()
        for prompt in self.prompts:
            if prompt.id == prompt_id:
                return prompt
        return None
    
    def add_prompt(self, prompt: Prompt) -> None:
        """Add a new prompt."""
        if not self._loaded:
            self.load_prompts()
        
        # Check for duplicate IDs
        if any(p.id == prompt.id for p in self.prompts):
            raise ValueError(f"Prompt with ID '{prompt.id}' already exists")
        
        self.prompts.append(prompt)
    
    def remove_prompt(self, prompt_id: str) -> bool:
        """Remove a prompt by ID. Returns True if found and removed."""
        if not self._loaded:
            self.load_prompts()
        
        for i, prompt in enumerate(self.prompts):
            if prompt.id == prompt_id:
                del self.prompts[i]
                return True
        return False
    
    def get_all_prompts(self) -> List[Prompt]:
        """Get all available prompts."""
        if not self._loaded:
            self.load_prompts()
        return self.prompts.copy()
    
    def get_random_prompt(self, prompt_type: Optional[PromptType] = None, 
                         difficulty: Optional[str] = None) -> Optional[Prompt]:
        """Get a random prompt, optionally filtered by type or difficulty."""
        import random
        
        if not self._loaded:
            self.load_prompts()
        
        candidates = self.prompts.copy()
        
        if prompt_type:
            candidates = [p for p in candidates if p.prompt_type == prompt_type]
        
        if difficulty:
            candidates = [p for p in candidates if p.difficulty == difficulty]
        
        if not candidates:
            return None
        
        return random.choice(candidates)