"""Unit tests for the Credence Textual TUI Application."""

import pytest

from credence.tui.app import CredenceApp


@pytest.mark.unit
async def test_credence_tui_app_lifecycle() -> None:
    """Verify CredenceApp boots, loads widgets, switches all tabs via keys and actions, and executes sync."""
    app = CredenceApp()

    async with app.run_test() as pilot:
        # Check app initialized with widgets
        assert app.is_running
        assert app.query_one("#sidebar") is not None
        assert app.query_one("#history_table") is not None
        assert app.query_one("#taxonomy_tree") is not None
        assert app.query_one("#subjects_tree") is not None
        assert app.query_one("#feeds_table") is not None
        assert app.query_one("#identity_panel") is not None
        assert app.query_one("#quota_panel") is not None
        assert app.query_one("#ops_panel") is not None
        assert app.query_one("#mesh_panel") is not None

        # Test switching tabs via action handlers
        app.action_switch_to_inspector()
        await pilot.pause()

        app.action_switch_to_taxonomies()
        await pilot.pause()

        app.action_switch_to_subjects()
        await pilot.pause()

        app.action_switch_to_feeds()
        await pilot.pause()

        app.action_switch_to_leaderboard()
        await pilot.pause()

        app.action_switch_to_quota()
        await pilot.pause()

        app.action_switch_to_identity()
        await pilot.pause()

        app.action_switch_to_ops()
        await pilot.pause()

        app.action_switch_to_mesh()
        await pilot.pause()

        # Test keybindings 1-9 and m
        await pilot.press("1")
        await pilot.pause()
        await pilot.press("2")
        await pilot.pause()
        await pilot.press("3")
        await pilot.pause()
        await pilot.press("4")
        await pilot.pause()
        await pilot.press("5")
        await pilot.pause()
        await pilot.press("6")
        await pilot.pause()
        await pilot.press("7")
        await pilot.pause()
        await pilot.press("8")
        await pilot.pause()
        await pilot.press("9")
        await pilot.pause()
        await pilot.press("m")
        await pilot.pause()

        # Test view mode cycling (v)
        assert app._view_mode == "rich"
        await pilot.press("v")
        await pilot.pause()
        assert app._view_mode == "compact"
        await pilot.press("v")
        await pilot.pause()
        assert app._view_mode == "raw"
        await pilot.press("v")
        await pilot.pause()
        assert app._view_mode == "rich"

        # Test random audit action / keybinding (r)
        await pilot.press("r")
        await pilot.pause()

        # Test refresh data action
        await app.action_refresh_data()
        await pilot.pause()

        # Test sync feeds action
        app.action_sync_feeds_action()
        await pilot.pause()
