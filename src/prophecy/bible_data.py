"""Bible data management for Hebrew biblical texts."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class BibleVerse(BaseModel):
    """Represents a single verse from the Bible."""
    book: str
    chapter: int
    verse: int
    text: str
    
    def __str__(self) -> str:
        return f"{self.book} {self.chapter}:{self.verse} - {self.text}"


class BibleChapter(BaseModel):
    """Represents a chapter from the Bible."""
    book: str
    chapter: int
    verses: List[BibleVerse]
    
    def get_verse(self, verse_num: int) -> Optional[BibleVerse]:
        """Get a specific verse from this chapter."""
        for verse in self.verses:
            if verse.verse == verse_num:
                return verse
        return None


class BibleBook(BaseModel):
    """Represents a book from the Bible."""
    name: str
    chapters: List[BibleChapter]
    
    def get_chapter(self, chapter_num: int) -> Optional[BibleChapter]:
        """Get a specific chapter from this book."""
        for chapter in self.chapters:
            if chapter.chapter == chapter_num:
                return chapter
        return None
    
    def get_verse(self, chapter_num: int, verse_num: int) -> Optional[BibleVerse]:
        """Get a specific verse from this book."""
        chapter = self.get_chapter(chapter_num)
        if chapter:
            return chapter.get_verse(verse_num)
        return None


class BibleDataManager:
    """Manages loading and accessing Hebrew biblical texts from JSON files."""
    
    def __init__(self, data_path: Optional[Path] = None):
        """Initialize the Bible data manager.
        
        Args:
            data_path: Path to directory containing JSON files for biblical books.
                      Defaults to 'data' subdirectory.
        """
        if data_path is None:
            data_path = Path(__file__).parent.parent.parent / "data"
        self.data_path = Path(data_path)
        self.books: Dict[str, BibleBook] = {}
        self._loaded = False
    
    def load_data(self) -> None:
        """Load all biblical data from JSON files."""
        if not self.data_path.exists():
            raise FileNotFoundError(f"Bible data directory not found: {self.data_path}")
        
        json_files = list(self.data_path.glob("*.json"))
        # Filter out prompts.json and other non-bible files
        bible_files = [f for f in json_files if f.name not in ['prompts.json', 'config.json']]
        
        if not bible_files:
            raise FileNotFoundError(f"No biblical JSON files found in {self.data_path}")
        
        for json_file in bible_files:
            try:
                book = self._load_book_from_file(json_file)
                self.books[book.name.lower()] = book
            except Exception as e:
                print(f"Warning: Failed to load {json_file}: {e}")
        
        self._loaded = True
        print(f"Loaded {len(self.books)} biblical books")
    
    def _load_book_from_file(self, file_path: Path) -> BibleBook:
        """Load a single book from a JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Flexible JSON structure handling
        if isinstance(data, dict):
            if 'name' in data and 'chapters' in data:
                # Direct book format
                return self._parse_book_data(data)
            elif 'book' in data:
                # Nested book format
                return self._parse_book_data(data['book'])
            else:
                # Assume the entire dict is chapters with book name from filename
                book_name = file_path.stem.title()
                return self._parse_chapters_data(book_name, data)
        else:
            raise ValueError(f"Unexpected JSON structure in {file_path}")
    
    def _parse_book_data(self, book_data: Dict[str, Any]) -> BibleBook:
        """Parse book data from a dictionary."""
        book_name = book_data['name']
        chapters_data = book_data['chapters']
        
        chapters = []
        for chapter_data in chapters_data:
            chapter = self._parse_chapter_data(book_name, chapter_data)
            chapters.append(chapter)
        
        return BibleBook(name=book_name, chapters=chapters)
    
    def _parse_chapters_data(self, book_name: str, chapters_data: Dict[str, Any]) -> BibleBook:
        """Parse chapters data when the JSON root is chapters."""
        chapters = []
        for chapter_key, verses_data in chapters_data.items():
            chapter_num = int(chapter_key)
            verses = []
            for verse_key, text in verses_data.items():
                verse_num = int(verse_key)
                verse = BibleVerse(
                    book=book_name,
                    chapter=chapter_num,
                    verse=verse_num,
                    text=str(text)
                )
                verses.append(verse)
            
            chapter = BibleChapter(
                book=book_name,
                chapter=chapter_num,
                verses=verses
            )
            chapters.append(chapter)
        
        return BibleBook(name=book_name, chapters=chapters)
    
    def _parse_chapter_data(self, book_name: str, chapter_data: Dict[str, Any]) -> BibleChapter:
        """Parse a single chapter's data."""
        chapter_num = chapter_data['chapter']
        verses_data = chapter_data['verses']
        
        verses = []
        for verse_data in verses_data:
            verse = BibleVerse(
                book=book_name,
                chapter=chapter_num,
                verse=verse_data['verse'],
                text=verse_data['text']
            )
            verses.append(verse)
        
        return BibleChapter(
            book=book_name,
            chapter=chapter_num,
            verses=verses
        )
    
    def get_book(self, book_name: str) -> Optional[BibleBook]:
        """Get a specific book by name."""
        if not self._loaded:
            self.load_data()
        return self.books.get(book_name.lower())
    
    def get_verse(self, book_name: str, chapter: int, verse: int) -> Optional[BibleVerse]:
        """Get a specific verse."""
        book = self.get_book(book_name)
        if book:
            return book.get_verse(chapter, verse)
        return None
    
    def get_chapter(self, book_name: str, chapter: int) -> Optional[BibleChapter]:
        """Get a specific chapter."""
        book = self.get_book(book_name)
        if book:
            return book.get_chapter(chapter)
        return None
    
    def list_books(self) -> List[str]:
        """Get a list of all available book names."""
        if not self._loaded:
            self.load_data()
        return list(self.books.keys())
    
    def search_text(self, query: str, book_name: Optional[str] = None) -> List[BibleVerse]:
        """Search for text across verses.
        
        Args:
            query: Text to search for
            book_name: Optional book name to limit search to
            
        Returns:
            List of verses containing the query text
        """
        if not self._loaded:
            self.load_data()
        
        results = []
        books_to_search = [self.books[book_name.lower()]] if book_name else self.books.values()
        
        for book in books_to_search:
            for chapter in book.chapters:
                for verse in chapter.verses:
                    if query.lower() in verse.text.lower():
                        results.append(verse)
        
        return results