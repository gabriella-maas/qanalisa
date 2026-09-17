from __future__ import annotations

from pathlib import Path
from time import perf_counter

import typer

from qanalisa.ai.claude_cli_provider import ClaudeCliProvider
from qanalisa.analysis.bug_generator import BugGenerator
from qanalisa.analysis.pipeline import AnalysisPipeline
from qanalisa.analysis.scenario_expander import ScenarioExpander, ScenarioNotFoundError
from qanalisa.config.settings import Settings
from qanalisa.jira.client import JiraClient, JiraError
from qanalisa.knowledge.loader import KnowledgeLoader
from qanalisa.knowledge.matcher import KnowledgeMatcher
from qanalisa.reports.markdown import render_markdown
from qanalisa.storage.workspace import Workspace

app = typer.Typer(help="QAnalisa — Entenda a story. Mapeie o risco. Teste melhor.")



def _format_elapsed(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    remainder = seconds - minutes * 60
    return f"{minutes}m{remainder:04.1f}s"


def _analysis_progress(stage: str, state: str, elapsed: float | None) -> None:
    if stage == "story" and state == "start":
        typer.echo("⠋ Interpretando requisito...")
    elif stage == "story" and state == "done":
        typer.echo(f"✓ Requisito analisado — {_format_elapsed(elapsed or 0.0)}")
    elif stage == "plan" and state == "start":
        typer.echo("⠋ Analisando impacto e planejando testes...")
    elif stage == "plan" and state == "done":
        typer.echo(f"✓ Plano de testes gerado — {_format_elapsed(elapsed or 0.0)}")


def _knowledge_root() -> Path:
    return Path(__file__).resolve().parents[2] / "knowledge" / "vrsuper"



def _build_provider(settings: Settings) -> ClaudeCliProvider:
    return ClaudeCliProvider(
        command=settings.claude_command,
        model=settings.claude_model,
        timeout_seconds=settings.claude_timeout_seconds,
    )


def _print_detailed_scenario(detailed) -> None:
    typer.echo(f"{detailed.id} — {detailed.title}")
    typer.echo(f"Prioridade: {detailed.priority}")
    typer.echo(f"Objetivo: {detailed.objective}")
    typer.echo("Pré-condições:")
    if detailed.preconditions:
        for item in detailed.preconditions:
            typer.echo(f"- {item}")
    else:
        typer.echo("- Nenhuma pré-condição específica identificada.")
    typer.echo("Passos:")
    for index, step in enumerate(detailed.steps, start=1):
        typer.echo(f"{index}. {step}")
    typer.echo(f"Resultado esperado: {detailed.expected_result}")
    if detailed.related_risks:
        typer.echo("Riscos relacionados:")
        for risk in detailed.related_risks:
            typer.echo(f"- {risk}")



def _print_full_bug(report) -> None:
    typer.echo(report.title)
    typer.echo("\nPré-condições")
    for item in report.preconditions:
        typer.echo(f"- {item}")
    typer.echo("\nPassos para reproduzir")
    for index, step in enumerate(report.steps, start=1):
        typer.echo(f"{index}. {step}")
    typer.echo(f"\nResultado atual\n{report.actual_result}")
    typer.echo(f"\nResultado esperado\n{report.expected_result}")
    typer.echo("\nEvidências")
    for item in report.evidence:
        typer.echo(f"- {item}")
    typer.echo(f"\nImpacto\n{report.impact}")


def _run_bug(issue_key: str, *, full: bool) -> None:
    issue_key = issue_key.upper()
    workspace = Workspace(Path.cwd() / ".qa")
    issue = workspace.load_story(issue_key)
    analysis = workspace.load_analysis(issue_key)
    if issue is None or analysis is None:
        typer.secho(
            f"Contexto de {issue_key} não encontrado. Execute qanalisa {issue_key} primeiro.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    defect = typer.prompt("Descreva o problema encontrado").strip()
    if not defect:
        typer.secho("A descrição do problema não pode estar vazia.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    settings = Settings()
    provider = _build_provider(settings)
    for warning in provider.preflight():
        typer.secho(f"Aviso: {warning}", fg=typer.colors.YELLOW)

    generator = BugGenerator(provider)
    if full:
        report = generator.generate_full(issue, analysis, defect)
        workspace.save_bug(issue_key, report, full=True)
        _print_full_bug(report)
    else:
        report = generator.generate_short(issue, analysis, defect)
        workspace.save_bug(issue_key, report, full=False)
        typer.echo(report.text)

def _run_scenario(issue_key: str, scenario_id: str) -> None:
    workspace = Workspace(Path.cwd() / ".qa")
    issue = workspace.load_story(issue_key)
    analysis = workspace.load_analysis(issue_key)
    if issue is None or analysis is None:
        typer.secho(
            f"Contexto de {issue_key.upper()} não encontrado. Execute qanalisa {issue_key.upper()} primeiro.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    settings = Settings()
    provider = _build_provider(settings)
    for warning in provider.preflight():
        typer.secho(f"Aviso: {warning}", fg=typer.colors.YELLOW)
    try:
        detailed = ScenarioExpander(provider).expand(issue, analysis, scenario_id)
    except ScenarioNotFoundError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc
    _print_detailed_scenario(detailed)

def _run_analysis(issue_key: str, *, reanalyze: bool) -> None:
    issue_key = issue_key.upper()
    workspace = Workspace(Path.cwd() / ".qa")
    total_started = perf_counter()

    if not reanalyze:
        cached_story = workspace.load_story(issue_key)
        cached_analysis = workspace.load_analysis(issue_key)
        if cached_story is not None and cached_analysis is not None:
            markdown = render_markdown(cached_story, cached_analysis)
            path = workspace.save_markdown(issue_key, markdown)
            typer.echo(f"QAnalisa: análise carregada do cache para {issue_key}.")
            typer.echo(str(path))
            return

    settings = Settings()
    provider = _build_provider(settings)
    for warning in provider.preflight():
        typer.secho(f"Aviso: {warning}", fg=typer.colors.YELLOW)

    try:
        issue = JiraClient(
            base_url=settings.jira_base_url,
            email=settings.jira_email,
            token=settings.jira_api_token,
        ).get_issue(issue_key)
    except JiraError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    workspace.save_story(issue)
    typer.echo("✓ Story carregada do Jira")
    knowledge = KnowledgeLoader(_knowledge_root()).load()
    match = KnowledgeMatcher(knowledge).match(f"{issue.title}\n{issue.description}")
    if match.module:
        matched = match.module + (f" > {match.feature}" if match.feature else "")
        typer.echo(f"✓ Módulo identificado: {matched}")
    else:
        typer.echo("? Nenhum módulo específico identificado na base VRSuper")
    analysis = AnalysisPipeline(
        provider,
        provider_name=settings.ai_provider,
        model=settings.claude_model,
    ).analyze(
        issue,
        match,
        knowledge_version=knowledge.version,
        progress=_analysis_progress,
    )
    workspace.save_analysis(issue.key, analysis)
    markdown = render_markdown(issue, analysis)
    path = workspace.save_markdown(issue.key, markdown)

    typer.echo(f"QAnalisa: {issue.key} — {issue.title}")
    typer.echo(f"Cenários: {len(analysis.tests)} | Negativos/borda: {len(analysis.negative_tests)}")
    typer.echo(f"Relatório: {path}")
    typer.echo(f"✓ Concluído em {_format_elapsed(perf_counter() - total_started)}")


@app.command()
def main(
    target: str | None = typer.Argument(None, help="Chave da tarefa Jira, por exemplo FN-1234"),
    second: str | None = typer.Argument(None, hidden=True),
    reanalyze: bool = typer.Option(False, "--reanalyze", help="Ignora o cache e gera uma nova análise."),
    test_id: str | None = typer.Option(None, "--test", help="Detalha um cenário já gerado, por exemplo CT07."),
    full: bool = typer.Option(False, "--full", help="Gera bug report completo no modo bug."),
) -> None:
    """QAnalisa — Entenda a story. Mapeie o risco. Teste melhor."""
    if not target:
        typer.echo("Informe uma tarefa, por exemplo: qanalisa FN-1234")
        raise typer.Exit(code=2)
    if target.casefold() == "bug":
        if not second:
            typer.echo("Informe a tarefa: qanalisa bug FN-1234", err=True)
            raise typer.Exit(code=2)
        _run_bug(second, full=full)
        return
    if second is not None:
        typer.echo("Argumentos adicionais não são suportados para análise de tarefa.", err=True)
        raise typer.Exit(code=2)
    if full:
        typer.echo("--full só pode ser usado com qanalisa bug FN-1234.", err=True)
        raise typer.Exit(code=2)
    if test_id:
        _run_scenario(target.upper(), test_id.upper())
        return
    _run_analysis(target, reanalyze=reanalyze)


if __name__ == "__main__":
    app()
