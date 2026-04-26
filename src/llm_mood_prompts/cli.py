"""llm-mood-prompts CLI.

Skills are hand-authored SKILL.md files in the repo's skills/ directory.
This CLI just copies them into ~/.claude/skills/ so Claude Code picks
them up. No State abstraction, no rendering — the markdown is the
deliverable.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from importlib.resources import as_file, files
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

DEFAULT_SKILLS_ROOT = Path.home() / ".claude" / "skills"
DEFAULT_JOURNAL_PATH = Path.home() / ".claude" / "llm-mood-prompts-journal.jsonl"

console = Console()


def _bundled_skills_dir() -> Path:
    """Locate the bundled skills/ directory.

    Two layouts to support:
    - Wheel install: skills live at `llm_mood_prompts/skills/` via the hatch
      force-include in pyproject.toml.
    - Editable install: force-include doesn't apply, so the skills are
      still at `<repo>/skills/`. Resolve relative to the source file.
    """
    resource = files("llm_mood_prompts") / "skills"
    with as_file(resource) as path:
        wheel_path = Path(path)
    if wheel_path.is_dir():
        return wheel_path

    # Editable-install fallback: <repo>/skills next to src/llm_mood_prompts
    repo_root = Path(__file__).resolve().parent.parent.parent
    editable_path = repo_root / "skills"
    if editable_path.is_dir():
        return editable_path

    raise click.ClickException(
        f"Bundled skills/ directory not found. Looked at {wheel_path} and {editable_path}."
    )


def _iter_skill_dirs(skills_src: Path) -> list[Path]:
    return sorted(p for p in skills_src.iterdir() if p.is_dir() and (p / "SKILL.md").is_file())


def _journal(action: str, payload: dict, journal_path: Path) -> None:
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {"ts": datetime.now(timezone.utc).isoformat(), "action": action, **payload}
    with journal_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


@click.group()
def cli() -> None:
    """Inject naturalistic state primers into Claude Code as skills."""


@cli.command()
@click.option(
    "--skills-root",
    type=click.Path(file_okay=False, path_type=Path),
    default=DEFAULT_SKILLS_ROOT,
    show_default=True,
)
@click.option(
    "--name",
    "name_filter",
    type=str,
    default=None,
    help="Install only this skill by name. Default: all.",
)
def install(skills_root: Path, name_filter: str | None) -> None:
    """Copy bundled skills into ~/.claude/skills/."""
    src = _bundled_skills_dir()
    skill_dirs = _iter_skill_dirs(src)
    if name_filter:
        skill_dirs = [d for d in skill_dirs if d.name == name_filter]
        if not skill_dirs:
            raise click.ClickException(f"No skill named {name_filter!r} found in bundle.")

    skills_root.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for skill_dir in skill_dirs:
        dest = skills_root / skill_dir.name
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copy2(skill_dir / "SKILL.md", dest / "SKILL.md")
        written.append(skill_dir.name)

    _journal("install", {"installed": written, "skills_root": str(skills_root)}, DEFAULT_JOURNAL_PATH)
    console.print(
        f"[green]Installed[/green] {len(written)} skill(s) into [bold]{skills_root}[/bold]:"
    )
    for name in written:
        console.print(f"  /{name}")


@cli.command(name="list")
def list_skills() -> None:
    """List all bundled skills (what `install` would copy)."""
    src = _bundled_skills_dir()
    skill_dirs = _iter_skill_dirs(src)

    table = Table(show_lines=False)
    table.add_column("Skill", style="bold cyan")
    table.add_column("Body (first line)")

    for skill_dir in skill_dirs:
        body = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        first_prose_line = _first_prose_line(body)
        table.add_row(f"/{skill_dir.name}", first_prose_line)

    console.print(table)


def _first_prose_line(skill_md: str) -> str:
    in_frontmatter = False
    seen_frontmatter_open = False
    for raw in skill_md.splitlines():
        line = raw.rstrip()
        if line == "---":
            if not seen_frontmatter_open:
                in_frontmatter = True
                seen_frontmatter_open = True
                continue
            in_frontmatter = False
            continue
        if in_frontmatter or not line.strip():
            continue
        return line if len(line) <= 80 else line[:77] + "..."
    return ""


@cli.command()
@click.argument("name", type=str)
def preview(name: str) -> None:
    """Print what `/name` would inject."""
    src = _bundled_skills_dir()
    skill_path = src / name / "SKILL.md"
    if not skill_path.is_file():
        raise click.ClickException(f"No skill named {name!r}. Run `llm-mood-prompts list` to see options.")
    console.rule(f"[bold]/{name}[/bold]")
    console.print(skill_path.read_text(encoding="utf-8"))


@cli.command()
@click.option(
    "--journal-path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=DEFAULT_JOURNAL_PATH,
    show_default=True,
)
@click.option("--limit", type=int, default=10, show_default=True)
def journal(journal_path: Path, limit: int) -> None:
    """Show recent install history."""
    if not journal_path.exists():
        console.print(f"[yellow]No journal yet at {journal_path}.[/yellow]")
        return
    lines = journal_path.read_text(encoding="utf-8").splitlines()
    entries = [json.loads(line) for line in lines if line.strip()]
    for entry in entries[-limit:]:
        ts = entry.get("ts", "?")
        action = entry.get("action", "?")
        installed = entry.get("installed", [])
        console.print(f"[dim]{ts}[/dim]  {action}  [bold]{len(installed)}[/bold] skill(s)")


@cli.command()
@click.option(
    "--skills-root",
    type=click.Path(file_okay=False, path_type=Path),
    default=DEFAULT_SKILLS_ROOT,
    show_default=True,
)
@click.confirmation_option(prompt="This will delete every llm-mood-prompts skill directory. Proceed?")
def uninstall(skills_root: Path) -> None:
    """Remove all installed llm-mood-prompts skill directories."""
    src = _bundled_skills_dir()
    skill_dirs = _iter_skill_dirs(src)
    removed = 0
    for skill_dir in skill_dirs:
        target = skills_root / skill_dir.name
        if target.exists():
            shutil.rmtree(target)
            removed += 1
    _journal("uninstall", {"removed_count": removed, "skills_root": str(skills_root)}, DEFAULT_JOURNAL_PATH)
    console.print(f"[green]Removed[/green] {removed} skill director(ies).")


if __name__ == "__main__":
    cli()
