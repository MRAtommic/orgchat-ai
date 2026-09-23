import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "webai"))

import database
from routes.chat import create_meeting_reminder_flex_bubble

def test_attendance_and_schedule():
    print("Testing Attendance and Schedule LINE Bot Integration...")

    # 1. Test schedule reminder bubble
    mock_sch = {
        "id": 999,
        "title": "ประชุมสรุปงานไตรมาส 4",
        "start_date": "2026-10-25",
        "start_time": "14:30",
        "category": "Meeting",
        "description": "ประชุมประจำเดือน",
        "username": "admin",
        "display_name": "พี่อาร์ม",
        "organization_id": 1
    }
    bubble = create_meeting_reminder_flex_bubble(mock_sch, minutes_before=30)
    assert bubble["type"] == "bubble"
    assert bubble["header"]["type"] == "box"
    assert "30 นาที" in bubble["header"]["contents"][1]["text"]
    assert "ประชุมสรุปงานไตรมาส 4" in bubble["header"]["contents"][2]["text"]
    print("  ✓ Meeting reminder Flex bubble generated properly")

    # 2. Test DB upcoming schedules query
    upcoming = database.get_upcoming_schedules(window_minutes=60)
    assert isinstance(upcoming, list)
    print(f"  ✓ get_upcoming_schedules returned {len(upcoming)} items")

    # 3. Add a test schedule
    test_id = database.add_schedule(
        username="admin",
        title="Automated Test Meeting",
        start_date="2026-12-31",
        description="Testing LINE integration",
        category="Meeting",
        start_time="10:00",
        is_public=1,
        org_id=1
    )
    assert test_id is not None
    print(f"  ✓ Added test schedule ID #{test_id}")

    # 4. Mark reminder sent
    database.mark_schedule_reminder_sent(test_id)
    print(f"  ✓ Marked reminder sent for schedule #{test_id}")

    # Clean up test schedule
    database.delete_schedule(test_id, "admin")
    print(f"  ✓ Cleaned up test schedule #{test_id}")

    print("ALL TESTS PASSED SUCCESSFULLY! 🎉")

if __name__ == "__main__":
    test_attendance_and_schedule()
