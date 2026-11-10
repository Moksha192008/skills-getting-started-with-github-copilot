import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(
        app_module,
        "activities",
        {
            "Chess Club": {
                "description": "Practice chess",
                "schedule": "Fridays",
                "max_participants": 3,
                "participants": ["first@example.com", "second@example.com"],
            },
            "Empty Club": {
                "description": "Try a new activity",
                "schedule": "Mondays",
                "max_participants": 5,
                "participants": [],
            },
        },
    )
    return TestClient(app_module.app)


def test_root_redirects_to_activity_page(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_activity_data(client):
    # Arrange
    expected_names = {"Chess Club", "Empty Club"}

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert set(response.json()) == expected_names
    assert response.json()["Chess Club"]["participants"] == [
        "first@example.com",
        "second@example.com",
    ]


def test_signup_adds_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = "new@example.com"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    participants = client.get("/activities").json()[activity_name]["participants"]
    assert email in participants


def test_signup_returns_404_for_unknown_activity(client):
    # Arrange
    email = "new@example.com"

    # Act
    response = client.post(
        "/activities/Unknown Club/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_only_the_selected_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = "first@example.com"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {activity_name}"
    }
    participants = client.get("/activities").json()[activity_name]["participants"]
    assert participants == ["second@example.com"]


def test_unregister_returns_404_for_missing_participant(client):
    # Arrange
    email = "missing@example.com"

    # Act
    response = client.delete(
        "/activities/Chess Club/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"


def test_unregister_returns_404_for_unknown_activity(client):
    # Arrange
    email = "first@example.com"

    # Act
    response = client.delete(
        "/activities/Unknown Club/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"