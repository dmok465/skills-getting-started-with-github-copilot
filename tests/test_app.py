"""
Unit tests for the Mergington High School Activities API
Tests cover all endpoints: GET /, GET /activities, POST /activities/{activity_name}/signup, and DELETE /activities/{activity_name}/signup

Tests follow the AAA (Arrange-Act-Assert) pattern:
- ARRANGE: Set up test data and preconditions
- ACT: Execute the function/code being tested
- ASSERT: Verify the results
"""

import pytest
from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from src.app import root, get_activities, signup_for_activity, unregister_from_activity


# ============================================================================
# FIXTURES - Provide clean test data for each test
# ============================================================================

@pytest.fixture
def mock_activities(monkeypatch):
    """Provide a clean in-memory activities dictionary for each test"""
    test_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": []
        }
    }
    monkeypatch.setattr("src.app.activities", test_activities)
    return test_activities


@pytest.fixture
def mock_full_activity(monkeypatch):
    """Provide an activity at capacity for boundary testing"""
    test_activities = {
        "Full Club": {
            "description": "A completely full activity",
            "schedule": "Mondays, 2:00 PM - 3:00 PM",
            "max_participants": 2,
            "participants": ["user1@test.edu", "user2@test.edu"]
        }
    }
    monkeypatch.setattr("src.app.activities", test_activities)
    return test_activities


# ============================================================================
# TEST: GET / (Root Redirect)
# ============================================================================

def test_root_redirect():
    """Test that root endpoint redirects to /static/index.html
    
    AAA Pattern:
    - ARRANGE: No setup needed, testing a simple function
    - ACT: Call the root() function
    - ASSERT: Verify it returns a RedirectResponse to the correct location
    """
    # ARRANGE
    # (no setup required for this test)

    # ACT
    result = root()

    # ASSERT
    assert isinstance(result, RedirectResponse)
    assert result.headers["location"] == "/static/index.html"


# ============================================================================
# TESTS: GET /activities
# ============================================================================

def test_get_activities_returns_all(mock_activities):
    """Test that GET /activities returns all activities
    
    AAA Pattern:
    - ARRANGE: Mock activities fixture provides 3 test activities
    - ACT: Call get_activities()
    - ASSERT: Verify all 3 activities are returned
    """
    # ARRANGE
    # (mock_activities fixture provides test data)

    # ACT
    result = get_activities()

    # ASSERT
    assert len(result) == 3
    assert "Chess Club" in result
    assert "Programming Class" in result
    assert "Gym Class" in result


def test_get_activities_structure(mock_activities):
    """Test that each activity has the required structure
    
    AAA Pattern:
    - ARRANGE: Mock activities fixture provides test data
    - ACT: Call get_activities()
    - ASSERT: Verify each activity has required fields
    """
    # ARRANGE
    # (mock_activities fixture provides test data)

    # ACT
    result = get_activities()

    # ASSERT
    for activity_name, activity in result.items():
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)


def test_get_activities_participant_count(mock_activities):
    """Test that participant counts are correct
    
    AAA Pattern:
    - ARRANGE: Mock activities with specific participant counts (2, 1, 0)
    - ACT: Call get_activities()
    - ASSERT: Verify participant counts match expected values
    """
    # ARRANGE
    # (mock_activities fixture sets up: Chess Club=2, Programming Class=1, Gym Class=0)

    # ACT
    result = get_activities()

    # ASSERT
    assert len(result["Chess Club"]["participants"]) == 2
    assert len(result["Programming Class"]["participants"]) == 1
    assert len(result["Gym Class"]["participants"]) == 0


def test_get_activities_participant_details(mock_activities):
    """Test that participant email details are correct
    
    AAA Pattern:
    - ARRANGE: Mock activities with specific participant emails
    - ACT: Call get_activities()
    - ASSERT: Verify specific emails are in participants lists
    """
    # ARRANGE
    # (mock_activities fixture sets up specific participant emails)

    # ACT
    result = get_activities()

    # ASSERT
    assert "michael@mergington.edu" in result["Chess Club"]["participants"]
    assert "daniel@mergington.edu" in result["Chess Club"]["participants"]
    assert "emma@mergington.edu" in result["Programming Class"]["participants"]


# ============================================================================
# TESTS: POST /activities/{activity_name}/signup
# ============================================================================

def test_signup_success(mock_activities):
    """Test successful signup adds email to participants
    
    AAA Pattern:
    - ARRANGE: Mock activities with an empty activity (Gym Class)
    - ACT: Call signup_for_activity("Gym Class", "newstudent@mergington.edu")
    - ASSERT: Verify email is added and response message is correct
    """
    # ARRANGE
    activity_name = "Gym Class"
    email = "newstudent@mergington.edu"
    initial_count = len(mock_activities[activity_name]["participants"])

    # ACT
    result = signup_for_activity(activity_name, email)

    # ASSERT
    assert result["message"] == f"Signed up {email} for {activity_name}"
    assert email in mock_activities[activity_name]["participants"]
    assert len(mock_activities[activity_name]["participants"]) == initial_count + 1


def test_signup_duplicate_email(mock_activities):
    """Test signup with duplicate email returns 400 error
    
    AAA Pattern:
    - ARRANGE: Mock activities with michael@mergington.edu already in Chess Club
    - ACT: Try to signup michael@mergington.edu to Chess Club again
    - ASSERT: Verify HTTPException with 400 status is raised
    """
    # ARRANGE
    activity_name = "Chess Club"
    duplicate_email = "michael@mergington.edu"
    assert duplicate_email in mock_activities[activity_name]["participants"]

    # ACT & ASSERT
    with pytest.raises(HTTPException) as exc_info:
        signup_for_activity(activity_name, duplicate_email)
    
    # ASSERT error details
    assert exc_info.value.status_code == 400
    assert "already signed up" in exc_info.value.detail


def test_signup_nonexistent_activity(mock_activities):
    """Test signup to nonexistent activity returns 404 error
    
    AAA Pattern:
    - ARRANGE: Verify "Nonexistent Club" is not in mock activities
    - ACT: Try to signup to "Nonexistent Club"
    - ASSERT: Verify HTTPException with 404 status is raised
    """
    # ARRANGE
    activity_name = "Nonexistent Club"
    email = "student@mergington.edu"
    assert activity_name not in mock_activities

    # ACT & ASSERT
    with pytest.raises(HTTPException) as exc_info:
        signup_for_activity(activity_name, email)
    
    # ASSERT error details
    assert exc_info.value.status_code == 404
    assert "Activity not found" in exc_info.value.detail


def test_signup_adds_to_correct_activity(mock_activities):
    """Test that signup adds email to the correct activity
    
    AAA Pattern:
    - ARRANGE: Set up test email and activity
    - ACT: Signup to Programming Class
    - ASSERT: Verify email is ONLY in Programming Class, not other activities
    """
    # ARRANGE
    activity_name = "Programming Class"
    email = "newstudent@mergington.edu"

    # ACT
    signup_for_activity(activity_name, email)

    # ASSERT - email should be in Programming Class only
    assert email not in mock_activities["Chess Club"]["participants"]
    assert email in mock_activities[activity_name]["participants"]
    assert email not in mock_activities["Gym Class"]["participants"]


def test_signup_response_message_format(mock_activities):
    """Test that signup response message has correct format
    
    AAA Pattern:
    - ARRANGE: Set up email and activity
    - ACT: Call signup_for_activity()
    - ASSERT: Verify response message contains expected text
    """
    # ARRANGE
    activity_name = "Gym Class"
    email = "testuser@mergington.edu"

    # ACT
    result = signup_for_activity(activity_name, email)

    # ASSERT
    assert "Signed up" in result["message"]
    assert email in result["message"]
    assert activity_name in result["message"]


def test_signup_multiple_students_same_activity(mock_activities):
    """Test that multiple different students can sign up for same activity
    
    AAA Pattern:
    - ARRANGE: Gym Class starts empty
    - ACT: Signup two different students
    - ASSERT: Verify both are in participants list
    """
    # ARRANGE
    activity_name = "Gym Class"
    email1 = "student1@mergington.edu"
    email2 = "student2@mergington.edu"
    initial_count = len(mock_activities[activity_name]["participants"])

    # ACT
    signup_for_activity(activity_name, email1)
    signup_for_activity(activity_name, email2)

    # ASSERT
    assert len(mock_activities[activity_name]["participants"]) == initial_count + 2
    assert email1 in mock_activities[activity_name]["participants"]
    assert email2 in mock_activities[activity_name]["participants"]


# ============================================================================
# TESTS: DELETE /activities/{activity_name}/signup
# ============================================================================

def test_unsignup_success(mock_activities):
    """Test successful unsignup removes email from participants
    
    AAA Pattern:
    - ARRANGE: Chess Club has michael@mergington.edu
    - ACT: Call unregister_from_activity("Chess Club", "michael@mergington.edu")
    - ASSERT: Verify email is removed and response message is correct
    """
    # ARRANGE
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    initial_count = len(mock_activities[activity_name]["participants"])
    assert email in mock_activities[activity_name]["participants"]

    # ACT
    result = unregister_from_activity(activity_name, email)

    # ASSERT
    assert result["message"] == f"Unregistered {email} from {activity_name}"
    assert email not in mock_activities[activity_name]["participants"]
    assert len(mock_activities[activity_name]["participants"]) == initial_count - 1


def test_unsignup_not_enrolled(mock_activities):
    """Test unsignup for non-enrolled student returns 400 error
    
    AAA Pattern:
    - ARRANGE: Verify email is NOT in Chess Club
    - ACT: Try to unsignup email that's not enrolled
    - ASSERT: Verify HTTPException with 400 status is raised
    """
    # ARRANGE
    activity_name = "Chess Club"
    email = "notstudent@mergington.edu"
    assert email not in mock_activities[activity_name]["participants"]

    # ACT & ASSERT
    with pytest.raises(HTTPException) as exc_info:
        unregister_from_activity(activity_name, email)
    
    # ASSERT error details
    assert exc_info.value.status_code == 400
    assert "not signed up" in exc_info.value.detail


def test_unsignup_nonexistent_activity(mock_activities):
    """Test unsignup from nonexistent activity returns 404 error
    
    AAA Pattern:
    - ARRANGE: Verify activity doesn't exist
    - ACT: Try to unsignup from nonexistent activity
    - ASSERT: Verify HTTPException with 404 status is raised
    """
    # ARRANGE
    activity_name = "Nonexistent Club"
    email = "student@mergington.edu"
    assert activity_name not in mock_activities

    # ACT & ASSERT
    with pytest.raises(HTTPException) as exc_info:
        unregister_from_activity(activity_name, email)
    
    # ASSERT error details
    assert exc_info.value.status_code == 404
    assert "Activity not found" in exc_info.value.detail


def test_unsignup_removes_from_correct_activity(mock_activities):
    """Test that unsignup removes email from correct activity only
    
    AAA Pattern:
    - ARRANGE: Signup to multiple activities, verify both succeeded
    - ACT: Unsignup from Programming Class only
    - ASSERT: Verify removed from Programming Class but still in Gym Class
    """
    # ARRANGE
    email = "testuser@mergington.edu"
    gym_activity = "Gym Class"
    prog_activity = "Programming Class"
    
    signup_for_activity(gym_activity, email)
    signup_for_activity(prog_activity, email)
    assert email in mock_activities[gym_activity]["participants"]
    assert email in mock_activities[prog_activity]["participants"]

    # ACT
    unregister_from_activity(prog_activity, email)

    # ASSERT
    assert email not in mock_activities[prog_activity]["participants"]
    assert email in mock_activities[gym_activity]["participants"]


def test_unsignup_response_message_format(mock_activities):
    """Test that unsignup response message has correct format
    
    AAA Pattern:
    - ARRANGE: Identify a participant to remove
    - ACT: Call unregister_from_activity()
    - ASSERT: Verify response message format
    """
    # ARRANGE
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # ACT
    result = unregister_from_activity(activity_name, email)

    # ASSERT
    assert "Unregistered" in result["message"]
    assert email in result["message"]
    assert activity_name in result["message"]


def test_unsignup_partially_full_activity(mock_activities):
    """Test unsignup from activity with multiple participants
    
    AAA Pattern:
    - ARRANGE: Chess Club has 2 participants (michael, daniel)
    - ACT: Remove daniel
    - ASSERT: Verify daniel is removed but michael remains
    """
    # ARRANGE
    activity_name = "Chess Club"
    email_to_remove = "daniel@mergington.edu"
    email_to_keep = "michael@mergington.edu"
    initial_count = len(mock_activities[activity_name]["participants"])

    # ACT
    unregister_from_activity(activity_name, email_to_remove)

    # ASSERT
    assert len(mock_activities[activity_name]["participants"]) == initial_count - 1
    assert email_to_keep in mock_activities[activity_name]["participants"]
    assert email_to_remove not in mock_activities[activity_name]["participants"]


# ============================================================================
# INTEGRATION TESTS - Multiple operations in sequence
# ============================================================================

def test_signup_then_unsignup(mock_activities):
    """Test signing up and then unregistering from same activity
    
    AAA Pattern:
    - ARRANGE: Define email and activity
    - ACT: First signup, then unsignup
    - ASSERT: Verify email added then removed correctly
    """
    # ARRANGE
    email = "integration@mergington.edu"
    activity = "Gym Class"
    assert email not in mock_activities[activity]["participants"]

    # ACT - Signup
    signup_result = signup_for_activity(activity, email)
    assert email in mock_activities[activity]["participants"]

    # ACT - Unsignup
    unsignup_result = unregister_from_activity(activity, email)

    # ASSERT
    assert email not in mock_activities[activity]["participants"]
    assert "Signed up" in signup_result["message"]
    assert "Unregistered" in unsignup_result["message"]


def test_signup_after_another_unsignup(mock_activities):
    """Test that a student can signup after another student unregisters
    
    AAA Pattern:
    - ARRANGE: Chess Club starts with 2 participants
    - ACT: Remove one, then add a new one
    - ASSERT: Verify count stays at 2 with different participant
    """
    # ARRANGE
    activity = "Chess Club"
    student_to_remove = "michael@mergington.edu"
    student_to_add = "newstudent@mergington.edu"
    initial_count = len(mock_activities[activity]["participants"])

    # ACT - One participant leaves
    unregister_from_activity(activity, student_to_remove)
    assert len(mock_activities[activity]["participants"]) == initial_count - 1

    # ACT - New student signs up
    signup_for_activity(activity, student_to_add)

    # ASSERT
    assert len(mock_activities[activity]["participants"]) == initial_count
    assert student_to_add in mock_activities[activity]["participants"]
    assert student_to_remove not in mock_activities[activity]["participants"]


def test_cannot_signup_twice_even_after_unsignup_then_signup_again(mock_activities):
    """Test that duplicate prevention works correctly across multiple operations
    
    AAA Pattern:
    - ARRANGE: Define email and activity
    - ACT: Signup → Try duplicate → Unsignup → Signup again
    - ASSERT: Verify error on duplicate, success on re-signup after unsignup
    """
    # ARRANGE
    email = "student@mergington.edu"
    activity = "Gym Class"
    assert email not in mock_activities[activity]["participants"]

    # ACT & ASSERT - First signup succeeds
    signup_for_activity(activity, email)
    assert email in mock_activities[activity]["participants"]

    # ACT & ASSERT - Second signup fails (duplicate)
    with pytest.raises(HTTPException) as exc_info:
        signup_for_activity(activity, email)
    assert exc_info.value.status_code == 400

    # ACT - Unsignup
    unregister_from_activity(activity, email)
    assert email not in mock_activities[activity]["participants"]

    # ACT & ASSERT - Signup again succeeds (no longer duplicate)
    signup_for_activity(activity, email)
    assert email in mock_activities[activity]["participants"]
