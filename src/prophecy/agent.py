"""Main agentic system for processing Hebrew bible stories with yes/no prompts."""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import random

from .bible_data import BibleDataManager, BibleVerse
from .prompts import PromptsManager, Prompt, PromptResponse, PromptType


class SessionResult:
    """Stores the result of a single prompt session."""
    
    def __init__(self, prompt: Prompt, user_response: PromptResponse, 
                 is_correct: Optional[bool] = None, timestamp: Optional[datetime] = None):
        self.prompt = prompt
        self.user_response = user_response
        self.is_correct = is_correct
        self.timestamp = timestamp or datetime.now()
    
    def __str__(self) -> str:
        status = "✓" if self.is_correct else "✗" if self.is_correct is False else "?"
        return f"{status} {self.prompt.text} -> {self.user_response.value}"


class SessionStats:
    """Statistics for a session or set of sessions."""
    
    def __init__(self, results: List[SessionResult]):
        self.results = results
        self.total_questions = len(results)
        self.correct_answers = sum(1 for r in results if r.is_correct is True)
        self.incorrect_answers = sum(1 for r in results if r.is_correct is False)
        self.unknown_answers = sum(1 for r in results if r.is_correct is None)
        
        self.accuracy = (self.correct_answers / self.total_questions * 100) if self.total_questions > 0 else 0.0
    
    def get_stats_by_type(self) -> Dict[PromptType, Dict[str, int]]:
        """Get statistics broken down by prompt type."""
        stats = {}
        for result in self.results:
            prompt_type = result.prompt.prompt_type
            if prompt_type not in stats:
                stats[prompt_type] = {"total": 0, "correct": 0, "incorrect": 0, "unknown": 0}
            
            stats[prompt_type]["total"] += 1
            if result.is_correct is True:
                stats[prompt_type]["correct"] += 1
            elif result.is_correct is False:
                stats[prompt_type]["incorrect"] += 1
            else:
                stats[prompt_type]["unknown"] += 1
        
        return stats
    
    def get_stats_by_difficulty(self) -> Dict[str, Dict[str, int]]:
        """Get statistics broken down by difficulty."""
        stats = {}
        for result in self.results:
            difficulty = result.prompt.difficulty or "unknown"
            if difficulty not in stats:
                stats[difficulty] = {"total": 0, "correct": 0, "incorrect": 0, "unknown": 0}
            
            stats[difficulty]["total"] += 1
            if result.is_correct is True:
                stats[difficulty]["correct"] += 1
            elif result.is_correct is False:
                stats[difficulty]["incorrect"] += 1
            else:
                stats[difficulty]["unknown"] += 1
        
        return stats


class ProphecyAgent:
    """Main agentic system for processing Hebrew bible stories with prompts."""
    
    def __init__(self, data_path: Optional[str] = None, prompts_file: Optional[str] = None):
        """Initialize the Prophecy agent.
        
        Args:
            data_path: Path to directory containing biblical JSON files
            prompts_file: Path to prompts JSON file
        """
        self.bible_manager = BibleDataManager(data_path)
        self.prompts_manager = PromptsManager(prompts_file)
        self.session_results: List[SessionResult] = []
        self.current_session_results: List[SessionResult] = []
    
    def initialize(self) -> None:
        """Initialize the agent by loading data and prompts."""
        print("Initializing Prophecy Agent...")
        try:
            self.bible_manager.load_data()
        except FileNotFoundError as e:
            print(f"Warning: {e}")
            print("Bible data will not be available for verse lookup.")
        
        self.prompts_manager.load_prompts()
        print("Agent initialized successfully!")
    
    def start_new_session(self) -> None:
        """Start a new question session."""
        self.current_session_results = []
    
    def get_random_prompt(self, prompt_type: Optional[PromptType] = None, 
                         difficulty: Optional[str] = None) -> Optional[Prompt]:
        """Get a random prompt for the user."""
        return self.prompts_manager.get_random_prompt(prompt_type, difficulty)
    
    def ask_prompt(self, prompt: Prompt) -> Dict[str, Any]:
        """Present a prompt and return context information.
        
        Returns a dictionary with prompt information and related biblical context.
        """
        context = {
            "prompt": prompt,
            "reference": prompt.get_reference(),
            "type": prompt.prompt_type.value,
            "difficulty": prompt.difficulty,
            "related_verses": []
        }
        
        # Try to get related biblical verses
        if prompt.book and prompt.chapter:
            if prompt.verse_start:
                verse_end = prompt.verse_end or prompt.verse_start
                for verse_num in range(prompt.verse_start, verse_end + 1):
                    verse = self.bible_manager.get_verse(prompt.book, prompt.chapter, verse_num)
                    if verse:
                        context["related_verses"].append(verse)
            else:
                # Get the whole chapter
                chapter = self.bible_manager.get_chapter(prompt.book, prompt.chapter)
                if chapter:
                    context["related_verses"] = chapter.verses[:5]  # Limit to first 5 verses
        
        return context
    
    def submit_response(self, prompt: Prompt, user_response: PromptResponse) -> SessionResult:
        """Submit a user response to a prompt and get the result."""
        # Determine if the response is correct
        is_correct = None
        if prompt.expected_answer:
            is_correct = (user_response == prompt.expected_answer)
        
        result = SessionResult(prompt, user_response, is_correct)
        self.current_session_results.append(result)
        self.session_results.append(result)
        
        return result
    
    def get_prompt_explanation(self, prompt: Prompt) -> Optional[str]:
        """Get the explanation for a prompt's correct answer."""
        return prompt.explanation
    
    def end_session(self) -> SessionStats:
        """End the current session and return statistics."""
        stats = SessionStats(self.current_session_results)
        return stats
    
    def get_overall_stats(self) -> SessionStats:
        """Get statistics for all sessions."""
        return SessionStats(self.session_results)
    
    def search_biblical_text(self, query: str, book: Optional[str] = None) -> List[BibleVerse]:
        """Search for text in biblical content."""
        return self.bible_manager.search_text(query, book)
    
    def get_verse(self, book: str, chapter: int, verse: int) -> Optional[BibleVerse]:
        """Get a specific biblical verse."""
        return self.bible_manager.get_verse(book, chapter, verse)
    
    def list_available_books(self) -> List[str]:
        """Get a list of available biblical books."""
        return self.bible_manager.list_books()
    
    def get_prompts_by_type(self, prompt_type: PromptType) -> List[Prompt]:
        """Get all prompts of a specific type."""
        return self.prompts_manager.get_prompts_by_type(prompt_type)
    
    def get_prompts_by_book(self, book: str) -> List[Prompt]:
        """Get all prompts for a specific book."""
        return self.prompts_manager.get_prompts_by_book(book)
    
    def get_prompts_by_difficulty(self, difficulty: str) -> List[Prompt]:
        """Get all prompts of a specific difficulty."""
        return self.prompts_manager.get_prompts_by_difficulty(difficulty)
    
    def add_custom_prompt(self, prompt_data: Dict[str, Any]) -> Prompt:
        """Add a custom prompt to the system."""
        prompt = Prompt(**prompt_data)
        self.prompts_manager.add_prompt(prompt)
        return prompt
    
    def interactive_session(self, num_questions: int = 10, 
                           prompt_type: Optional[PromptType] = None,
                           difficulty: Optional[str] = None) -> SessionStats:
        """Run an interactive session with the specified parameters."""
        self.start_new_session()
        
        print(f"Starting interactive session with {num_questions} questions")
        if prompt_type:
            print(f"Prompt type: {prompt_type.value}")
        if difficulty:
            print(f"Difficulty: {difficulty}")
        print("-" * 50)
        
        for i in range(num_questions):
            prompt = self.get_random_prompt(prompt_type, difficulty)
            if not prompt:
                print("No more prompts available with the specified criteria.")
                break
            
            print(f"\nQuestion {i + 1}/{num_questions}")
            context = self.ask_prompt(prompt)
            
            print(f"Reference: {context['reference']}")
            print(f"Type: {context['type'].title()}")
            if context['difficulty']:
                print(f"Difficulty: {context['difficulty'].title()}")
            print(f"\n{prompt.text}")
            
            # In a real interactive system, this would get user input
            # For now, we'll simulate random responses
            response = random.choice([PromptResponse.YES, PromptResponse.NO])
            print(f"Response: {response.value}")
            
            result = self.submit_response(prompt, response)
            
            if result.is_correct is not None:
                if result.is_correct:
                    print("✓ Correct!")
                else:
                    print("✗ Incorrect!")
                    if prompt.expected_answer:
                        print(f"Expected: {prompt.expected_answer.value}")
                
                if prompt.explanation:
                    print(f"Explanation: {prompt.explanation}")
            else:
                print("No expected answer available.")
            
            print("-" * 30)
        
        return self.end_session()