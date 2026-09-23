from graph import research_graph
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule

console = Console()


def main():
    console.print(Rule("[bold blue]Research Agent[/bold blue]"))
    topic = input("\nEnter research topic: ").strip()

    if not topic:
        console.print("[red]No topic provided. Exiting.[/red]")
        return

    console.print(f"\n[bold cyan]Starting research on:[/bold cyan] {topic}\n")

    result = research_graph.invoke({
        "topic": topic,
        "sub_queries": [],
        "search_results": "",
        "scraped_content": "",
        "sources": [],
        "report": "",
        "critique": "",
        "score": 0,
        "iterations": 0,
        "chart_data": {},
    })

    # ── Final Report ───────────────────────────────────────────────────────────
    console.print(Rule("[bold green]Final Report[/bold green]"))
    console.print(Markdown(result["report"]))

    # ── Critique ───────────────────────────────────────────────────────────────
    console.print(Rule("[bold yellow]Critic Review[/bold yellow]"))
    console.print(Panel(result["critique"], border_style="yellow"))

    # ── Summary ────────────────────────────────────────────────────────────────
    console.print(
        f"\n[bold]Completed in[/bold] {result['iterations']} iteration(s) "
        f"| Final score: [bold green]{result['score']}/10[/bold green]"
    )


if __name__ == "__main__":
    main()
