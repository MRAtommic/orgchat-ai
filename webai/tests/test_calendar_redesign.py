"""
Tests for Calendar Redesign & Hardening (PLAN_CALENDAR_REDESIGN.md):
- Task 0 (Security): Stored XSS defense in upcoming & day detail
- Task 1 (Bug): Modal centering guarantee (no top-left drifting on edit)
- Task 2 (Layout): Full width calendar + 2-column bottom section
- Task 3 (Compaction): Day cell event caps (+N more pill)
- Task 4 (Detail Modal): Day detail modal markup and functionality
- Task 5 (Timezone): Local date string instead of UTC to avoid Thai midnight lag
"""

import os
import re
import pytest

WEB_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_html_markup_calendar_redesign():
    """Verify templates/index.html contains the full-width calendar and dayDetailModal."""
    html_path = os.path.join(WEB_ROOT, 'templates', 'index.html')
    assert os.path.isfile(html_path), "index.html must exist"
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Full width layout
    assert 'max-w-[2000px]' in html, "view-calendar must have max-w-[2000px]"
    
    # 2. Day detail modal exists with accessibility attributes
    assert 'id="dayDetailModal"' in html, "dayDetailModal must be present in index.html"
    assert 'role="dialog"' in html, "dialog role must be present"
    assert 'aria-labelledby="dayDetailModalTitle"' in html, "dayDetailModal must have aria-labelledby"
    assert 'id="dayDetailList"' in html, "dayDetailList container must exist"
    assert 'id="dayDetailAddBtn"' in html, "dayDetailAddBtn must exist"
    assert 'id="closeDayDetailModal"' in html, "closeDayDetailModal button must exist"

    # 3. Schedule modal centering & accessibility
    assert 'id="scheduleModal"' in html, "scheduleModal must exist"
    assert 'aria-labelledby="scheduleModalTitle"' in html, "scheduleModal must have aria-labelledby"


def test_js_calendar_centering_and_day_detail():
    """Verify static/js/chat.js implements centering fixes and dayDetail modal logic."""
    js_path = os.path.join(WEB_ROOT, 'static', 'js', 'chat.js')
    assert os.path.isfile(js_path), "chat.js must exist"
    with open(js_path, 'r', encoding='utf-8') as f:
        js = f.read()

    # 1. Centering helpers
    assert 'function openScheduleModal()' in js, "openScheduleModal helper must exist"
    assert 'function closeScheduleModalAction()' in js, "closeScheduleModalAction helper must exist"
    assert 'scheduleModal.classList.add(\'flex\', \'items-center\', \'justify-center\')' in js

    # 2. editSchedule re-centers modal
    assert 'function editSchedule(id)' in js
    # editSchedule must call openScheduleModal()
    edit_idx = js.find('function editSchedule(id)')
    assert edit_idx != -1
    edit_block = js[edit_idx:edit_idx+1200]
    assert 'openScheduleModal()' in edit_block, "editSchedule must call openScheduleModal()"

    # 3. Day detail modal functions
    assert 'function openDayDetailModal(' in js, "openDayDetailModal must exist"
    assert 'function closeDayDetailModalAction()' in js, "closeDayDetailModalAction must exist"
    assert 'function renderDayDetailContent(' in js, "renderDayDetailContent must exist"

    # 4. Timezone fix: localDateStr
    assert 'function localDateStr(' in js, "localDateStr helper must exist"
    # Ensure localDateStr is exported
    assert 'window.localDateStr = localDateStr' in js


def test_js_xss_protection_in_calendar():
    """Verify that renderUpcoming, renderCalendar, and renderDayDetailContent use escHtml and _safeUrl."""
    js_path = os.path.join(WEB_ROOT, 'static', 'js', 'chat.js')
    with open(js_path, 'r', encoding='utf-8') as f:
        js = f.read()

    # renderUpcoming XSS check
    up_idx = js.find('function renderUpcoming()')
    assert up_idx != -1
    up_block = js[up_idx:up_idx+5000]
    assert '${escHtml(s.title)}' in up_block, "renderUpcoming must escape s.title"
    assert '${escHtml(s.desc)' in up_block, "renderUpcoming must escape s.desc"
    assert '_safeUrl(s.avatar_url)' in up_block, "renderUpcoming must sanitize avatar_url"

    # renderDayDetailContent XSS check
    dd_idx = js.find('function renderDayDetailContent(')
    assert dd_idx != -1
    cal_idx = js.find('function renderCalendar()', dd_idx)
    assert cal_idx != -1
    dd_block = js[dd_idx:cal_idx]
    assert '${escHtml(s.title)}' in dd_block, "renderDayDetailContent must escape s.title"
    assert '${escHtml(s.desc)}' in dd_block, "renderDayDetailContent must escape s.desc"
    assert '_safeUrl(s.avatar_url)' in dd_block or 'safeAvatar' in dd_block, "renderDayDetailContent must sanitize avatar_url"


def test_js_window_exports():
    """Verify that calendar functions are exported to window for UI and tests."""
    js_path = os.path.join(WEB_ROOT, 'static', 'js', 'chat.js')
    with open(js_path, 'r', encoding='utf-8') as f:
        js = f.read()

    exports = [
        'window.openDayDetailModal = openDayDetailModal;',
        'window.closeDayDetailModalAction = closeDayDetailModalAction;',
        'window.renderDayDetailContent = renderDayDetailContent;',
        'window.localDateStr = localDateStr;',
        'window.openScheduleModal = openScheduleModal;',
        'window.closeScheduleModalAction = closeScheduleModalAction;',
        'window.editSchedule = editSchedule;',
        'window.deleteSchedule = deleteSchedule;',
        'window.toggleScheduleStatus = toggleScheduleStatus;',
        'window.openAddModal = openAddModal;'
    ]
    for exp in exports:
        assert exp in js, f"Export missing: {exp}"
