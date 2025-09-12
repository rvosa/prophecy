"""Test suite for the Prophecy agentic system."""

import pytest
import tempfile
import json
from pathlib import Path

from prophecy.bible_data import BibleDataManager, BibleVerse
from prophecy.prompts import PromptsManager, Prompt, PromptType, PromptResponse
from prophecy.agent import ProphecyAgent


class TestBibleDataManager:
    """Test the Bible data management functionality."""
    
    def test_load_bible_data(self):
        """Test loading Bible data from JSON files."""
        # Create temporary test data
        with tempfile.TemporaryDirectory() as temp_dir:
            test_data_path = Path(temp_dir)
            
            # Create a test Genesis file
            genesis_data = {
                "name": "Genesis",
                "chapters": [
                    {
                        "chapter": 1,
                        "verses": [
                            {"verse": 1, "text": "In the beginning God created the heaven and the earth."}
                        ]
                    }
                ]
            }
            
            with open(test_data_path / "genesis.json", 'w') as f:
                json.dump(genesis_data, f)
            
            # Test loading
            manager = BibleDataManager(test_data_path)
            manager.load_data()
            
            assert len(manager.books) == 1
            assert "genesis" in manager.books
            
            book = manager.get_book("Genesis")
            assert book is not None
            assert book.name == "Genesis"
    
    def test_get_verse(self):
        """Test retrieving specific verses."""
        # Create temporary test data
        with tempfile.TemporaryDirectory() as temp_dir:
            test_data_path = Path(temp_dir)
            
            genesis_data = {
                "name": "Genesis",
                "chapters": [
                    {
                        "chapter": 1,
                        "verses": [
                            {"verse": 1, "text": "In the beginning God created the heaven and the earth."},
                            {"verse": 2, "text": "And the earth was without form, and void."}
                        ]
                    }
                ]
            }
            
            with open(test_data_path / "genesis.json", 'w') as f:
                json.dump(genesis_data, f)
            
            manager = BibleDataManager(test_data_path)
            manager.load_data()
            
            verse = manager.get_verse("Genesis", 1, 1)
            assert verse is not None
            assert verse.text == "In the beginning God created the heaven and the earth."
            
            # Test non-existent verse
            verse = manager.get_verse("Genesis", 1, 999)
            assert verse is None
    
    def test_search_text(self):
        """Test text search functionality."""
        # Create temporary test data
        with tempfile.TemporaryDirectory() as temp_dir:
            test_data_path = Path(temp_dir)
            
            genesis_data = {
                "name": "Genesis",
                "chapters": [
                    {
                        "chapter": 1,
                        "verses": [
                            {"verse": 1, "text": "In the beginning God created the heaven and the earth."},
                            {"verse": 3, "text": "And God said, Let there be light: and there was light."}
                        ]
                    }
                ]
            }
            
            with open(test_data_path / "genesis.json", 'w') as f:
                json.dump(genesis_data, f)
            
            manager = BibleDataManager(test_data_path)
            manager.load_data()
            
            results = manager.search_text("God")
            assert len(results) == 2
            
            results = manager.search_text("light")
            assert len(results) == 1
            assert results[0].verse == 3


class TestPromptsManager:
    """Test the prompts management functionality."""
    
    def test_default_prompts_creation(self):
        """Test that default prompts are created when no file exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            prompts_file = Path(temp_dir) / "prompts.json"
            
            manager = PromptsManager(prompts_file)
            manager.load_prompts()
            
            assert len(manager.prompts) > 0
            assert prompts_file.exists()
    
    def test_prompt_filtering(self):
        """Test filtering prompts by type and difficulty."""
        with tempfile.TemporaryDirectory() as temp_dir:
            prompts_file = Path(temp_dir) / "prompts.json"
            
            manager = PromptsManager(prompts_file)
            manager.load_prompts()
            
            # Test filtering by type
            plot_prompts = manager.get_prompts_by_type(PromptType.PLOT)
            assert all(p.prompt_type == PromptType.PLOT for p in plot_prompts)
            
            # Test filtering by difficulty
            easy_prompts = manager.get_prompts_by_difficulty("easy")
            assert all(p.difficulty == "easy" for p in easy_prompts)
    
    def test_add_custom_prompt(self):
        """Test adding custom prompts."""
        with tempfile.TemporaryDirectory() as temp_dir:
            prompts_file = Path(temp_dir) / "prompts.json"
            
            manager = PromptsManager(prompts_file)
            manager.load_prompts()
            
            initial_count = len(manager.prompts)
            
            custom_prompt = Prompt(
                id="test_prompt",
                text="Is this a test?",
                prompt_type=PromptType.PLOT,
                expected_answer=PromptResponse.YES
            )
            
            manager.add_prompt(custom_prompt)
            assert len(manager.prompts) == initial_count + 1
            
            retrieved = manager.get_prompt_by_id("test_prompt")
            assert retrieved is not None
            assert retrieved.text == "Is this a test?"


class TestProphecyAgent:
    """Test the main agent functionality."""
    
    def test_agent_initialization(self):
        """Test agent initialization with temporary data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test data
            data_path = Path(temp_dir) / "data"
            data_path.mkdir()
            
            genesis_data = {
                "name": "Genesis",
                "chapters": [
                    {
                        "chapter": 1,
                        "verses": [
                            {"verse": 1, "text": "In the beginning God created the heaven and the earth."}
                        ]
                    }
                ]
            }
            
            with open(data_path / "genesis.json", 'w') as f:
                json.dump(genesis_data, f)
            
            agent = ProphecyAgent(str(data_path))
            agent.initialize()
            
            assert agent.bible_manager._loaded
            assert agent.prompts_manager._loaded
    
    def test_prompt_session(self):
        """Test a basic prompt session."""
        with tempfile.TemporaryDirectory() as temp_dir:
            agent = ProphecyAgent()
            agent.prompts_manager.load_prompts()
            
            agent.start_new_session()
            
            # Get a prompt
            prompt = agent.get_random_prompt()
            assert prompt is not None
            
            # Ask the prompt
            context = agent.ask_prompt(prompt)
            assert "prompt" in context
            assert context["prompt"] == prompt
            
            # Submit a response
            result = agent.submit_response(prompt, PromptResponse.YES)
            assert result is not None
            assert result.prompt == prompt
            assert result.user_response == PromptResponse.YES
            
            # End session
            stats = agent.end_session()
            assert stats.total_questions == 1
    
    def test_search_functionality(self):
        """Test biblical text search through the agent."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test data
            data_path = Path(temp_dir) / "data"
            data_path.mkdir()
            
            genesis_data = {
                "name": "Genesis",
                "chapters": [
                    {
                        "chapter": 1,
                        "verses": [
                            {"verse": 1, "text": "In the beginning God created the heaven and the earth."},
                            {"verse": 3, "text": "And God said, Let there be light: and there was light."}
                        ]
                    }
                ]
            }
            
            with open(data_path / "genesis.json", 'w') as f:
                json.dump(genesis_data, f)
            
            agent = ProphecyAgent(str(data_path))
            agent.bible_manager.load_data()
            
            results = agent.search_biblical_text("God")
            assert len(results) == 2
            
            results = agent.search_biblical_text("light")
            assert len(results) == 1


if __name__ == "__main__":
    pytest.main([__file__])