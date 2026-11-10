import typer
import logging
import sys
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import track

# Налаштування логування (діагностика йде в stderr)
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger("findex")

app = typer.Typer(help="Findex Search Engine CLI")
console = Console()

# Тут будуть імпорти ваших модулів
from .index import InvertedIndex
from .storage import save_pickle, load_pickle
from .models import Index
from .search import search


@app.callback()
def main(
        verbose: int = typer.Option(0, "--verbose", "-v", count=True, help="Increase verbosity (-v, -vv)")
):
    if verbose == 1:
        logging.getLogger().setLevel(logging.INFO)
    elif verbose >= 2:
        logging.getLogger().setLevel(logging.DEBUG)


@app.command()
def index(
        data_dir: Path = typer.Argument(..., help="Directory with text files"),
        out: Path = typer.Option(Path("index.bin"), "--out", "-o", help="Output index file")
):
    """Build the inverted index from a directory of text files."""
    console.print(f"[bold blue]Building index from {data_dir}...[/bold blue]")

    idx = InvertedIndex()
    # Функція track з rich створює смугу прогресу
    try:
        idx.build(data_dir)
        save_pickle(idx, out)
        console.print(f"[bold green]Index saved to {out}[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def search_cmd(
        index_file: Path = typer.Argument(..., help="Path to index file"),
        query: str = typer.Argument(..., help="Search query"),
        scorer: str = typer.Option("tfidf", "--scorer", help="Ranking algorithm (tfidf or bm25)"),
        json_out: bool = typer.Option(False, "--json", help="Output results as JSON")
):
    """Search the index with a query."""
    if not index_file.exists():
        console.print(f"[bold red]Error: Index file '{index_file}' not found.[/bold red]")
        raise typer.Exit(code=1)

    try:
        data = load_pickle(index_file)
        idx = Index(postings=data['postings'], doc_meta=data['doc_meta'])

        # Завантаження корпусу для сніпетів
        corpus_dict = {}
        data_dir = Path("data")
        if data_dir.exists():
            from .iterators import iter_documents
            for i, text in enumerate(iter_documents(data_dir)):
                corpus_dict[i] = text

        results = search(idx, query, scorer_type=scorer, corpus_dict=corpus_dict)

        if json_out:
            # Вивід у stdout для перенаправлення
            output = [{"doc_id": r.doc_id, "score": r.score, "snippet": r.snippet} for r in results]
            typer.echo(json.dumps(output))
        else:
            if not results:
                console.print("[yellow]No results found.[/yellow]")
                return

            table = Table(title=f"Search Results for '{query}' ({scorer})")
            table.add_column("Doc ID", style="cyan")
            table.add_column("Score", style="magenta")
            table.add_column("Snippet", style="green")

            for r in results:
                table.add_row(str(r.doc_id), str(r.score), r.snippet)
            console.print(table)

    except Exception as e:
        console.print(f"[bold red]Error during search: {e}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def stats(index_file: Path = typer.Argument(..., help="Path to index file")):
    """Show statistics about the index."""
    if not index_file.exists():
        console.print(f"[bold red]Error: Index file '{index_file}' not found.[/bold red]")
        raise typer.Exit(code=1)

    data = load_pickle(index_file)
    idx = Index(postings=data['postings'], doc_meta=data['doc_meta'])

    console.print(f"[bold]Index Statistics[/bold]")
    console.print(f"Documents: {idx.num_docs}")
    console.print(f"Unique Terms: {len(idx)}")
    console.print(f"Avg Doc Length: {idx.avg_doc_length:.2f}")


if __name__ == "__main__":
    app()