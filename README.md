# Prophecy

An agentic system for processing Hebrew bible stories with yes/no prompts.

## Overview

Prophecy is an intelligent system that presents users with yes/no questions about biblical stories and provides contextual information, explanations, and statistics. The system is designed to work with Hebrew biblical texts stored as JSON files and can be extended with custom prompts.

## Features

- **Interactive Q&A Sessions**: Run sessions with customizable parameters (number of questions, difficulty, topic type)
- **Biblical Text Search**: Search through biblical content for specific terms or phrases
- **Contextual Learning**: Get related verses and explanations for each question
- **Statistics Tracking**: Track performance across sessions with detailed analytics
- **Flexible Data Format**: Support for various JSON structures for biblical data
- **CLI Interface**: Rich command-line interface with colored output and tables
- **Extensible Prompts**: Easy to add custom prompts and categories

## Installation

1. Clone this repository:
```bash
git clone https://github.com/rvosa/prophecy.git
cd prophecy
```

2. Install the package:
```bash
pip install -e .
```

3. (Optional) Install development dependencies:
```bash
pip install -e .[dev]
```

## Quick Start

1. Initialize the system:
```bash
prophecy initialize
```

2. Start an interactive session:
```bash
prophecy interactive
```

3. Search biblical text:
```bash
prophecy search "light"
```

4. View available books:
```bash
prophecy list-books
```

## Usage

### Interactive Sessions

Run an interactive Q&A session:

```bash
# Basic session with 10 questions
prophecy interactive

# Custom session with specific parameters
prophecy interactive --num-questions 20 --type plot --difficulty medium

# Session focused on a specific topic
prophecy interactive --type miracle --difficulty hard
```

### Search Functions

Search for text in biblical content:

```bash
# Search all books
prophecy search "garden"

# Search specific book
prophecy search "burning bush" --book exodus
```

Get a specific verse:

```bash
prophecy verse Genesis 1 1
```

### List Commands

```bash
# List available books
prophecy list-books

# List all prompts
prophecy list-prompts

# Filter prompts by type or difficulty
prophecy list-prompts --type character --difficulty easy
```

### Statistics

View your performance statistics:

```bash
prophecy stats
```

## Data Structure

### Biblical Data

Biblical data should be stored as JSON files in the `data/` directory. Each file represents one book:

```json
{
  "name": "Genesis",
  "chapters": [
    {
      "chapter": 1,
      "verses": [
        {
          "verse": 1,
          "text": "In the beginning God created the heaven and the earth."
        }
      ]
    }
  ]
}
```

### Prompts Data

Prompts are stored in `data/prompts.json`:

```json
{
  "prompts": [
    {
      "id": "unique_id",
      "text": "Did Adam and Eve live in the Garden of Eden?",
      "prompt_type": "setting",
      "book": "Genesis",
      "chapter": 2,
      "verse_start": 8,
      "expected_answer": "yes",
      "explanation": "Genesis 2:8 describes God placing Adam in the garden.",
      "difficulty": "easy"
    }
  ]
}
```

### Prompt Types

- `character`: Questions about biblical characters
- `plot`: Questions about story events and narratives
- `theme`: Questions about themes and messages
- `setting`: Questions about locations and contexts
- `moral`: Questions about moral and ethical aspects
- `prophecy`: Questions about prophetic content
- `miracle`: Questions about miracles and supernatural events
- `genealogy`: Questions about family relationships and lineages

## Git Submodule for Bible Data

To add biblical data via git submodule:

```bash
git submodule add https://github.com/your-repo/bible-data.git data/bible-texts
```

The system will automatically detect and load JSON files from subdirectories.

## Development

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
# Format code
black src/

# Check imports
isort src/

# Lint code
flake8 src/

# Type checking
mypy src/
```

### Adding Custom Prompts

You can add custom prompts programmatically:

```python
from prophecy import ProphecyAgent
from prophecy.prompts import Prompt, PromptType, PromptResponse

agent = ProphecyAgent()
agent.initialize()

custom_prompt = Prompt(
    id="my_custom_prompt",
    text="Was Moses found in a basket?",
    prompt_type=PromptType.PLOT,
    book="Exodus",
    chapter=2,
    verse_start=3,
    expected_answer=PromptResponse.YES,
    explanation="Exodus 2:3 describes Moses being placed in a basket.",
    difficulty="medium"
)

agent.add_custom_prompt(custom_prompt.model_dump())
```

## Configuration

The system looks for data in the following locations:

- Biblical data: `data/` directory (JSON files)
- Prompts: `data/prompts.json`
- Custom paths can be specified via CLI options

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request