import os
import tempfile
import pytest
from app import create_app
from models.database import init_db
from models.user import UserModel
from models.event import EventModel
from services.ai_planner import calculate_budget_breakdown, generate_local_plan

@pytest.fixture
def app_instance():
    """Create a temporary test application instance with an isolated database."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    
    test_config = {
        "TESTING": True,
        "DATABASE_PATH": db_path,
        "SECRET_KEY": "test-secret-key-celebrationai",
        "GEMINI_API_KEY": ""  # Test in pure deterministic local heuristic mode
    }

    app = create_app(test_config)

    with app.app_context():
        init_db(app)

    yield app

    os.close(db_fd)
    if os.path.exists(db_path):
        try:
            os.unlink(db_path)
        except PermissionError:
            pass

@pytest.fixture
def client(app_instance):
    return app_instance.test_client()

def test_health_and_homepage(client):
    """Verify health endpoint and landing page render correctly."""
    health_res = client.get("/health")
    assert health_res.status_code == 200
    health_data = health_res.get_json()
    assert health_data["status"] == "healthy"
    assert health_data["service"] == "CelebrationAI"

    home_res = client.get("/")
    assert home_res.status_code == 200
    html = home_res.data.decode("utf-8")
    assert "Every celebration deserves a" in html
    assert "Plan My Event" in html
    assert "Weddings" in html
    assert "Birthdays" in html

def test_explore_and_how_it_works(client):
    """Verify exploration and methodology pages load."""
    exp_res = client.get("/explore")
    assert exp_res.status_code == 200
    assert "Celebration Themes" in exp_res.data.decode("utf-8")

    hiw_res = client.get("/how-it-works")
    assert hiw_res.status_code == 200
    assert "Designed for Real Celebrations" in hiw_res.data.decode("utf-8")

def test_user_registration_and_authentication(client, app_instance):
    """Verify user registration, hashing, and login authentication."""
    with app_instance.app_context():
        user = UserModel.create("Priya Sharma", "priya@example.com", "SecretPass123!")
        assert user is not None
        assert user["email"] == "priya@example.com"

        # Password authentication
        auth_success = UserModel.authenticate("priya@example.com", "SecretPass123!")
        assert auth_success is not None
        assert auth_success["name"] == "Priya Sharma"

        # Bad password
        auth_fail = UserModel.authenticate("priya@example.com", "WrongPassword")
        assert auth_fail is None

def test_event_form_validation(client):
    """Verify server-side required field validation."""
    # Attempt event creation without required fields
    res = client.post("/api/events/generate", json={})
    assert res.status_code == 400
    data = res.get_json()
    assert data["success"] is False
    assert len(data["errors"]) >= 4

def test_create_event_and_ai_plan_generation(client, app_instance):
    """Verify complete end-to-end event generation and persistence."""
    payload = {
        "title": "Ananya & Arjun's Sangeet & Reception",
        "event_type": "Wedding",
        "event_date": "2026-12-15",
        "start_time": "18:00",
        "end_time": "23:30",
        "location": "Leela Palace, Bangalore",
        "indoor_outdoor": "Hybrid",
        "guest_count": 150,
        "total_budget": 500000.0,
        "currency": "INR",
        "budget_tier": "balanced",
        "theme": "Regal Blossom & Ivory Splendor",
        "food_preference": "Mixed (Veg & Non-Veg)",
        "services_needed": ["Venue", "Catering", "Decoration", "Photography", "Music or DJ", "Cake and desserts"]
    }

    res = client.post("/api/events/generate", json=payload)
    assert res.status_code == 201
    res_data = res.get_json()
    assert res_data["success"] is True
    event_id = res_data["event_id"]
    assert event_id is not None

    # Verify event stored in DB
    with app_instance.app_context():
        ev = EventModel.get_event(event_id)
        assert ev["title"] == payload["title"]
        assert ev["guest_count"] == 150
        assert ev["total_budget"] == 500000.0

        # Check expenses generated
        expenses = EventModel.get_expenses(event_id)
        assert len(expenses) > 0
        total_planned = sum(e["planned_amount"] for e in expenses)
        # Arithmetic integrity: planned expenses must not exceed budget
        assert total_planned <= ev["total_budget"]

        # Check timeline tasks generated
        tasks = EventModel.get_tasks(event_id)
        assert len(tasks) >= 5

        # Check vendors generated
        vendors = EventModel.get_vendors(event_id)
        assert len(vendors) >= 3

        # Check ideas generated
        ideas = EventModel.get_ideas(event_id)
        assert len(ideas) >= 4

def test_budget_calculations_and_expenses_crud(client, app_instance):
    """Verify adding, updating, and deleting expenses with correct budget totals."""
    with app_instance.app_context():
        demo_user = UserModel.get_or_create_demo_user()
        ev = EventModel.create_event(demo_user["id"], {
            "title": "Test Budget Event",
            "event_type": "Birthday",
            "event_date": "2026-11-20",
            "location": "Community Center",
            "guest_count": 50,
            "total_budget": 50000.0
        })
        event_id = ev["id"]

    # 1. Add expense
    add_res = client.post(f"/api/events/{event_id}/expenses", json={
        "category": "Catering",
        "title": "Buffet Caterer Advance",
        "planned_amount": 15000.0,
        "actual_amount": 5000.0,
        "status": "Pending",
        "notes": "Deposit receipt #101"
    })
    assert add_res.status_code == 200
    exp_id = add_res.get_json()["expense_id"]

    # Verify DB
    with app_instance.app_context():
        expenses = EventModel.get_expenses(event_id)
        assert len(expenses) == 1
        assert expenses[0]["actual_amount"] == 5000.0

    # 2. Update expense
    upd_res = client.put(f"/api/events/{event_id}/expenses/{exp_id}", json={
        "actual_amount": 15000.0,
        "status": "Paid"
    })
    assert upd_res.status_code == 200

    with app_instance.app_context():
        expenses = EventModel.get_expenses(event_id)
        assert expenses[0]["actual_amount"] == 15000.0
        assert expenses[0]["status"] == "Paid"

    # 3. Delete expense
    del_res = client.delete(f"/api/events/{event_id}/expenses/{exp_id}")
    assert del_res.status_code == 200

    with app_instance.app_context():
        expenses = EventModel.get_expenses(event_id)
        assert len(expenses) == 0

def test_timeline_tasks_toggle_and_crud(client, app_instance):
    """Verify milestone creation, completion toggling, and removal."""
    with app_instance.app_context():
        demo_user = UserModel.get_or_create_demo_user()
        ev = EventModel.create_event(demo_user["id"], {
            "title": "Test Timeline Event",
            "event_type": "Anniversary",
            "event_date": "2026-12-01",
            "location": "Banquet Room",
            "total_budget": 80000.0
        })
        event_id = ev["id"]

    # Add task
    add_res = client.post(f"/api/events/{event_id}/tasks", json={
        "title": "Book acoustic violinist",
        "due_date": "2026-11-15",
        "priority": "High",
        "category": "Booking",
        "explanation": "Music reservation"
    })
    assert add_res.status_code == 200
    task_id = add_res.get_json()["task_id"]

    # Toggle task to completed
    toggle_res = client.post(f"/api/events/{event_id}/tasks/{task_id}/toggle")
    assert toggle_res.status_code == 200
    assert toggle_res.get_json()["is_completed"] is True

    with app_instance.app_context():
        tasks = EventModel.get_tasks(event_id)
        assert tasks[0]["is_completed"] == 1

def test_vendor_status_updates(client, app_instance):
    """Verify vendor checklist status changes."""
    with app_instance.app_context():
        demo_user = UserModel.get_or_create_demo_user()
        ev = EventModel.create_event(demo_user["id"], {
            "title": "Vendor Test Event",
            "event_type": "College Festival",
            "event_date": "2026-11-25",
            "location": "Auditorium",
            "total_budget": 200000.0
        })
        event_id = ev["id"]

    add_res = client.post(f"/api/events/{event_id}/vendors", json={
        "category": "Sound & Lighting",
        "name": "Pulse Audio Pro",
        "contact_info": "+91 9123456789",
        "estimated_cost": 45000.0,
        "booking_status": "Needed"
    })
    assert add_res.status_code == 200
    vendor_id = add_res.get_json()["vendor_id"]

    # Update status to Booked
    upd_res = client.put(f"/api/events/{event_id}/vendors/{vendor_id}", json={
        "booking_status": "Booked",
        "payment_status": "Advance Paid"
    })
    assert upd_res.status_code == 200

    with app_instance.app_context():
        vendors = EventModel.get_vendors(event_id)
        assert vendors[0]["booking_status"] == "Booked"
        assert vendors[0]["payment_status"] == "Advance Paid"

def test_guest_list_management(client, app_instance):
    """Verify guest additions, party counts, and RSVP status updates."""
    with app_instance.app_context():
        demo_user = UserModel.get_or_create_demo_user()
        ev = EventModel.create_event(demo_user["id"], {
            "title": "Guest Test Event",
            "event_type": "Birthday",
            "event_date": "2026-11-10",
            "location": "Home Lawn",
            "total_budget": 30000.0
        })
        event_id = ev["id"]

    # Add guest with party size of 2
    add_res = client.post(f"/api/events/{event_id}/guests", json={
        "name": "Kavita Rao",
        "email_or_phone": "kavita@example.com",
        "rsvp_status": "Invited",
        "attendees_count": 2,
        "dietary_preference": "Vegetarian",
        "table_or_group": "Family"
    })
    assert add_res.status_code == 200
    guest_id = add_res.get_json()["guest_id"]

    # Update RSVP to Attending
    upd_res = client.put(f"/api/events/{event_id}/guests/{guest_id}", json={
        "rsvp_status": "Attending"
    })
    assert upd_res.status_code == 200

    with app_instance.app_context():
        guests = EventModel.get_guests(event_id)
        assert guests[0]["rsvp_status"] == "Attending"
        assert guests[0]["attendees_count"] == 2

def test_chat_assistant_and_proposals(client, app_instance):
    """Verify AI event chat assistant and structured action proposals."""
    with app_instance.app_context():
        demo_user = UserModel.get_or_create_demo_user()
        ev = EventModel.create_event(demo_user["id"], {
            "title": "Chat Test Event",
            "event_type": "Wedding",
            "event_date": "2026-12-20",
            "location": "Grand Palace",
            "total_budget": 500000.0,
            "guest_count": 100,
            "food_preference": "Mixed"
        })
        event_id = ev["id"]

    # 1. Ask cost saving question
    chat_res = client.post(f"/api/events/{event_id}/chat", json={
        "message": "How can I save ₹5,000 on this celebration?"
    })
    assert chat_res.status_code == 200
    chat_data = chat_res.get_json()
    assert chat_data["success"] is True
    assert "save" in chat_data["reply"].lower()

    # 2. Ask budget addition question that produces an action proposal
    prop_res = client.post(f"/api/events/{event_id}/chat", json={
        "message": "Recalculate my budget after adding ₹2,000 for photography"
    })
    assert prop_res.status_code == 200
    prop_data = prop_res.get_json()
    assert prop_data["action_proposal"] is not None
    proposal = prop_data["action_proposal"]
    assert proposal["type"] == "add_expense"

    # 3. Apply the proposed action
    apply_res = client.post(f"/api/events/{event_id}/chat/apply-action", json=proposal)
    assert apply_res.status_code == 200

    with app_instance.app_context():
        expenses = EventModel.get_expenses(event_id)
        assert any("Photography" in e["title"] or e["planned_amount"] == 2000.0 for e in expenses)

def test_private_event_authorization(client, app_instance):
    """Verify authorization checks: User A cannot access User B's event dashboard."""
    with app_instance.app_context():
        user_a = UserModel.create("User A", "user_a@test.com", "PasswordA123")
        user_b = UserModel.create("User B", "user_b@test.com", "PasswordB123")

        ev_b = EventModel.create_event(user_b["id"], {
            "title": "User B Secret Gala",
            "event_type": "Anniversary",
            "event_date": "2026-12-31",
            "location": "Private Villa",
            "total_budget": 100000.0
        })
        event_b_id = ev_b["id"]

    # Sign in as User A
    with client.session_transaction() as sess:
        sess["user_id"] = user_a["id"]
        sess["user_name"] = user_a["name"]

    # Attempt to open User B's event dashboard
    res = client.get(f"/events/{event_b_id}", follow_redirects=False)
    # Should be redirected away with access denied
    assert res.status_code == 302
    assert "/events" in res.headers["Location"]
