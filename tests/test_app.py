from copy import deepcopy

import pytest

from src.app import activities


def test_root_redirects_to_static_page(client):
    # Arrange
    url = "/"

    # Act
    response = client.get(url, follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_static_page_is_served(client):
    # Arrange
    url = "/static/index.html"

    # Act
    response = client.get(url)

    # Assert
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Mergington High School" in response.text


def test_get_activities_returns_activity_details(client):
    # Arrange
    expected = deepcopy(activities)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected
    assert isinstance(response.json(), dict)
    for details in response.json().values():
        assert {"description", "schedule", "max_participants", "participants"} <= details.keys()
        assert isinstance(details["description"], str)
        assert isinstance(details["schedule"], str)
        assert isinstance(details["max_participants"], int)
        assert isinstance(details["participants"], list)


def test_signup_adds_participant_only_to_selected_activity(client):
    # Arrange
    activity_name = "Chess Club"
    email = "new+student@mergington.edu"
    expected = deepcopy(activities)
    expected[activity_name]["participants"].append(email)

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})
    updated = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert updated.status_code == 200
    assert updated.json() == expected
    assert updated.json()[activity_name]["participants"].count(email) == 1
    assert activities == expected


def test_duplicate_signup_is_rejected_without_changes(client):
    # Arrange
    url = "/activities/Chess Club/signup"
    email = "new@mergington.edu"
    initial_response = client.post(url, params={"email": email})
    assert initial_response.status_code == 200
    expected = deepcopy(activities)

    # Act
    response = client.post(url, params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Student already signed up for this activity"}
    assert activities == expected


@pytest.mark.parametrize("method", ["POST", "DELETE"])
def test_unknown_activity_is_rejected_without_changes(client, method):
    # Arrange
    expected = deepcopy(activities)
    url = "/activities/Nonexistent Activity/signup"

    # Act
    response = client.request(method, url, params={"email": "student@mergington.edu"})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert activities == expected


def test_unregister_removes_only_selected_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]
    expected = deepcopy(activities)
    expected[activity_name]["participants"].remove(email)

    # Act
    response = client.delete(f"/activities/{activity_name}/signup", params={"email": email})
    updated = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
    assert updated.status_code == 200
    assert updated.json() == expected
    assert email not in updated.json()[activity_name]["participants"]
    assert activities == expected


def test_unregister_last_participant_leaves_empty_list(client):
    # Arrange
    activity_name = "Chess Club"
    email = "only@mergington.edu"
    activities[activity_name]["participants"] = [email]
    expected = deepcopy(activities)
    expected[activity_name]["participants"] = []

    # Act
    response = client.delete(f"/activities/{activity_name}/signup", params={"email": email})
    updated = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert updated.status_code == 200
    assert updated.json() == expected
    assert activities == expected


def test_participant_can_register_again_after_unregistering(client):
    # Arrange
    activity_name = "Chess Club"
    url = f"/activities/{activity_name}/signup"
    email = activities[activity_name]["participants"][0]
    initial_response = client.delete(url, params={"email": email})
    assert initial_response.status_code == 200
    expected = deepcopy(activities)
    expected[activity_name]["participants"].append(email)

    # Act
    response = client.post(url, params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert activities == expected
    assert activities[activity_name]["participants"].count(email) == 1


def test_unregister_missing_participant_is_rejected_without_changes(client):
    # Arrange
    expected = deepcopy(activities)
    email = "not-registered@mergington.edu"

    # Act
    response = client.delete("/activities/Chess Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Student is not signed up for this activity"}
    assert activities == expected


def test_repeated_unregister_is_rejected_without_changes(client):
    # Arrange
    url = "/activities/Chess Club/signup"
    email = activities["Chess Club"]["participants"][0]
    initial_response = client.delete(url, params={"email": email})
    assert initial_response.status_code == 200
    expected = deepcopy(activities)

    # Act
    response = client.delete(url, params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Student is not signed up for this activity"}
    assert activities == expected


@pytest.mark.parametrize("method", ["POST", "DELETE"])
def test_signup_routes_require_email_without_changes(client, method):
    # Arrange
    expected = deepcopy(activities)
    url = "/activities/Chess Club/signup"

    # Act
    response = client.request(method, url)

    # Assert
    assert response.status_code == 422
    assert any(error["loc"] == ["query", "email"] for error in response.json()["detail"])
    assert activities == expected