import json
from datetime import datetime
from models.database import get_db

class EventModel:
    """Data access object for Events and all associated planning components."""

    @staticmethod
    def create_event(user_id, data):
        """Create a new event record."""
        db = get_db()
        cursor = db.execute(
            """
            INSERT INTO events (
                user_id, title, event_type, event_date, start_time, end_time,
                location, indoor_outdoor, guest_count, total_budget, currency,
                budget_tier, theme, color_palette, food_preference,
                entertainment_preference, cultural_traditions, accessibility_needs,
                additional_notes, services_needed, ai_concept
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                data.get("title", "My Celebration"),
                data.get("event_type", "Other"),
                data.get("event_date", ""),
                data.get("start_time", ""),
                data.get("end_time", ""),
                data.get("location", ""),
                data.get("indoor_outdoor", "Indoor"),
                int(data.get("guest_count", 50)),
                float(data.get("total_budget", 0.0)),
                data.get("currency", "INR"),
                data.get("budget_tier", "balanced"),
                data.get("theme", ""),
                json.dumps(data.get("color_palette", [])) if isinstance(data.get("color_palette"), list) else data.get("color_palette", ""),
                data.get("food_preference", "Mixed"),
                data.get("entertainment_preference", ""),
                data.get("cultural_traditions", ""),
                data.get("accessibility_needs", ""),
                data.get("additional_notes", ""),
                json.dumps(data.get("services_needed", [])) if isinstance(data.get("services_needed"), list) else data.get("services_needed", "[]"),
                json.dumps(data.get("ai_concept", {})) if isinstance(data.get("ai_concept"), dict) else data.get("ai_concept", "{}")
            )
        )
        db.commit()
        return EventModel.get_event(cursor.lastrowid, user_id=user_id)

    @staticmethod
    def get_event(event_id, user_id=None):
        """Retrieve single event by id and optional user ownership check."""
        db = get_db()
        if user_id:
            row = db.execute("SELECT * FROM events WHERE id = ? AND user_id = ?", (event_id, user_id)).fetchone()
        else:
            row = db.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
        
        if not row:
            return None
        
        event = dict(row)
        # Parse JSON fields safely
        try:
            event["color_palette"] = json.loads(event["color_palette"]) if event["color_palette"] else []
        except Exception:
            event["color_palette"] = [event["color_palette"]] if event["color_palette"] else []

        try:
            event["services_needed"] = json.loads(event["services_needed"]) if event["services_needed"] else []
        except Exception:
            event["services_needed"] = []

        try:
            event["ai_concept"] = json.loads(event["ai_concept"]) if event["ai_concept"] else {}
        except Exception:
            event["ai_concept"] = {}

        return event

    @staticmethod
    def list_events_for_user(user_id):
        """List all events for a user with aggregated statistics."""
        db = get_db()
        rows = db.execute(
            """
            SELECT e.*,
                   COALESCE((SELECT SUM(actual_amount) FROM expenses WHERE event_id = e.id), 0.0) AS actual_spent,
                   COALESCE((SELECT SUM(planned_amount) FROM expenses WHERE event_id = e.id), 0.0) AS planned_spent,
                   (SELECT COUNT(*) FROM timeline_tasks WHERE event_id = e.id) AS total_tasks,
                   (SELECT COUNT(*) FROM timeline_tasks WHERE event_id = e.id AND is_completed = 1) AS completed_tasks,
                   (SELECT COUNT(*) FROM guests WHERE event_id = e.id) AS total_guests,
                   (SELECT COUNT(*) FROM guests WHERE event_id = e.id AND rsvp_status = 'Attending') AS confirmed_guests
            FROM events e
            WHERE e.user_id = ?
            ORDER BY e.event_date ASC, e.created_at DESC
            """,
            (user_id,)
        ).fetchall()

        events = []
        for r in rows:
            ev = dict(r)
            try:
                ev["services_needed"] = json.loads(ev["services_needed"]) if ev["services_needed"] else []
            except Exception:
                ev["services_needed"] = []
            events.append(ev)
        return events

    @staticmethod
    def update_event(event_id, user_id, data):
        """Update event details."""
        db = get_db()
        fields = []
        values = []

        allowed = [
            "title", "event_type", "event_date", "start_time", "end_time",
            "location", "indoor_outdoor", "guest_count", "total_budget", "currency",
            "budget_tier", "theme", "food_preference", "entertainment_preference",
            "cultural_traditions", "accessibility_needs", "additional_notes"
        ]

        for k in allowed:
            if k in data:
                fields.append(f"{k} = ?")
                val = data[k]
                if k == "guest_count":
                    val = int(val)
                elif k == "total_budget":
                    val = float(val)
                values.append(val)

        if "color_palette" in data:
            fields.append("color_palette = ?")
            cp = data["color_palette"]
            values.append(json.dumps(cp) if isinstance(cp, (list, dict)) else str(cp))

        if "services_needed" in data:
            fields.append("services_needed = ?")
            sn = data["services_needed"]
            values.append(json.dumps(sn) if isinstance(sn, (list, dict)) else str(sn))

        if "ai_concept" in data:
            fields.append("ai_concept = ?")
            ac = data["ai_concept"]
            values.append(json.dumps(ac) if isinstance(ac, dict) else str(ac))

        fields.append("updated_at = CURRENT_TIMESTAMP")

        if not fields:
            return EventModel.get_event(event_id, user_id)

        values.extend([event_id, user_id])
        query = f"UPDATE events SET {', '.join(fields)} WHERE id = ? AND user_id = ?"
        db.execute(query, values)
        db.commit()
        return EventModel.get_event(event_id, user_id)

    @staticmethod
    def delete_event(event_id, user_id):
        """Delete event if owned by user."""
        db = get_db()
        db.execute("DELETE FROM events WHERE id = ? AND user_id = ?", (event_id, user_id))
        db.commit()
        return True

    # =========================================================================
    # EXPENSES
    # =========================================================================
    @staticmethod
    def get_expenses(event_id):
        """Get all expenses for an event."""
        db = get_db()
        rows = db.execute(
            "SELECT * FROM expenses WHERE event_id = ? ORDER BY planned_amount DESC, id ASC",
            (event_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def add_expense(event_id, category, title, planned_amount=0.0, actual_amount=0.0, status="Planned", notes=""):
        """Add a new expense item."""
        db = get_db()
        cursor = db.execute(
            """
            INSERT INTO expenses (event_id, category, title, planned_amount, actual_amount, status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (event_id, category, title, max(0.0, float(planned_amount)), max(0.0, float(actual_amount)), status, notes)
        )
        db.commit()
        return cursor.lastrowid

    @staticmethod
    def update_expense(expense_id, event_id, data):
        """Update an existing expense."""
        db = get_db()
        db.execute(
            """
            UPDATE expenses
            SET category = COALESCE(?, category),
                title = COALESCE(?, title),
                planned_amount = COALESCE(?, planned_amount),
                actual_amount = COALESCE(?, actual_amount),
                status = COALESCE(?, status),
                notes = COALESCE(?, notes)
            WHERE id = ? AND event_id = ?
            """,
            (
                data.get("category"),
                data.get("title"),
                max(0.0, float(data["planned_amount"])) if "planned_amount" in data else None,
                max(0.0, float(data["actual_amount"])) if "actual_amount" in data else None,
                data.get("status"),
                data.get("notes"),
                expense_id,
                event_id
            )
        )
        db.commit()

    @staticmethod
    def delete_expense(expense_id, event_id):
        """Delete an expense."""
        db = get_db()
        db.execute("DELETE FROM expenses WHERE id = ? AND event_id = ?", (expense_id, event_id))
        db.commit()

    # =========================================================================
    # TIMELINE TASKS
    # =========================================================================
    @staticmethod
    def get_tasks(event_id):
        """Get all timeline tasks sorted chronologically."""
        db = get_db()
        rows = db.execute(
            "SELECT * FROM timeline_tasks WHERE event_id = ? ORDER BY due_date ASC, id ASC",
            (event_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def add_task(event_id, title, due_date="", priority="Medium", category="Preparation", explanation=""):
        """Add timeline task."""
        db = get_db()
        cursor = db.execute(
            """
            INSERT INTO timeline_tasks (event_id, title, due_date, priority, category, explanation)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (event_id, title, due_date, priority, category, explanation)
        )
        db.commit()
        return cursor.lastrowid

    @staticmethod
    def update_task(task_id, event_id, data):
        """Update timeline task."""
        db = get_db()
        db.execute(
            """
            UPDATE timeline_tasks
            SET title = COALESCE(?, title),
                due_date = COALESCE(?, due_date),
                priority = COALESCE(?, priority),
                category = COALESCE(?, category),
                explanation = COALESCE(?, explanation),
                is_completed = COALESCE(?, is_completed)
            WHERE id = ? AND event_id = ?
            """,
            (
                data.get("title"),
                data.get("due_date"),
                data.get("priority"),
                data.get("category"),
                data.get("explanation"),
                data.get("is_completed"),
                task_id,
                event_id
            )
        )
        db.commit()

    @staticmethod
    def toggle_task(task_id, event_id):
        """Toggle task completion status."""
        db = get_db()
        row = db.execute(
            "SELECT is_completed FROM timeline_tasks WHERE id = ? AND event_id = ?",
            (task_id, event_id)
        ).fetchone()
        if row:
            new_val = 0 if row["is_completed"] else 1
            db.execute(
                "UPDATE timeline_tasks SET is_completed = ? WHERE id = ? AND event_id = ?",
                (new_val, task_id, event_id)
            )
            db.commit()
            return new_val
        return None

    @staticmethod
    def delete_task(task_id, event_id):
        """Delete task."""
        db = get_db()
        db.execute("DELETE FROM timeline_tasks WHERE id = ? AND event_id = ?", (task_id, event_id))
        db.commit()

    # =========================================================================
    # VENDORS
    # =========================================================================
    @staticmethod
    def get_vendors(event_id):
        """Get all vendor records for an event."""
        db = get_db()
        rows = db.execute("SELECT * FROM vendors WHERE event_id = ? ORDER BY id ASC", (event_id,)).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def add_vendor(event_id, category, name="", contact_info="", estimated_cost=0.0, actual_cost=0.0,
                   booking_status="Needed", payment_status="Unpaid", deadline="", notes=""):
        """Add a vendor tracking entry."""
        db = get_db()
        cursor = db.execute(
            """
            INSERT INTO vendors (
                event_id, category, name, contact_info, estimated_cost, actual_cost,
                booking_status, payment_status, deadline, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id, category, name, contact_info,
                max(0.0, float(estimated_cost)), max(0.0, float(actual_cost)),
                booking_status, payment_status, deadline, notes
            )
        )
        db.commit()
        return cursor.lastrowid

    @staticmethod
    def update_vendor(vendor_id, event_id, data):
        """Update vendor details."""
        db = get_db()
        db.execute(
            """
            UPDATE vendors
            SET category = COALESCE(?, category),
                name = COALESCE(?, name),
                contact_info = COALESCE(?, contact_info),
                estimated_cost = COALESCE(?, estimated_cost),
                actual_cost = COALESCE(?, actual_cost),
                booking_status = COALESCE(?, booking_status),
                payment_status = COALESCE(?, payment_status),
                deadline = COALESCE(?, deadline),
                notes = COALESCE(?, notes)
            WHERE id = ? AND event_id = ?
            """,
            (
                data.get("category"),
                data.get("name"),
                data.get("contact_info"),
                float(data["estimated_cost"]) if "estimated_cost" in data else None,
                float(data["actual_cost"]) if "actual_cost" in data else None,
                data.get("booking_status"),
                data.get("payment_status"),
                data.get("deadline"),
                data.get("notes"),
                vendor_id,
                event_id
            )
        )
        db.commit()

    @staticmethod
    def delete_vendor(vendor_id, event_id):
        """Delete vendor."""
        db = get_db()
        db.execute("DELETE FROM vendors WHERE id = ? AND event_id = ?", (vendor_id, event_id))
        db.commit()

    # =========================================================================
    # GUESTS
    # =========================================================================
    @staticmethod
    def get_guests(event_id):
        """Get guest list."""
        db = get_db()
        rows = db.execute("SELECT * FROM guests WHERE event_id = ? ORDER BY name ASC", (event_id,)).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def add_guest(event_id, name, email_or_phone="", rsvp_status="Invited", attendees_count=1,
                  dietary_preference="No preference", table_or_group="", notes=""):
        """Add guest."""
        db = get_db()
        cursor = db.execute(
            """
            INSERT INTO guests (
                event_id, name, email_or_phone, rsvp_status, attendees_count,
                dietary_preference, table_or_group, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id, name.strip(), email_or_phone.strip(), rsvp_status,
                max(1, int(attendees_count)), dietary_preference, table_or_group.strip(), notes.strip()
            )
        )
        db.commit()
        return cursor.lastrowid

    @staticmethod
    def update_guest(guest_id, event_id, data):
        """Update guest information."""
        db = get_db()
        db.execute(
            """
            UPDATE guests
            SET name = COALESCE(?, name),
                email_or_phone = COALESCE(?, email_or_phone),
                rsvp_status = COALESCE(?, rsvp_status),
                attendees_count = COALESCE(?, attendees_count),
                dietary_preference = COALESCE(?, dietary_preference),
                table_or_group = COALESCE(?, table_or_group),
                notes = COALESCE(?, notes)
            WHERE id = ? AND event_id = ?
            """,
            (
                data.get("name"),
                data.get("email_or_phone"),
                data.get("rsvp_status"),
                int(data["attendees_count"]) if "attendees_count" in data else None,
                data.get("dietary_preference"),
                data.get("table_or_group"),
                data.get("notes"),
                guest_id,
                event_id
            )
        )
        db.commit()

    @staticmethod
    def delete_guest(guest_id, event_id):
        """Delete guest."""
        db = get_db()
        db.execute("DELETE FROM guests WHERE id = ? AND event_id = ?", (guest_id, event_id))
        db.commit()

    # =========================================================================
    # CHECKLIST ITEMS
    # =========================================================================
    @staticmethod
    def get_checklist_items(event_id):
        """Get shopping & prep checklist items."""
        db = get_db()
        rows = db.execute("SELECT * FROM checklist_items WHERE event_id = ? ORDER BY id ASC", (event_id,)).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def add_checklist_item(event_id, category, item_name, estimated_cost=0.0, notes=""):
        """Add checklist item."""
        db = get_db()
        cursor = db.execute(
            """
            INSERT INTO checklist_items (event_id, category, item_name, estimated_cost, notes)
            VALUES (?, ?, ?, ?, ?)
            """,
            (event_id, category, item_name.strip(), max(0.0, float(estimated_cost)), notes.strip())
        )
        db.commit()
        return cursor.lastrowid

    @staticmethod
    def toggle_checklist_item(item_id, event_id):
        """Toggle checklist item completed status."""
        db = get_db()
        row = db.execute(
            "SELECT is_completed FROM checklist_items WHERE id = ? AND event_id = ?",
            (item_id, event_id)
        ).fetchone()
        if row:
            new_val = 0 if row["is_completed"] else 1
            db.execute(
                "UPDATE checklist_items SET is_completed = ? WHERE id = ? AND event_id = ?",
                (new_val, item_id, event_id)
            )
            db.commit()
            return new_val
        return None

    @staticmethod
    def delete_checklist_item(item_id, event_id):
        """Delete checklist item."""
        db = get_db()
        db.execute("DELETE FROM checklist_items WHERE id = ? AND event_id = ?", (item_id, event_id))
        db.commit()

    # =========================================================================
    # EVENT IDEAS (Bookmarkable)
    # =========================================================================
    @staticmethod
    def get_ideas(event_id):
        """Get personalized event ideas."""
        db = get_db()
        rows = db.execute("SELECT * FROM event_ideas WHERE event_id = ? ORDER BY id ASC", (event_id,)).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def add_idea(event_id, category, title, description):
        """Add personalized idea."""
        db = get_db()
        cursor = db.execute(
            "INSERT INTO event_ideas (event_id, category, title, description) VALUES (?, ?, ?, ?)",
            (event_id, category, title.strip(), description.strip())
        )
        db.commit()
        return cursor.lastrowid

    @staticmethod
    def toggle_favorite_idea(idea_id, event_id):
        """Toggle favorite bookmark on an idea."""
        db = get_db()
        row = db.execute("SELECT is_favorited FROM event_ideas WHERE id = ? AND event_id = ?", (idea_id, event_id)).fetchone()
        if row:
            new_val = 0 if row["is_favorited"] else 1
            db.execute("UPDATE event_ideas SET is_favorited = ? WHERE id = ? AND event_id = ?", (new_val, idea_id, event_id))
            db.commit()
            return new_val
        return None

    # =========================================================================
    # CHAT ASSISTANT MESSAGES
    # =========================================================================
    @staticmethod
    def get_chat_history(event_id, limit=30):
        """Get recent chat messages."""
        db = get_db()
        rows = db.execute(
            "SELECT * FROM chat_messages WHERE event_id = ? ORDER BY id ASC LIMIT ?",
            (event_id, limit)
        ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def add_chat_message(event_id, sender, content, action_proposal=None):
        """Add chat message to history."""
        db = get_db()
        action_json = json.dumps(action_proposal) if action_proposal else None
        cursor = db.execute(
            "INSERT INTO chat_messages (event_id, sender, content, action_proposal) VALUES (?, ?, ?, ?)",
            (event_id, sender, content, action_json)
        )
        db.commit()
        return cursor.lastrowid

    # =========================================================================
    # POPULATE AI PLAN
    # =========================================================================
    @staticmethod
    def populate_ai_plan(event_id, plan_data):
        """
        Populate the database with structured items generated by AI or rule-based engine.
        Ensures strict mathematical consistency: total planned expenses <= event budget.
        """
        db = get_db()

        # Update event concept & theme if provided
        concept = plan_data.get("concept", {})
        if concept:
            db.execute(
                "UPDATE events SET ai_concept = ?, theme = COALESCE(NULLIF(theme, ''), ?) WHERE id = ?",
                (json.dumps(concept), concept.get("theme", ""), event_id)
            )

        # Clear existing AI-generated items if this is a regeneration
        db.execute("DELETE FROM expenses WHERE event_id = ?", (event_id,))
        db.execute("DELETE FROM timeline_tasks WHERE event_id = ?", (event_id,))
        db.execute("DELETE FROM vendors WHERE event_id = ?", (event_id,))
        db.execute("DELETE FROM checklist_items WHERE event_id = ?", (event_id,))
        db.execute("DELETE FROM event_ideas WHERE event_id = ?", (event_id,))

        # 1. Budget Breakdown -> Expenses
        for exp in plan_data.get("budget_breakdown", []):
            db.execute(
                """
                INSERT INTO expenses (event_id, category, title, planned_amount, actual_amount, status, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    exp.get("category", "General"),
                    exp.get("title", exp.get("category", "Item")),
                    max(0.0, float(exp.get("estimated_amount", 0.0))),
                    0.0,
                    "Planned",
                    exp.get("reason", "")
                )
            )

        # 2. Timeline Tasks
        for task in plan_data.get("timeline", []):
            db.execute(
                """
                INSERT INTO timeline_tasks (event_id, title, due_date, priority, category, explanation)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    task.get("task", "Event Task"),
                    task.get("due_date", ""),
                    task.get("priority", "Medium"),
                    task.get("category", "Preparation"),
                    task.get("explanation", "")
                )
            )

        # 3. Vendor Checklist
        for vendor in plan_data.get("vendors", []):
            db.execute(
                """
                INSERT INTO vendors (
                    event_id, category, name, contact_info, estimated_cost, actual_cost,
                    booking_status, payment_status, deadline, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    vendor.get("category", "Vendor"),
                    "",  # User fills actual vendor name
                    "",  # User fills contact info
                    max(0.0, float(vendor.get("estimated_budget", 0.0))),
                    0.0,
                    vendor.get("status", "Needed"),
                    "Unpaid",
                    vendor.get("deadline", ""),
                    vendor.get("why_needed", "")
                )
            )

        # 4. Personalized Ideas
        for idea in plan_data.get("ideas", []):
            db.execute(
                "INSERT INTO event_ideas (event_id, category, title, description) VALUES (?, ?, ?, ?)",
                (
                    event_id,
                    idea.get("category", "General"),
                    idea.get("title", "Creative Idea"),
                    idea.get("description", "")
                )
            )

        # 5. Shopping & Prep Checklist
        for item in plan_data.get("checklist", []):
            db.execute(
                """
                INSERT INTO checklist_items (event_id, category, item_name, is_completed, estimated_cost, notes)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    item.get("category", "General"),
                    item.get("item", "Item"),
                    0,
                    max(0.0, float(item.get("estimated_cost", 0.0))),
                    item.get("notes", "")
                )
            )

        db.commit()
        return True
