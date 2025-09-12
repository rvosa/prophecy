"""Command-line interface for the Prophecy agentic system."""

import click
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt as RichPrompt, Confirm
from rich.panel import Panel
from rich.text import Text
from typing import Optional

from .agent import ProphecyAgent, SessionStats
from .prompts import PromptType, PromptResponse

console = Console()


def print_stats(stats: SessionStats, title: str = "Session Statistics") -> None:
    """Print session statistics in a formatted table."""
    # Overall stats
    table = Table(title=title, show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="green")
    
    table.add_row("Total Questions", str(stats.total_questions))
    table.add_row("Correct Answers", str(stats.correct_answers))
    table.add_row("Incorrect Answers", str(stats.incorrect_answers))
    table.add_row("Unknown Answers", str(stats.unknown_answers))
    table.add_row("Accuracy", f"{stats.accuracy:.1f}%")
    
    console.print(table)
    
    # Stats by type
    type_stats = stats.get_stats_by_type()
    if type_stats:
        console.print("\n[bold]By Prompt Type:[/bold]")
        type_table = Table(show_header=True, header_style="bold blue")
        type_table.add_column("Type")
        type_table.add_column("Total", justify="right")
        type_table.add_column("Correct", justify="right")
        type_table.add_column("Accuracy", justify="right")
        
        for prompt_type, data in type_stats.items():
            accuracy = (data["correct"] / data["total"] * 100) if data["total"] > 0 else 0
            type_table.add_row(
                prompt_type.value.title(),
                str(data["total"]),
                str(data["correct"]),
                f"{accuracy:.1f}%"
            )
        
        console.print(type_table)
    
    # Stats by difficulty
    diff_stats = stats.get_stats_by_difficulty()
    if diff_stats:
        console.print("\n[bold]By Difficulty:[/bold]")
        diff_table = Table(show_header=True, header_style="bold yellow")
        diff_table.add_column("Difficulty")
        diff_table.add_column("Total", justify="right")
        diff_table.add_column("Correct", justify="right")
        diff_table.add_column("Accuracy", justify="right")
        
        for difficulty, data in diff_stats.items():
            accuracy = (data["correct"] / data["total"] * 100) if data["total"] > 0 else 0
            diff_table.add_row(
                difficulty.title(),
                str(data["total"]),
                str(data["correct"]),
                f"{accuracy:.1f}%"
            )
        
        console.print(diff_table)


@click.group()
@click.option('--data-path', help='Path to biblical data directory')
@click.option('--prompts-file', help='Path to prompts JSON file')
@click.pass_context
def cli(ctx, data_path, prompts_file):
    """Prophecy: An agentic system for processing Hebrew bible stories."""
    ctx.ensure_object(dict)
    ctx.obj['agent'] = ProphecyAgent(data_path, prompts_file)


@cli.command()
@click.pass_context
def initialize(ctx):
    """Initialize the agent by loading data and prompts."""
    agent = ctx.obj['agent']
    with console.status("[bold green]Initializing agent..."):
        agent.initialize()
    console.print("[bold green]✓[/bold green] Agent initialized successfully!")


@cli.command()
@click.option('--num-questions', '-n', default=10, help='Number of questions to ask')
@click.option('--type', 'prompt_type', type=click.Choice([t.value for t in PromptType]), help='Filter by prompt type')
@click.option('--difficulty', type=click.Choice(['easy', 'medium', 'hard']), help='Filter by difficulty')
@click.pass_context
def interactive(ctx, num_questions, prompt_type, difficulty):
    """Start an interactive question session."""
    agent = ctx.obj['agent']
    
    # Initialize if not already done
    if not agent.prompts_manager._loaded:
        with console.status("[bold green]Initializing agent..."):
            agent.initialize()
    
    # Convert string to enum if provided
    prompt_type_enum = PromptType(prompt_type) if prompt_type else None
    
    console.print(Panel.fit(
        f"[bold blue]Interactive Session[/bold blue]\n"
        f"Questions: {num_questions}\n"
        f"Type: {prompt_type or 'All'}\n"
        f"Difficulty: {difficulty or 'All'}",
        border_style="blue"
    ))
    
    agent.start_new_session()
    
    for i in range(num_questions):
        prompt = agent.get_random_prompt(prompt_type_enum, difficulty)
        if not prompt:
            console.print("[yellow]No more prompts available with the specified criteria.[/yellow]")
            break
        
        console.print(f"\n[bold]Question {i + 1}/{num_questions}[/bold]")
        
        context = agent.ask_prompt(prompt)
        
        # Display prompt information
        info_text = f"Reference: {context['reference']}\n"
        info_text += f"Type: {context['type'].title()}\n"
        if context['difficulty']:
            info_text += f"Difficulty: {context['difficulty'].title()}\n"
        
        console.print(Panel(info_text, title="Context", border_style="cyan"))
        
        # Display related verses if available
        if context['related_verses']:
            verses_text = ""
            for verse in context['related_verses'][:3]:  # Show max 3 verses
                verses_text += f"{verse.book} {verse.chapter}:{verse.verse} - {verse.text[:100]}...\n"
            
            if verses_text:
                console.print(Panel(verses_text.strip(), title="Related Verses", border_style="green"))
        
        # Ask the question
        console.print(f"\n[bold yellow]{prompt.text}[/bold yellow]")
        
        # Get user response
        response_str = RichPrompt.ask(
            "Your answer",
            choices=["yes", "y", "no", "n"],
            default="yes"
        ).lower()
        
        if response_str in ["yes", "y"]:
            user_response = PromptResponse.YES
        else:
            user_response = PromptResponse.NO
        
        # Submit response and get result
        result = agent.submit_response(prompt, user_response)
        
        # Show result
        if result.is_correct is not None:
            if result.is_correct:
                console.print("[bold green]✓ Correct![/bold green]")
            else:
                console.print("[bold red]✗ Incorrect![/bold red]")
                if prompt.expected_answer:
                    console.print(f"Expected: [bold]{prompt.expected_answer.value}[/bold]")
            
            if prompt.explanation:
                console.print(Panel(prompt.explanation, title="Explanation", border_style="yellow"))
        else:
            console.print("[yellow]No expected answer available.[/yellow]")
        
        # Ask if user wants to continue
        if i < num_questions - 1:
            if not Confirm.ask("\nContinue to next question?", default=True):
                break
    
    # Show session statistics
    stats = agent.end_session()
    console.print("\n")
    print_stats(stats, "Session Complete!")


@cli.command()
@click.option('--book', help='Search within a specific book')
@click.argument('query')
@click.pass_context
def search(ctx, query, book):
    """Search for text in biblical content."""
    agent = ctx.obj['agent']
    
    # Initialize if not already done
    if not agent.bible_manager._loaded:
        with console.status("[bold green]Loading biblical data..."):
            try:
                agent.bible_manager.load_data()
            except FileNotFoundError:
                console.print("[red]Biblical data not available. Please check data directory.[/red]")
                return
    
    with console.status(f"[bold green]Searching for '{query}'..."):
        results = agent.search_biblical_text(query, book)
    
    if not results:
        console.print(f"[yellow]No results found for '[bold]{query}[/bold]'[/yellow]")
        return
    
    console.print(f"\n[bold green]Found {len(results)} results for '[bold]{query}[/bold]':[/bold green]")
    
    for i, verse in enumerate(results[:10], 1):  # Show max 10 results
        console.print(f"\n{i}. [bold cyan]{verse.book} {verse.chapter}:{verse.verse}[/bold cyan]")
        # Highlight the search term
        highlighted_text = verse.text.replace(
            query, f"[bold yellow]{query}[/bold yellow]"
        )
        console.print(f"   {highlighted_text}")
    
    if len(results) > 10:
        console.print(f"\n[dim]... and {len(results) - 10} more results[/dim]")


@cli.command()
@click.pass_context
def stats(ctx):
    """Show overall statistics."""
    agent = ctx.obj['agent']
    
    if not agent.session_results:
        console.print("[yellow]No session data available. Run an interactive session first.[/yellow]")
        return
    
    overall_stats = agent.get_overall_stats()
    print_stats(overall_stats, "Overall Statistics")


@cli.command()
@click.pass_context
def list_books(ctx):
    """List available biblical books."""
    agent = ctx.obj['agent']
    
    # Initialize if not already done
    if not agent.bible_manager._loaded:
        with console.status("[bold green]Loading biblical data..."):
            try:
                agent.bible_manager.load_data()
            except FileNotFoundError:
                console.print("[red]Biblical data not available. Please check data directory.[/red]")
                return
    
    books = agent.list_available_books()
    
    if not books:
        console.print("[yellow]No biblical books available.[/yellow]")
        return
    
    console.print(f"\n[bold green]Available Books ({len(books)}):[/bold green]")
    for book in sorted(books):
        console.print(f"  • {book.title()}")


@cli.command()
@click.option('--type', 'prompt_type', type=click.Choice([t.value for t in PromptType]), help='Filter by prompt type')
@click.option('--difficulty', type=click.Choice(['easy', 'medium', 'hard']), help='Filter by difficulty')
@click.option('--book', help='Filter by book')
@click.pass_context
def list_prompts(ctx, prompt_type, difficulty, book):
    """List available prompts."""
    agent = ctx.obj['agent']
    
    # Initialize if not already done
    if not agent.prompts_manager._loaded:
        with console.status("[bold green]Loading prompts..."):
            agent.prompts_manager.load_prompts()
    
    prompts = agent.prompts_manager.get_all_prompts()
    
    # Apply filters
    if prompt_type:
        prompts = [p for p in prompts if p.prompt_type.value == prompt_type]
    if difficulty:
        prompts = [p for p in prompts if p.difficulty == difficulty]
    if book:
        prompts = [p for p in prompts if p.book and p.book.lower() == book.lower()]
    
    if not prompts:
        console.print("[yellow]No prompts found matching the criteria.[/yellow]")
        return
    
    console.print(f"\n[bold green]Available Prompts ({len(prompts)}):[/bold green]")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("ID", style="cyan")
    table.add_column("Question", style="white")
    table.add_column("Type", style="blue")
    table.add_column("Reference", style="green")
    table.add_column("Difficulty", style="yellow")
    
    for prompt in prompts:
        table.add_row(
            prompt.id,
            prompt.text[:50] + ("..." if len(prompt.text) > 50 else ""),
            prompt.prompt_type.value,
            prompt.get_reference(),
            prompt.difficulty or "unknown"
        )
    
    console.print(table)


@cli.command()
@click.argument('book')
@click.argument('chapter', type=int)
@click.argument('verse', type=int)
@click.pass_context
def verse(ctx, book, chapter, verse):
    """Get a specific biblical verse."""
    agent = ctx.obj['agent']
    
    # Initialize if not already done
    if not agent.bible_manager._loaded:
        with console.status("[bold green]Loading biblical data..."):
            try:
                agent.bible_manager.load_data()
            except FileNotFoundError:
                console.print("[red]Biblical data not available. Please check data directory.[/red]")
                return
    
    verse_obj = agent.get_verse(book, chapter, verse)
    
    if not verse_obj:
        console.print(f"[red]Verse not found: {book} {chapter}:{verse}[/red]")
        return
    
    console.print(f"\n[bold cyan]{verse_obj.book} {verse_obj.chapter}:{verse_obj.verse}[/bold cyan]")
    console.print(f"{verse_obj.text}")


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == '__main__':
    main()