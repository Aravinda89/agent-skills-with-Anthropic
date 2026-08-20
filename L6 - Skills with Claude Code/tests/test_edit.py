"""Tests for the edit command."""

import json

from task.commands import app
from task.storage import load_tasks


class TestEdit:
    """Test suite for edit command."""

    def test_edits_title(self, runner, sample_data):
        """Test changing a task title."""
        result = runner.invoke(app, ["edit", "1", "--title", "New title"])

        assert result.exit_code == 0
        tasks = load_tasks()
        assert tasks[0].title == "New title"
        assert tasks[0].priority.value == "low"

    def test_edits_priority(self, runner, sample_data):
        """Test changing a task priority."""
        result = runner.invoke(app, ["edit", "1", "--priority", "high"])

        assert result.exit_code == 0
        tasks = load_tasks()
        assert tasks[0].priority.value == "high"
        assert tasks[0].title == "First task"

    def test_edits_title_and_priority(self, runner, sample_data):
        """Test changing both fields at once."""
        result = runner.invoke(app, ["edit", "1", "-t", "Renamed", "-p", "medium"])

        assert result.exit_code == 0
        tasks = load_tasks()
        assert tasks[0].title == "Renamed"
        assert tasks[0].priority.value == "medium"

    def test_no_options_makes_no_edits(self, runner, sample_data):
        """Test that omitting options edits nothing."""
        result = runner.invoke(app, ["edit", "1"])

        assert result.exit_code == 0
        assert "no edits were done, specify title or priority" in result.output

        tasks = load_tasks()
        assert tasks[0].title == "First task"
        assert tasks[0].priority.value == "low"

    def test_displays_table_after_edit(self, runner, sample_data):
        """Test that the task table is shown after an edit."""
        result = runner.invoke(app, ["edit", "1", "--title", "Renamed"])

        assert result.exit_code == 0
        assert "Renamed" in result.output
        assert "Second task" in result.output
        assert "2 tasks" in result.output

    def test_priority_is_case_insensitive(self, runner, sample_data):
        """Test that priority accepts mixed case."""
        result = runner.invoke(app, ["edit", "1", "--priority", "HIGH"])

        assert result.exit_code == 0
        assert load_tasks()[0].priority.value == "high"

    def test_invalid_priority(self, runner, sample_data):
        """Test that an unknown priority shows an error."""
        result = runner.invoke(app, ["edit", "1", "--priority", "urgent"])

        assert result.exit_code == 2
        assert "Invalid priority: urgent" in result.output
        assert load_tasks()[0].priority.value == "low"

    def test_empty_title(self, runner, sample_data):
        """Test that a blank title shows an error."""
        result = runner.invoke(app, ["edit", "1", "--title", "   "])

        assert result.exit_code == 2
        assert "Title cannot be empty" in result.output
        assert load_tasks()[0].title == "First task"

    def test_title_is_stripped(self, runner, sample_data):
        """Test that surrounding whitespace is trimmed."""
        runner.invoke(app, ["edit", "1", "--title", "  Padded  "])

        assert load_tasks()[0].title == "Padded"

    def test_task_id_not_found(self, runner, sample_data):
        """Test that an out-of-range ID shows an error."""
        result = runner.invoke(app, ["edit", "999", "--title", "Nope"])

        assert result.exit_code == 2
        assert "Task 999 not found" in result.output

    def test_task_id_zero(self, runner, sample_data):
        """Test that ID 0 shows an error."""
        result = runner.invoke(app, ["edit", "0", "--title", "Nope"])

        assert result.exit_code == 2
        assert "Task ID must be positive" in result.output

    def test_edit_on_empty_storage(self, runner, temp_storage):
        """Test editing when no tasks exist."""
        result = runner.invoke(app, ["edit", "1", "--title", "Nope"])

        assert result.exit_code == 2
        assert "Task 1 not found" in result.output

    def test_preserves_other_fields(self, runner, sample_data):
        """Test that done and due_date survive an edit."""
        result = runner.invoke(app, ["edit", "2", "--title", "Renamed"])

        assert result.exit_code == 0
        task = load_tasks()[1]
        assert task.title == "Renamed"
        assert task.done is True
        assert task.due_date is not None

    def test_only_edits_specified_task(self, runner, sample_data):
        """Test that other tasks are untouched."""
        runner.invoke(app, ["edit", "1", "--title", "Renamed", "-p", "high"])

        tasks = load_tasks()
        assert tasks[1].title == "Second task"
        assert tasks[1].priority.value == "high"
        assert tasks[1].done is True

    # --- Success output ---------------------------------------------------

    def test_success_message_includes_new_title(self, runner, sample_data):
        """Test that the success message names the updated task."""
        result = runner.invoke(app, ["edit", "1", "--title", "New title"])

        assert result.exit_code == 0
        assert "Updated: New title" in result.output

    def test_success_message_uses_stripped_title(self, runner, sample_data):
        """Test that the success message shows the trimmed title."""
        result = runner.invoke(app, ["edit", "1", "--title", "  Padded  "])

        assert result.exit_code == 0
        assert "Updated: Padded" in result.output

    def test_success_message_on_priority_only_edit(self, runner, sample_data):
        """Test that a priority-only edit reports the existing title."""
        result = runner.invoke(app, ["edit", "1", "--priority", "high"])

        assert result.exit_code == 0
        assert "Updated: First task" in result.output

    # --- Short options ----------------------------------------------------

    def test_edits_title_with_short_option(self, runner, sample_data):
        """Test that -t sets the title on its own."""
        result = runner.invoke(app, ["edit", "1", "-t", "Short flag title"])

        assert result.exit_code == 0
        assert load_tasks()[0].title == "Short flag title"

    def test_edits_priority_with_short_option(self, runner, sample_data):
        """Test that -p sets the priority on its own."""
        result = runner.invoke(app, ["edit", "1", "-p", "medium"])

        assert result.exit_code == 0
        assert load_tasks()[0].priority.value == "medium"

    # --- No-option behaviour ----------------------------------------------

    def test_no_options_does_not_show_table(self, runner, sample_data):
        """Test that a no-op edit skips the task table."""
        result = runner.invoke(app, ["edit", "1"])

        assert result.exit_code == 0
        assert "Second task" not in result.output

    def test_no_options_skips_task_id_validation(self, runner, sample_data):
        """Test that the no-op check runs before ID validation."""
        # The command returns early, so an out-of-range ID is never reported.
        result = runner.invoke(app, ["edit", "999"])

        assert result.exit_code == 0
        assert "no edits were done, specify title or priority" in result.output
        assert "not found" not in result.output

    # --- Task ID validation -----------------------------------------------

    def test_negative_task_id(self, runner, sample_data):
        """Test that a negative ID shows an error."""
        # "--" ends option parsing so -1 is read as the TASK_ID argument.
        result = runner.invoke(app, ["edit", "--title", "Nope", "--", "-1"])

        assert result.exit_code == 2
        assert "Task ID must be positive" in result.output
        assert load_tasks()[0].title == "First task"

    def test_non_integer_task_id(self, runner, sample_data):
        """Test that a non-numeric ID is rejected by the parser."""
        result = runner.invoke(app, ["edit", "abc", "--title", "Nope"])

        assert result.exit_code == 2
        assert load_tasks()[0].title == "First task"

    def test_missing_title_value(self, runner, sample_data):
        """Test that --title without a value is a usage error."""
        result = runner.invoke(app, ["edit", "1", "--title"])

        assert result.exit_code == 2
        assert load_tasks()[0].title == "First task"

    def test_edits_last_task(self, runner, sample_data):
        """Test editing the highest valid ID (boundary case)."""
        result = runner.invoke(app, ["edit", "2", "--title", "Last renamed"])

        assert result.exit_code == 0
        assert load_tasks()[1].title == "Last renamed"

    # --- Value validation --------------------------------------------------

    def test_empty_string_title(self, runner, sample_data):
        """Test that an empty-string title shows an error."""
        result = runner.invoke(app, ["edit", "1", "--title", ""])

        assert result.exit_code == 2
        assert "Title cannot be empty" in result.output
        assert load_tasks()[0].title == "First task"

    def test_empty_priority(self, runner, sample_data):
        """Test that an empty-string priority shows an error."""
        result = runner.invoke(app, ["edit", "1", "-p", ""])

        assert result.exit_code == 2
        assert "Use low, medium, or high" in result.output
        assert load_tasks()[0].priority.value == "low"

    def test_task_id_checked_before_priority(self, runner, sample_data):
        """Test that a bad ID is reported ahead of a bad priority."""
        result = runner.invoke(app, ["edit", "999", "-p", "urgent"])

        assert result.exit_code == 2
        assert "Task 999 not found" in result.output
        assert "Invalid priority" not in result.output

    def test_title_checked_before_priority(self, runner, sample_data):
        """Test that a blank title is reported ahead of a bad priority."""
        result = runner.invoke(app, ["edit", "1", "-t", " ", "-p", "urgent"])

        assert result.exit_code == 2
        assert "Title cannot be empty" in result.output
        assert "Invalid priority" not in result.output

    def test_invalid_priority_does_not_apply_title(self, runner, sample_data):
        """Test that a rejected edit leaves the title unchanged."""
        result = runner.invoke(app, ["edit", "1", "-t", "Renamed", "-p", "urgent"])

        assert result.exit_code == 2
        assert load_tasks()[0].title == "First task"

    # --- Persistence -------------------------------------------------------

    def test_preserves_created_at(self, runner, temp_storage, sample_data):
        """Test that created_at survives an edit."""
        original = sample_data["tasks"][0]["created_at"]

        result = runner.invoke(app, ["edit", "1", "--title", "Renamed"])

        assert result.exit_code == 0
        data = json.loads(temp_storage.read_text())
        assert data["tasks"][0]["created_at"] == original

    def test_storage_keeps_schema_version(self, runner, temp_storage, sample_data):
        """Test that the version field is retained after an edit."""
        result = runner.invoke(app, ["edit", "1", "--title", "Renamed"])

        assert result.exit_code == 0
        data = json.loads(temp_storage.read_text())
        assert data["version"] == 1
        assert len(data["tasks"]) == 2

    def test_lowers_priority(self, runner, sample_data):
        """Test that priority can be downgraded."""
        result = runner.invoke(app, ["edit", "2", "--priority", "low"])

        assert result.exit_code == 0
        assert load_tasks()[1].priority.value == "low"

    def test_editing_done_task_preserves_done(self, runner, sample_data):
        """Test that editing a completed task keeps it completed."""
        result = runner.invoke(app, ["edit", "2", "--priority", "medium"])

        assert result.exit_code == 0
        task = load_tasks()[1]
        assert task.done is True
        assert task.priority.value == "medium"

    def test_does_not_add_or_remove_tasks(self, runner, sample_data):
        """Test that an edit keeps the task count stable."""
        result = runner.invoke(app, ["edit", "1", "--title", "Renamed"])

        assert result.exit_code == 0
        assert len(load_tasks()) == 2

    def test_sequential_edits_to_same_task(self, runner, sample_data):
        """Test that repeated edits accumulate."""
        runner.invoke(app, ["edit", "1", "--title", "First rename"])
        runner.invoke(app, ["edit", "1", "--priority", "high"])

        task = load_tasks()[0]
        assert task.title == "First rename"
        assert task.priority.value == "high"
