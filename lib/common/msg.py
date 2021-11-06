from rich import print as rprint
from rich.console import Console
from rich.theme import Theme
from rich.highlighter import RegexHighlighter

def err(msg: str):
    rprint(f"[bold red]error: {msg}[/]")

def warn(msg: str):
    rprint(f"[bold yellow]warning: {msg}[/]")

def info(msg: str):
    print(msg)



class DfHighlighter(RegexHighlighter):
    base_style = "df."
    highlights = [
        r"(?P<neg>(-[0-9]+\.[0-9]+))",
        #r"(?P<number>([0-9]+\.[0-9]+))",
    ]


def print_hi_negatives(s: str):
    console = Console(highlighter=DfHighlighter(), theme=Theme({
            "df.neg": "bold red",
            "df.number": "bold cyan",
        }))
    console.print(s)
