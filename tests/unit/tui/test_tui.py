"""Unit tests for the Credence Textual TUI Application."""

import pytest
from textual.coordinate import Coordinate
from textual.widgets import DataTable
from textual.widgets.data_table import RowKey

from credence.tui.app import CredenceApp
from credence.tui.screens.info_modal import InfoModalScreen


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
        assert app.query_one("#leaderboard_table") is not None
        assert app.query_one("#merit_panel") is not None

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

        # Test keybindings 1-9
        for key in ["1", "2", "3", "4", "5", "6", "7", "8", "9"]:
            await pilot.press(key)
            await pilot.pause()

        # Switch back to Inspector
        await pilot.press("1")
        await pilot.pause()

        # Test 3-tier epistemic lensing cycling (v)
        assert app._lens_mode == 1
        await pilot.press("v")
        await pilot.pause()
        assert app._lens_mode == 2
        await pilot.press("v")
        await pilot.pause()
        assert app._lens_mode == 3
        await pilot.press("v")
        await pilot.pause()
        assert app._lens_mode == 1

        # Test Surprise Me random audit cycling (r)
        initial_url = app._current_item["url"]
        await pilot.press("r")
        await pilot.pause()
        assert app._current_item["url"] != initial_url

        # Test selecting a history row
        hist_table = app.query_one("#history_table", DataTable)
        hist_table.cursor_coordinate = Coordinate(0, 0)
        app.on_data_table_row_selected(DataTable.RowSelected(hist_table, 0, RowKey("0")))
        await pilot.pause()

        # Test selecting a publisher dossier row
        app.action_switch_to_leaderboard()
        await pilot.pause()
        lb_table = app.query_one("#leaderboard_table", DataTable)
        lb_table.cursor_coordinate = Coordinate(1, 0)
        app.on_data_table_row_selected(DataTable.RowSelected(lb_table, 1, RowKey("1")))
        await pilot.pause()

        # Test refresh data action
        await app.action_refresh_data()
        await pilot.pause()

        # Test opening in-terminal topic & invariant modal (? / i)
        app.action_open_info_modal()
        await pilot.pause()
        assert isinstance(app.screen, InfoModalScreen)
        await pilot.press("escape")
        await pilot.pause()


@pytest.mark.unit
def test_tui_taxonomy_tree_population() -> None:
    """Verify populate_taxonomy_tree generates 3-tier nodes and RFC status badges."""
    from textual.widgets import Tree
    from credence.tui.widgets.taxonomy_tree import populate_taxonomy_tree

    tree = Tree("Root")
    populate_taxonomy_tree(tree)
    assert tree.root.label is not None
    assert "Epistemic Standards" in str(tree.root.label)
    assert len(tree.root.children) == 3  # Tier 0, Tier 1, Tier 2
