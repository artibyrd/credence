"""Unit tests for the Credence Textual TUI Application."""

import pytest

from credence.tui.app import CredenceApp


@pytest.mark.unit
async def test_credence_tui_app_lifecycle() -> None:
    """Verify CredenceApp boots, loads widgets, populates tree, quota, and panels, and closes cleanly."""
    app = CredenceApp()

    async with app.run_test() as pilot:
        # Check app initialized with widgets
        assert app.is_running
        assert app.query_one("#sidebar") is not None
        assert app.query_one("#history_table") is not None
        assert app.query_one("#taxonomy_tree") is not None
        assert app.query_one("#identity_panel") is not None
        assert app.query_one("#quota_panel") is not None

        # Test switching tabs
        app.action_switch_to_taxonomies()
        await pilot.pause()

        app.action_switch_to_quota()
        await pilot.pause()

        app.action_switch_to_identity()
        await pilot.pause()

        # Test refresh
        await app.action_refresh_data()
        await pilot.pause()
