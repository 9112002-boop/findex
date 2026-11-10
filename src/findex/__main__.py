import asyncio
import json
import logging
import os
import sys
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from .index import InvertedIndex, build_partial
from .models import Index
from .search import search
from .storage import load_pickle, save_pickle

# Налаштування логування (діагностика йде в stderr)
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger("findex")

app = typer.Typer(help="Findex Search Engine CLI")
console = Console()


@app.callback()
def main(
        verbose: int = typer.Option(0, "--verbose", "-v", count=True, help="Increase verbosity (-v, -vv)")
) -> None:
    if verbose == 1:
        logging.getLogger().setLevel(logging.INFO)
    elif verbose >= 2:
        logging.getLogger().setLevel(logging.DEBUG)


@app.command()
def index(
        data_dir: Path = typer.Argument(..., help="Directory with text files"),
        out: Path = typer.Option(Path("index.bin"), "--out", "-o", help="Output index file"),
        workers: int = typer.Option(1, "--workers", "-w", help="Number of workers"),
        executor: str = typer.Option("serial", "--executor", "-e", help="Executor type: serial, threads, processes")
) -> None:
    """Build the inverted index from a directory of text files."""
    console.print(f"[bold blue]Building index from {data_dir}...[/bold blue]")

    files = sorted(data_dir.glob("*.txt"))
    if not files:
        console.print("[bold red]Error: No .txt files found in the directory.[/bold red]")
        raise typer.Exit(code=1)

    # Розбиваємо файли на частини для кожного воркера
    num_workers = workers if workers > 0 else os.cpu_count() or 1
    chunk_size = (len(files) + num_workers - 1) // num_workers
    chunks = [files[i:i + chunk_size] for i in range(0, len(files), chunk_size)]

    partials = []
    try:
        if executor == "serial":
            for i, chunk in enumerate(chunks):
                partials.append(build_partial(chunk, start_doc_id=i * chunk_size))
        elif executor == "threads":
            with ThreadPoolExecutor(max_workers=num_workers) as pool:
                futures = [pool.submit(build_partial, chunk, i * chunk_size) for i, chunk in enumerate(chunks)]
                partials = [f.result() for f in futures]
        elif executor == "processes":
            with ProcessPoolExecutor(max_workers=num_workers) as pool:
                futures = [pool.submit(build_partial, chunk, i * chunk_size) for i, chunk in enumerate(chunks)]
                partials = [f.result() for f in futures]
        else:
            console.print(f"[bold red]Error: Unknown executor '{executor}'[/bold red]")
            raise typer.Exit(code=1)

        # Зливаємо результати
        final_index = InvertedIndex.merge(partials)
        save_pickle(final_index, out)
        console.print(f"[bold green]Index saved to {out}[/bold green]")

    except Exception as e:
        console.print(f"[bold red]Error during indexing: {e}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def search_cmd(
        index_file: Path = typer.Argument(..., help="Path to index file"),
        query: str = typer.Argument(..., help="Search query"),
        scorer: str = typer.Option("tfidf", "--scorer", help="Ranking algorithm (tfidf or bm25)"),
        json_out: bool = typer.Option(False, "--json", help="Output results as JSON")
) -> None:
    """Search the index with a query."""
    if not index_file.exists():
        console.print(f"[bold red]Error: Index file '{index_file}' not found.[/bold red]")
        raise typer.Exit(code=1)

    try:
        data = load_pickle(index_file)
        idx = Index(postings=data['postings'], doc_meta=data['doc_meta'])

        corpus_dict = {}
        data_dir = Path("data")
        if data_dir.exists():
            from .iterators import iter_documents
            for i, text in enumerate(iter_documents(data_dir)):
                corpus_dict[i] = text

        results = search(idx, query, scorer_type=scorer, corpus_dict=corpus_dict)

        if json_out:
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
def stats(index_file: Path = typer.Argument(..., help="Path to index file")) -> None:
    """Show statistics about the index."""
    if not index_file.exists():
        console.print(f"[bold red]Error: Index file '{index_file}' not found.[/bold red]")
        raise typer.Exit(code=1)

    data = load_pickle(index_file)
    idx = Index(postings=data['postings'], doc_meta=data['doc_meta'])

    console.print("[bold]Index Statistics[/bold]")
    console.print(f"Documents: {idx.num_docs}")
    console.print(f"Unique Terms: {len(idx)}")
    console.print(f"Avg Doc Length: {idx.avg_doc_length:.2f}")


@app.command()
def crawl(
        start_url: str = typer.Argument(..., help="Starting URL to crawl"),
        max_pages: int = typer.Option(200, "--max-pages", "-m", help="Maximum number of pages to crawl"),
        concurrency: int = typer.Option(5, "--concurrency", "-c", help="Number of concurrent requests"),
        out: Path = typer.Option(Path("crawl.jsonl"), "--out", "-o", help="Output JSONL file")
) -> None:
    """Asynchronously crawl a website and save results to JSONL."""
    from .crawler import crawl as run_crawl

    console.print(f"[bold blue]Starting async crawl of {start_url}[/bold blue]")
    console.print(f"Max pages: {max_pages}, Concurrency: {concurrency}")

    try:
        # Запускаємо асинхронний цикл подій
        asyncio.run(run_crawl(start_url, max_pages, concurrency, out))
        console.print(f"[bold green]Crawl complete. Results saved to {out}[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Crawl failed: {e}[/bold red]")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()