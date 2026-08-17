"""
Simultaneous Identical & Duplicate Submission Safety Test for OrgChat AI
Verifies that multiple users sending identical data simultaneously do NOT mix up or corrupt database state.
Usage:
    python test_duplicate_concurrent_submissions.py
"""
import sys
import os
import concurrent.futures

os.environ["FLASK_ENV"] = "testing"

try:
    import database
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import database


def test_simultaneous_identical_submissions():
    print("🧪 Running Simultaneous Identical Submissions Test...")
    
    # 5 different users submitting identical leave request data at the exact same time
    user_payloads = [
        ("user_alpha", "ลาพักร้อน", "2026-08-10", "2026-08-12", "พักผ่อนประจำปี", 1),
        ("user_beta", "ลาพักร้อน", "2026-08-10", "2026-08-12", "พักผ่อนประจำปี", 1),
        ("user_gamma", "ลาพักร้อน", "2026-08-10", "2026-08-12", "พักผ่อนประจำปี", 1),
        ("user_delta", "ลาพักร้อน", "2026-08-10", "2026-08-12", "พักผ่อนประจำปี", 1),
        ("user_epsilon", "ลาพักร้อน", "2026-08-10", "2026-08-12", "พักผ่อนประจำปี", 1),
    ]

    def submit_leave(item):
        username, l_type, start, end, reason, org_id = item
        leave_id = database.create_leave_request(username, l_type, start, end, reason, org_id=org_id)
        return username, leave_id

    # Execute all 5 submissions concurrently at the exact same millisecond
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(submit_leave, item) for item in user_payloads]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    # Check that each submission received a UNIQUE, non-conflicting primary key ID
    leave_ids = [res[1] for res in results]
    usernames = [res[0] for res in results]
    
    print(f"✔️ Submissions completed for users: {usernames}")
    print(f"✔️ Generated Leave Request IDs: {leave_ids}")
    
    assert len(leave_ids) == 5, "Not all submissions completed!"
    assert len(set(leave_ids)) == 5, "Duplicate IDs detected! Race condition in DB primary key assignment!"
    
    # Verify database data integrity: check each record belongs to its exact user
    for user, lid in results:
        user_leaves = database.get_user_leaves(user)
        matched = [l for l in user_leaves if l["id"] == lid]
        assert len(matched) == 1, f"Data cross-contamination! Leave ID {lid} not found for {user}"
        assert matched[0]["username"] == user, f"Data mixed up! Leave ID {lid} assigned to {matched[0]['username']} instead of {user}"

    print("\n==========================================================")
    print(" ✨ SIMULTANEOUS SUBMISSION SAFETY TEST: PASSED 100%")
    print("==========================================================")
    print("🔒 Zero Data Collision | Unique Atomic IDs | Absolute Data Isolation")
    print("==========================================================\n")


if __name__ == "__main__":
    test_simultaneous_identical_submissions()
