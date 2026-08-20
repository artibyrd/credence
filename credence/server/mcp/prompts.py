"""FastMCP Prompt Template Registrations for Credence."""

from __future__ import annotations

import logging

from mcp.server.mcpserver import MCPServer

logger = logging.getLogger("credence.server.mcp.prompts")


def _register_prompts(server: MCPServer) -> None:
    """Register FastMCP prompt templates."""

    @server.prompt(name="audit_article_prompt", description="Interactive prompt template for auditing an article.")
    def audit_article_prompt(url: str) -> str:
        return (
            f"Please conduct an epistemic trust audit of the following webpage URL:\n"
            f"Target URL: {url}\n\n"
            f"Use the `credence_check_url` tool to capture and evaluate the content against "
            f"SPJ journalistic ethics, logical fallacies, and deceptive patterns."
        )

    @server.prompt(
        name="explain_audit_report_prompt",
        description="Interactive prompt template instructing an AI agent to explain an epistemic audit report to a human reader in empathetic, plain language.",
    )
    def explain_audit_report_prompt(identifier: str) -> str:
        return (
            f"Please inspect and explain the Credence epistemic audit report for identifier: {identifier}\n\n"
            f"1. Fetch the report using `credence_get_audit(identifier='{identifier}', format='human')`.\n"
            f"2. Summarize the verdict, suspicion score, and confidence level in simple, empathetic terms.\n"
            f"3. Explain each detected violation (if any) with its quoted excerpt and why it was flagged.\n"
            f"4. Provide constructive guidance on how the reader can independently verify the assertions."
        )

    @server.prompt(
        name="fallacy_review_prompt",
        description="Structured prompt template for auditing argumentative text for formal and informal logical fallacies.",
    )
    def fallacy_review_prompt(text: str) -> str:
        return (
            f"Please analyze the following argumentative passage against the IEP Logical Fallacies taxonomy:\n\n"
            f"---\n{text}\n---\n\n"
            f"Use the `credence_evaluate_text` tool to detect fallacies (such as Ad Hominem, False Dilemma, "
            f"Post Hoc Ergo Propter Hoc, or Bandwagon appeals) and extract verbatim grounded citations."
        )

    @server.prompt(
        name="dark_pattern_review_prompt",
        description="Prompt template for reviewing user onboarding flows or e-commerce pages for deceptive UI patterns.",
    )
    def dark_pattern_review_prompt(url: str) -> str:
        return (
            f"Please perform a deceptive design audit on this target URL:\n"
            f"Target URL: {url}\n\n"
            f"Use the `credence_check_url` tool to inspect the rendered DOM for confirmshaming, fake urgency countdowns, "
            f"pre-selected options, disguised advertisements, and hidden recurring subscription terms."
        )
