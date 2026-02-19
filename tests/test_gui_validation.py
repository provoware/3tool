import importlib
import sys

from PySide6 import QtCore

from core import launcher_checks


def _import_gui_module():
    return importlib.import_module("videobatch_gui")


def test_gui_runtime_reports_missing_libgl_if_unavailable(gui_runtime_error):
    if gui_runtime_error is None:
        result = launcher_checks.check_gui_runtime(sys.executable)
        assert result.ok
        return

    result = launcher_checks.check_gui_runtime(sys.executable)
    assert not result.ok
    assert "GUI-Import fehlgeschlagen" in result.detail
    assert "libGL.so.1" in result.detail or "libEGL.so.1" in result.detail
    assert result.fix_hint


def test_validate_image_fields_marks_invalid(
    request, gui_runtime_available, gui_runtime_error
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        assert (
            "libGL.so.1" in gui_runtime_error
            or "libEGL.so.1" in gui_runtime_error
        )
        return

    qtbot = request.getfixturevalue("qtbot")
    videobatch_gui = _import_gui_module()
    win = videobatch_gui.MainWindow()
    qtbot.addWidget(win)
    win.image_edit.setText("/tmp/not-existing-image.jpg")
    win.validate_image_fields()

    assert "#ffd6d6" in win.image_edit.styleSheet()
    assert "existiert nicht" in win.validation_msg.text()


def test_validate_audio_fields_marks_invalid(
    request, gui_runtime_available, gui_runtime_error
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        assert (
            "libGL.so.1" in gui_runtime_error
            or "libEGL.so.1" in gui_runtime_error
        )
        return

    qtbot = request.getfixturevalue("qtbot")
    videobatch_gui = _import_gui_module()
    win = videobatch_gui.MainWindow()
    qtbot.addWidget(win)
    win.audio_edit.setText("/tmp/not-existing-audio.mp3")
    win.validate_audio_fields()

    assert "#ffd6d6" in win.audio_edit.styleSheet()
    assert "existiert nicht" in win.validation_msg.text()


def test_dashboard_counts_are_clamped(
    request, gui_runtime_available, gui_runtime_error
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        assert (
            "libGL.so.1" in gui_runtime_error
            or "libEGL.so.1" in gui_runtime_error
        )
        return

    qtbot = request.getfixturevalue("qtbot")
    videobatch_gui = _import_gui_module()
    dashboard = videobatch_gui.InfoDashboard()
    qtbot.addWidget(dashboard)

    dashboard.set_counts(2, 5, -1)

    assert dashboard.total_label.text() == "2"
    assert dashboard.done_label.text() == "2"
    assert dashboard.err_label.text() == "0"


def test_dashboard_progress_is_limited_to_100(
    request, gui_runtime_available, gui_runtime_error
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        assert (
            "libGL.so.1" in gui_runtime_error
            or "libEGL.so.1" in gui_runtime_error
        )
        return

    qtbot = request.getfixturevalue("qtbot")
    videobatch_gui = _import_gui_module()
    dashboard = videobatch_gui.InfoDashboard()
    qtbot.addWidget(dashboard)

    dashboard.set_progress(160)

    assert dashboard.progress.value() == 100
    assert dashboard.progress_value.text() == "100%"


def test_dashboard_metric_cards_reflow_to_three_columns_on_large_width(
    request, gui_runtime_available, gui_runtime_error
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        assert (
            "libGL.so.1" in gui_runtime_error
            or "libEGL.so.1" in gui_runtime_error
        )
        return

    qtbot = request.getfixturevalue("qtbot")
    videobatch_gui = _import_gui_module()
    dashboard = videobatch_gui.InfoDashboard()
    qtbot.addWidget(dashboard)

    dashboard._reflow_metric_cards(1000)

    positions = []
    for idx in range(dashboard.cards_layout.count()):
        row, col, _, _ = dashboard.cards_layout.getItemPosition(idx)
        positions.append((row, col))
    used_columns = {col for _, col in positions}
    assert used_columns == {0, 1, 2}


def test_dashboard_metric_reflow_recovers_from_invalid_width(
    request, gui_runtime_available, gui_runtime_error
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        assert (
            "libGL.so.1" in gui_runtime_error
            or "libEGL.so.1" in gui_runtime_error
        )
        return

    qtbot = request.getfixturevalue("qtbot")
    videobatch_gui = _import_gui_module()
    dashboard = videobatch_gui.InfoDashboard()
    qtbot.addWidget(dashboard)

    dashboard._reflow_metric_cards("ungueltig")

    positions = []
    for idx in range(dashboard.cards_layout.count()):
        row, col, _, _ = dashboard.cards_layout.getItemPosition(idx)
        positions.append((row, col))
    used_columns = {col for _, col in positions}
    assert used_columns == {0}


def test_dashboard_metric_cards_adapt_to_font_size_changes(
    request, gui_runtime_available, gui_runtime_error
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        assert (
            "libGL.so.1" in gui_runtime_error
            or "libEGL.so.1" in gui_runtime_error
        )
        return

    qtbot = request.getfixturevalue("qtbot")
    videobatch_gui = _import_gui_module()
    dashboard = videobatch_gui.InfoDashboard()
    qtbot.addWidget(dashboard)

    old_height = dashboard._metric_cards[0].minimumHeight()
    font = dashboard.font()
    font.setPointSize(font.pointSize() + 6)
    dashboard.setFont(font)
    qtbot.wait(0)

    new_height = dashboard._metric_cards[0].minimumHeight()
    assert new_height >= old_height


def test_dashboard_selection_counts_update_metric_labels(
    request, gui_runtime_available, gui_runtime_error
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        assert (
            "libGL.so.1" in gui_runtime_error
            or "libEGL.so.1" in gui_runtime_error
        )
        return

    qtbot = request.getfixturevalue("qtbot")
    videobatch_gui = _import_gui_module()
    dashboard = videobatch_gui.InfoDashboard()
    qtbot.addWidget(dashboard)

    dashboard.set_selection_counts(5, 3)

    assert dashboard.selected_images_label.text() == "5"
    assert dashboard.selected_audios_label.text() == "3"


def test_action_buttons_reflow_to_two_columns_on_medium_width(
    request, gui_runtime_available, gui_runtime_error
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        assert (
            "libGL.so.1" in gui_runtime_error
            or "libEGL.so.1" in gui_runtime_error
        )
        return

    qtbot = request.getfixturevalue("qtbot")
    videobatch_gui = _import_gui_module()
    win = videobatch_gui.MainWindow()
    qtbot.addWidget(win)

    win._reflow_action_buttons(available_width=500)

    positions = []
    for idx in range(win.top_buttons_layout.count()):
        row, col, _, _ = win.top_buttons_layout.getItemPosition(idx)
        positions.append((row, col))
    used_columns = {col for _, col in positions}
    assert used_columns == {0, 1}


def test_action_buttons_reflow_uses_four_columns_on_large_width(
    request, gui_runtime_available, gui_runtime_error
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        assert (
            "libGL.so.1" in gui_runtime_error
            or "libEGL.so.1" in gui_runtime_error
        )
        return

    qtbot = request.getfixturevalue("qtbot")
    videobatch_gui = _import_gui_module()
    win = videobatch_gui.MainWindow()
    qtbot.addWidget(win)

    win._reflow_action_buttons(available_width=1400)

    positions = []
    for idx in range(win.top_buttons_layout.count()):
        row, col, _, _ = win.top_buttons_layout.getItemPosition(idx)
        positions.append((row, col))
    used_columns = {col for _, col in positions}
    assert used_columns == {0, 1, 2, 3}


def test_action_buttons_reflow_recovers_from_invalid_width_type(
    request, gui_runtime_available, gui_runtime_error
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        assert (
            "libGL.so.1" in gui_runtime_error
            or "libEGL.so.1" in gui_runtime_error
        )
        return

    qtbot = request.getfixturevalue("qtbot")
    videobatch_gui = _import_gui_module()
    win = videobatch_gui.MainWindow()
    qtbot.addWidget(win)

    win._reflow_action_buttons(available_width="ungueltig")

    positions = []
    for idx in range(win.top_buttons_layout.count()):
        row, col, _, _ = win.top_buttons_layout.getItemPosition(idx)
        positions.append((row, col))
    used_columns = {col for _, col in positions}
    assert used_columns == {0}
    assert "verfügbare Breite ist ungültig" in win.log_edit.toPlainText()


def test_action_buttons_reflow_to_single_column_on_small_width(
    request, gui_runtime_available, gui_runtime_error
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        assert (
            "libGL.so.1" in gui_runtime_error
            or "libEGL.so.1" in gui_runtime_error
        )
        return

    qtbot = request.getfixturevalue("qtbot")
    videobatch_gui = _import_gui_module()
    win = videobatch_gui.MainWindow()
    qtbot.addWidget(win)

    win._reflow_action_buttons(available_width=240)

    positions = []
    for idx in range(win.top_buttons_layout.count()):
        row, col, _, _ = win.top_buttons_layout.getItemPosition(idx)
        positions.append((row, col))
    used_columns = {col for _, col in positions}
    assert used_columns == {0}


def test_focus_change_keeps_workflow_geometry_stable(
    request, gui_runtime_available, gui_runtime_error
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        assert (
            "libGL.so.1" in gui_runtime_error
            or "libEGL.so.1" in gui_runtime_error
        )
        return

    qtbot = request.getfixturevalue("qtbot")
    videobatch_gui = _import_gui_module()
    win = videobatch_gui.MainWindow()
    qtbot.addWidget(win)
    win.show()
    qtbot.waitExposed(win)

    initial_column_sizes = list(win.workflow_columns.sizes())
    initial_active = win._active_section_name

    win._on_focus_changed(win.table, win.log_edit)

    after_focus_column_sizes = list(win.workflow_columns.sizes())
    assert after_focus_column_sizes == initial_column_sizes
    assert win._active_section_name == "Protokoll"
    assert win._active_section_name != initial_active

    win._request_workflow_rebalance(force=True)
    qtbot.wait(win.WORKFLOW_REBALANCE_DEBOUNCE_MS + 80)
    rebalanced_column_sizes = list(win.workflow_columns.sizes())
    assert any(
        abs(current - original) >= win.WORKFLOW_REBALANCE_THRESHOLD_PX
        for current, original in zip(
            rebalanced_column_sizes,
            initial_column_sizes,
        )
    )


def test_workflow_reflows_to_vertical_stack_on_small_width(
    request, gui_runtime_available, gui_runtime_error
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        assert (
            "libGL.so.1" in gui_runtime_error
            or "libEGL.so.1" in gui_runtime_error
        )
        return

    qtbot = request.getfixturevalue("qtbot")
    videobatch_gui = _import_gui_module()
    win = videobatch_gui.MainWindow()
    qtbot.addWidget(win)
    win.resize(820, 740)

    win._update_workflow_section_constraints()
    win._request_workflow_rebalance(force=True)
    qtbot.wait(win.WORKFLOW_REBALANCE_DEBOUNCE_MS + 80)

    assert win.workflow_columns.orientation() == videobatch_gui.Qt.Vertical
    assert all(
        section.minimumWidth() <= win.workflow_columns.width()
        for section in win._workflow_sections
    )


def test_workflow_min_size_clamps_for_large_font_profile(
    request, gui_runtime_available, gui_runtime_error
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        assert (
            "libGL.so.1" in gui_runtime_error
            or "libEGL.so.1" in gui_runtime_error
        )
        return

    qtbot = request.getfixturevalue("qtbot")
    videobatch_gui = _import_gui_module()
    win = videobatch_gui.MainWindow()
    qtbot.addWidget(win)
    win.resize(980, 760)
    win._set_font(34)

    win._update_workflow_section_constraints()
    min_width, min_height = win._compute_workflow_min_size()

    assert min_width <= win.workflow_columns.width()
    assert min_height <= win.workflow_columns.height()
    assert all(
        section.minimumWidth() == min_width
        for section in win._workflow_sections
    )
    assert all(
        section.minimumHeight() == min_height
        for section in win._workflow_sections
    )


def test_density_profile_changes_workflow_min_size(
    request, gui_runtime_available, gui_runtime_error
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        return

    qtbot = request.getfixturevalue("qtbot")
    videobatch_gui = _import_gui_module()
    win = videobatch_gui.MainWindow()
    qtbot.addWidget(win)
    win.resize(1100, 800)

    win.density_combo.setCurrentText("Kompakt")
    compact_width, compact_height = win._compute_workflow_min_size(
        density_multiplier=win.settings.value("ui/density_scale", 1.0, float)
    )

    win.density_combo.setCurrentText("Groß")
    large_width, large_height = win._compute_workflow_min_size(
        density_multiplier=win.settings.value("ui/density_scale", 1.0, float)
    )

    assert large_width >= compact_width
    assert large_height >= compact_height


def test_scaled_sizes_keep_total_and_positive(
    gui_runtime_available, gui_runtime_error
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        return

    videobatch_gui = _import_gui_module()
    sizes = videobatch_gui.MainWindow._scaled_sizes((35, 30, 35), 1000)

    assert len(sizes) == 3
    assert sum(sizes) == 1000
    assert all(size > 0 for size in sizes)


def test_resize_rebalance_respects_user_splitter_layout(
    request, gui_runtime_available, gui_runtime_error
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        assert (
            "libGL.so.1" in gui_runtime_error
            or "libEGL.so.1" in gui_runtime_error
        )
        return

    qtbot = request.getfixturevalue("qtbot")
    videobatch_gui = _import_gui_module()
    win = videobatch_gui.MainWindow()
    qtbot.addWidget(win)
    win.show()
    qtbot.waitExposed(win)

    custom_sizes = [500, 180, 250]
    win.workflow_columns.setSizes(custom_sizes)
    win._user_layout_touched = True

    win._request_workflow_rebalance(force=False)
    qtbot.wait(win.WORKFLOW_REBALANCE_DEBOUNCE_MS + 80)

    current_sizes = list(win.workflow_columns.sizes())
    assert all(
        abs(current - target) < win.WORKFLOW_REBALANCE_THRESHOLD_PX
        for current, target in zip(current_sizes, custom_sizes)
    )


def test_large_controls_enable_readability_mode_and_longer_tooltips(
    request, gui_runtime_available, gui_runtime_error
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        return

    qtbot = request.getfixturevalue("qtbot")
    videobatch_gui = _import_gui_module()
    win = videobatch_gui.MainWindow()
    qtbot.addWidget(win)

    win.large_controls_toggle.setChecked(False)
    assert win.property("readabilityMode") == "standard"

    win.large_controls_toggle.setChecked(True)

    assert win.property("readabilityMode") == "large"
    assert win.toolTipDuration() == 22000
    assert win.large_controls_toggle.toolTipDuration() == 22000


def test_large_controls_increase_action_and_row_sizes(
    request, gui_runtime_available, gui_runtime_error
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        return

    qtbot = request.getfixturevalue("qtbot")
    videobatch_gui = _import_gui_module()
    win = videobatch_gui.MainWindow()
    qtbot.addWidget(win)

    win.large_controls_toggle.setChecked(False)
    compact_button_heights = [
        btn.minimumHeight() for btn in win._action_buttons()
    ]
    compact_row_height = win.table.verticalHeader().defaultSectionSize()

    win.large_controls_toggle.setChecked(True)
    large_button_heights = [
        btn.minimumHeight() for btn in win._action_buttons()
    ]
    large_row_height = win.table.verticalHeader().defaultSectionSize()

    assert min(large_button_heights) >= min(compact_button_heights)
    assert large_row_height > compact_row_height


def test_splitter_state_is_saved_and_restored_per_splitter(
    request, gui_runtime_available, gui_runtime_error
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        assert (
            "libGL.so.1" in gui_runtime_error
            or "libEGL.so.1" in gui_runtime_error
        )
        return

    qtbot = request.getfixturevalue("qtbot")
    videobatch_gui = _import_gui_module()
    win = videobatch_gui.MainWindow()
    qtbot.addWidget(win)

    column_sizes = [420, 210, 360]
    row_sizes = [[300, 140], [220, 320], [260, 280]]
    win.workflow_columns.setSizes(column_sizes)
    for splitter, sizes in zip(win.workflow_splitters, row_sizes):
        splitter.setSizes(sizes)

    win._save_workflow_splitter_state()

    clone = videobatch_gui.MainWindow()
    qtbot.addWidget(clone)
    clone._restore_workflow_splitter_state()

    restored_columns = list(clone.workflow_columns.sizes())
    assert all(
        abs(current - target) < clone.WORKFLOW_REBALANCE_THRESHOLD_PX
        for current, target in zip(restored_columns, column_sizes)
    )

    for splitter, target_sizes in zip(clone.workflow_splitters, row_sizes):
        current_sizes = list(splitter.sizes())
        assert all(
            abs(current - target) < clone.WORKFLOW_REBALANCE_THRESHOLD_PX
            for current, target in zip(current_sizes, target_sizes)
        )


def test_resize_event_batches_ui_recalc_with_debounce(
    request, gui_runtime_available, gui_runtime_error
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        assert (
            "libGL.so.1" in gui_runtime_error
            or "libEGL.so.1" in gui_runtime_error
        )
        return

    qtbot = request.getfixturevalue("qtbot")
    videobatch_gui = _import_gui_module()
    win = videobatch_gui.MainWindow()
    qtbot.addWidget(win)

    called = {"action": 0, "hint": 0}
    original_reflow = win._reflow_action_buttons
    original_rewrap = win._rewrap_focus_hint_label

    def counted_reflow(available_width):
        called["action"] += 1
        return original_reflow(available_width)

    def counted_rewrap():
        called["hint"] += 1
        return original_rewrap()

    win._reflow_action_buttons = counted_reflow
    win._rewrap_focus_hint_label = counted_rewrap

    win.resize(1000, 760)
    win.resize(1010, 760)
    win.resize(1020, 760)

    assert called["action"] == 0
    assert called["hint"] == 0

    qtbot.wait(win.UI_RECALC_DEBOUNCE_MS + 80)

    assert called["action"] == 1
    assert called["hint"] == 1


def test_workflow_shortcut_focuses_target_section(
    request, gui_runtime_available, gui_runtime_error
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        assert (
            "libGL.so.1" in gui_runtime_error
            or "libEGL.so.1" in gui_runtime_error
        )
        return

    qtbot = request.getfixturevalue("qtbot")
    videobatch_gui = _import_gui_module()
    win = videobatch_gui.MainWindow()
    qtbot.addWidget(win)
    win.show()
    qtbot.waitExposed(win)

    win._focus_workflow_section("Protokoll", win.log_edit)

    assert win._active_section_name == "Protokoll"
    assert win.focus_hint_label.text().startswith("Aktiver Bereich: Protokoll")


def test_workflow_tab_order_is_defined_with_core_sequence(
    request, gui_runtime_available, gui_runtime_error
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        assert (
            "libGL.so.1" in gui_runtime_error
            or "libEGL.so.1" in gui_runtime_error
        )
        return

    qtbot = request.getfixturevalue("qtbot")
    videobatch_gui = _import_gui_module()
    win = videobatch_gui.MainWindow()
    qtbot.addWidget(win)

    win._init_workflow_tab_order()

    expected_chain = [
        win.pool_tabs,
        win.out_dir_edit,
        win.project_dir_edit,
        win.crf_spin,
        win.preset_combo,
        win.width_spin,
        win.height_spin,
        win.abitrate_edit,
        win.output_template_edit,
        win.mode_combo,
        win.parallel_jobs_spin,
        win.btn_add_images,
        win.btn_add_audios,
        win.btn_auto_pair,
        win.btn_encode,
        win.table,
        win.help_pane,
        win.log_edit,
    ]
    assert win._tab_order_chain == expected_chain


def test_row_error_focuses_failed_row_and_updates_live_status(
    request, gui_runtime_available, gui_runtime_error
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        assert (
            "libGL.so.1" in gui_runtime_error
            or "libEGL.so.1" in gui_runtime_error
        )
        return

    qtbot = request.getfixturevalue("qtbot")
    videobatch_gui = _import_gui_module()
    win = videobatch_gui.MainWindow()
    qtbot.addWidget(win)

    win.pairs = [
        videobatch_gui.PairItem(
            image_path="/tmp/image-a.jpg",
            audio_path="/tmp/audio-a.mp3",
            output="/tmp/out-a.mp4",
        ),
        videobatch_gui.PairItem(
            image_path="/tmp/image-b.jpg",
            audio_path="/tmp/audio-b.mp3",
            output="/tmp/out-b.mp4",
        ),
    ]
    win.model.layoutChanged.emit()

    win._on_row_error(1, "Fehlendes Audio")

    assert win.table.currentIndex().row() == 1
    assert win._active_section_name == "Paare"
    assert win.live_status_label.text().startswith("Fehler in Zeile 2")
    assert "nächster schritt" in win.live_status_label.text().lower()


def test_workflow_splitter_policies_prioritize_preview_and_actions(
    request, gui_runtime_available, gui_runtime_error
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        assert (
            "libGL.so.1" in gui_runtime_error
            or "libEGL.so.1" in gui_runtime_error
        )
        return

    qtbot = request.getfixturevalue("qtbot")
    videobatch_gui = _import_gui_module()
    win = videobatch_gui.MainWindow()
    qtbot.addWidget(win)
    win.resize(1260, 820)

    win._update_workflow_section_constraints()
    win._request_workflow_rebalance(force=True)
    qtbot.wait(win.WORKFLOW_REBALANCE_DEBOUNCE_MS + 80)

    assert win.workflow_columns.stretchFactor(
        2
    ) > win.workflow_columns.stretchFactor(0)
    assert win.workflow_columns.stretchFactor(
        2
    ) > win.workflow_columns.stretchFactor(1)
    assert win.workflow_splitters[1].stretchFactor(0) > win.workflow_splitters[
        1
    ].stretchFactor(1)

    assert win.btn_box.minimumHeight() >= win.settings_widget.minimumHeight()
    assert win.help_box.minimumHeight() >= win.log_box.minimumHeight()

    col_sizes = list(win.workflow_columns.sizes())
    assert col_sizes[2] >= col_sizes[0]
    assert col_sizes[2] >= col_sizes[1]


def test_accessibility_metadata_assigns_section_descriptions(
    request, gui_runtime_available, gui_runtime_error
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        assert (
            "libGL.so.1" in gui_runtime_error
            or "libEGL.so.1" in gui_runtime_error
        )
        return

    qtbot = request.getfixturevalue("qtbot")
    videobatch_gui = _import_gui_module()
    win = videobatch_gui.MainWindow()
    qtbot.addWidget(win)

    assert win.statusBar().accessibleName() == "Statusleiste"
    assert "Live-Status" in win.live_status_label.accessibleName()
    assert "nächsten Schritten" not in win.statusBar().accessibleDescription()
    assert "nächsten Schritten" not in win.table.accessibleDescription()
    assert "Master-Detail" in win.table.accessibleDescription()


def test_dashboard_quick_status_cards_show_text_and_state(
    request, gui_runtime_available, gui_runtime_error
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        assert (
            "libGL.so.1" in gui_runtime_error
            or "libEGL.so.1" in gui_runtime_error
        )
        return

    qtbot = request.getfixturevalue("qtbot")
    videobatch_gui = _import_gui_module()
    dashboard = videobatch_gui.InfoDashboard()
    qtbot.addWidget(dashboard)

    dashboard.set_quick_status(
        image_count=2,
        audio_count=0,
        pair_count=1,
        ffmpeg_ok=False,
        output_ready=True,
    )

    cards = dashboard._status_cards
    assert "2 bereit" in cards["images"].text()
    assert cards["images"].property("statusState") == "ok"
    assert cards["audios"].property("statusState") == "warn"
    assert cards["ffmpeg"].property("statusState") == "warn"
    assert cards["output"].property("statusState") == "ok"


def test_dashboard_status_card_click_emits_card_key(
    request, gui_runtime_available, gui_runtime_error
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        assert (
            "libGL.so.1" in gui_runtime_error
            or "libEGL.so.1" in gui_runtime_error
        )
        return

    qtbot = request.getfixturevalue("qtbot")
    videobatch_gui = _import_gui_module()
    dashboard = videobatch_gui.InfoDashboard()
    qtbot.addWidget(dashboard)

    received = []
    dashboard.cardActivated.connect(received.append)

    card = dashboard._status_cards["pairs"]
    qtbot.mouseClick(card, QtCore.Qt.LeftButton)

    assert received == ["pairs"]


def test_drop_list_item_ignore_toggle_updates_label_and_font(
    request, gui_runtime_available, gui_runtime_error
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        assert (
            "libGL.so.1" in gui_runtime_error
            or "libEGL.so.1" in gui_runtime_error
        )
        return

    qtbot = request.getfixturevalue("qtbot")
    videobatch_gui = _import_gui_module()
    widget = videobatch_gui.DropListWidget("Test", (".png",))
    qtbot.addWidget(widget)
    widget.add_files(["/tmp/beispiel.png"])
    item = widget.item(0)

    first_toggle = widget._toggle_item_ignored(item)
    assert first_toggle is True
    assert item.text().endswith("(ignoriert)")
    assert item.font().strikeOut()

    second_toggle = widget._toggle_item_ignored(item)
    assert second_toggle is False
    assert not item.text().endswith("(ignoriert)")
    assert not item.font().strikeOut()


def test_drop_list_rename_item_label_uses_dialog_input(
    request, gui_runtime_available, gui_runtime_error, monkeypatch
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        assert (
            "libGL.so.1" in gui_runtime_error
            or "libEGL.so.1" in gui_runtime_error
        )
        return

    qtbot = request.getfixturevalue("qtbot")
    videobatch_gui = _import_gui_module()
    widget = videobatch_gui.DropListWidget("Test", (".png",))
    qtbot.addWidget(widget)
    widget.add_files(["/tmp/beispiel.png"])
    item = widget.item(0)

    monkeypatch.setattr(
        videobatch_gui.QtWidgets.QInputDialog,
        "getText",
        staticmethod(lambda *args, **kwargs: ("NeuName.png", True)),
    )

    assert widget._rename_item_label(item)
    assert item.text() == "NeuName.png"


def test_drop_list_rename_item_keeps_ignore_suffix(
    request, gui_runtime_available, gui_runtime_error, monkeypatch
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        assert (
            "libGL.so.1" in gui_runtime_error
            or "libEGL.so.1" in gui_runtime_error
        )
        return

    qtbot = request.getfixturevalue("qtbot")
    videobatch_gui = _import_gui_module()
    widget = videobatch_gui.DropListWidget("Test", (".png",))
    qtbot.addWidget(widget)
    widget.add_files(["/tmp/beispiel.png"])
    item = widget.item(0)
    widget._set_item_ignored(item, True)

    monkeypatch.setattr(
        videobatch_gui.QtWidgets.QInputDialog,
        "getText",
        staticmethod(lambda *args, **kwargs: ("Alias.png", True)),
    )

    assert widget._rename_item_label(item)
    assert item.text() == "Alias.png (ignoriert)"
