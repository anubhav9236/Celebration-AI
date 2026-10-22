import os
import json
import logging
from datetime import datetime, timezone
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, jsonify, flash, g
)

from config import Config, BASE_DIR
from models import init_db, close_db, UserModel, EventModel
from services import generate_event_plan, answer_event_chat

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def create_app(test_config=None):
    """Application factory for CelebrationAI."""
    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "static")
    )
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    # Register teardown
    app.teardown_appcontext(close_db)

    # Initialize database on startup safely
    with app.app_context():
        try:
            init_db(app)
        except Exception as e:
            logger.error(f"Startup DB initialization notice: {e}")

    # Global template context helpers
    @app.context_processor
    def inject_globals():
        current_user = None
        if "user_id" in session:
            try:
                current_user = UserModel.get_by_id(session["user_id"])
            except Exception:
                current_user = None
        
        has_api_key = bool(Config.GEMINI_API_KEY and Config.GEMINI_API_KEY != "your_gemini_api_key_here")

        return {
            "current_user": current_user,
            "has_gemini_key": has_api_key,
            "current_year": datetime.now().year,
            "default_currency": Config.DEFAULT_CURRENCY,
            "currency_symbol": Config.DEFAULT_CURRENCY_SYMBOL
        }

    # Auth decorator
    def login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
                # If running locally without login, automatically provide the demo user session
                demo_user = UserModel.get_or_create_demo_user()
                session["user_id"] = demo_user["id"]
                session["user_name"] = demo_user["name"]
            return f(*args, **kwargs)
        return decorated_function

    # =========================================================================
    # PUBLIC ROUTES
    # =========================================================================
    @app.route("/")
    def index():
        """CelebrationAI Landing Page."""
        return render_template("index.html")

    @app.route("/explore")
    def explore():
        """Inspiration & Themes catalog."""
        return render_template("explore.html")

    @app.route("/how-it-works")
    def how_it_works():
        """How CelebrationAI works guide."""
        return render_template("how_it_works.html")

    @app.route("/health")
    def health_check():
        """Production health check endpoint."""
        return jsonify({
            "status": "healthy",
            "service": "CelebrationAI",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "gemini_configured": bool(Config.GEMINI_API_KEY and Config.GEMINI_API_KEY != "your_gemini_api_key_here")
        }), 200

    # =========================================================================
    # AUTHENTICATION
    # =========================================================================
    @app.route("/login", methods=["GET", "POST"])
    def login():
        """User login."""
        if request.method == "POST":
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "")
            
            user = UserModel.authenticate(email, password)
            if user:
                session["user_id"] = user["id"]
                session["user_name"] = user["name"]
                flash(f"Welcome back, {user['name']}!", "success")
                next_url = request.args.get("next") or url_for("my_events")
                return redirect(next_url)
            else:
                flash("Invalid email or password. Please try again.", "danger")

        return render_template("login.html")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        """User registration."""
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "")
            confirm = request.form.get("confirm_password", "")

            if not name or not email or not password:
                flash("Please complete all required fields.", "warning")
            elif len(password) < 6:
                flash("Password must be at least 6 characters long.", "warning")
            elif password != confirm:
                flash("Passwords do not match.", "warning")
            else:
                existing = UserModel.get_by_email(email)
                if existing:
                    flash("An account with this email already exists. Please sign in.", "warning")
                else:
                    new_user = UserModel.create(name, email, password)
                    if new_user:
                        session["user_id"] = new_user["id"]
                        session["user_name"] = new_user["name"]
                        flash("Account created successfully! Welcome to CelebrationAI.", "success")
                        return redirect(url_for("create_event"))
                    else:
                        flash("Registration failed. Please try again.", "danger")

        return render_template("register.html")

    @app.route("/demo-login", methods=["POST"])
    def demo_login():
        """Instant demo login for evaluation."""
        demo_user = UserModel.get_or_create_demo_user()
        session["user_id"] = demo_user["id"]
        session["user_name"] = demo_user["name"]
        flash(f"Signed in as Demo User ({demo_user['name']}). All features are active!", "info")
        return redirect(url_for("my_events"))

    @app.route("/logout")
    def logout():
        """Logout and clear session."""
        session.clear()
        flash("You have been signed out.", "info")
        return redirect(url_for("index"))

    # =========================================================================
    # EVENT CREATION WIZARD
    # =========================================================================
    @app.route("/create")
    @login_required
    def create_event():
        """Multi-step Event Creation Wizard."""
        # Check URL query params for pre-fill from landing page or themes
        prefill = {
            "event_type": request.args.get("type", "Wedding"),
            "event_date": request.args.get("date", ""),
            "guest_count": request.args.get("guests", 100),
            "total_budget": request.args.get("budget", 200000),
            "location": request.args.get("location", ""),
            "theme": request.args.get("theme", "")
        }
        return render_template("create_event.html", prefill=prefill)

    @app.route("/api/events/generate", methods=["POST"])
    @login_required
    def api_generate_event():
        """
        API Endpoint: Validate form data, generate structured AI plan,
        and persist complete event into SQLite.
        """
        try:
            data = request.get_json() or {}
            
            # Validation
            title = data.get("title", "").strip()
            event_type = data.get("event_type", "").strip()
            event_date = data.get("event_date", "").strip()
            location = data.get("location", "").strip()
            total_budget = float(data.get("total_budget", 0))

            errors = []
            if not title:
                errors.append("Event name is required.")
            if not event_type:
                errors.append("Event type is required.")
            if not event_date:
                errors.append("Event date is required.")
            if not location:
                errors.append("Location is required.")
            if total_budget <= 0:
                errors.append("Please specify a valid budget greater than zero.")

            if errors:
                return jsonify({"success": False, "errors": errors}), 400

            # 1. Create Base Event in Database
            user_id = session.get("user_id")
            event = EventModel.create_event(user_id, data)
            if not event:
                return jsonify({"success": False, "message": "Failed to save event."}), 500

            # 2. Generate Plan using Generative AI (Gemini or Local Fallback)
            plan = generate_event_plan(data)

            # 3. Populate Event Components (Expenses, Timeline, Vendors, Ideas, Checklist)
            EventModel.populate_ai_plan(event["id"], plan)

            # 4. Add initial assistant welcome message
            currency_symbol = "₹" if data.get("currency") == "INR" else data.get("currency", "₹")
            welcome_msg = (
                f"Hello! I'm your CelebrationAI assistant for **{title}**. "
                f"I've structured a complete plan for your budget of {currency_symbol}{total_budget:,.2f}. "
                "Ask me any questions about saving costs, modifying food menus, or adjusting tasks!"
            )
            EventModel.add_chat_message(event["id"], "assistant", welcome_msg)

            return jsonify({
                "success": True,
                "event_id": event["id"],
                "is_demo": plan.get("is_demo", False),
                "mode_label": plan.get("mode_label", ""),
                "redirect_url": url_for("event_dashboard", event_id=event["id"])
            }), 201

        except Exception as e:
            logger.exception("Error in api_generate_event")
            return jsonify({
                "success": False,
                "message": "An unexpected error occurred while generating your event plan. Please check your inputs and try again."
            }), 500

    # =========================================================================
    # EVENT DASHBOARD & TABS
    # =========================================================================
    @app.route("/events")
    @login_required
    def my_events():
        """List of all user events with countdowns and progress."""
        user_id = session.get("user_id")
        events = EventModel.list_events_for_user(user_id)
        
        # Calculate days countdown for each event
        today = datetime.now().date()
        for ev in events:
            try:
                ev_date = datetime.strptime(ev["event_date"], "%Y-%m-%d").date()
                diff = (ev_date - today).days
                ev["days_left"] = diff
            except Exception:
                ev["days_left"] = None

        return render_template("my_events.html", events=events)

    @app.route("/events/<int:event_id>")
    @login_required
    def event_dashboard(event_id):
        """Single Event Dashboard with 7 functional tabs."""
        user_id = session.get("user_id")
        event = EventModel.get_event(event_id, user_id=user_id)
        if not event:
            flash("Event not found or access denied.", "danger")
            return redirect(url_for("my_events"))

        # Fetch all related collections
        expenses = EventModel.get_expenses(event_id)
        tasks = EventModel.get_tasks(event_id)
        vendors = EventModel.get_vendors(event_id)
        guests = EventModel.get_guests(event_id)
        checklist = EventModel.get_checklist_items(event_id)
        ideas = EventModel.get_ideas(event_id)
        chat_history = EventModel.get_chat_history(event_id)

        # Budget arithmetic
        total_budget = float(event["total_budget"])
        total_planned = sum(float(e["planned_amount"]) for e in expenses)
        total_actual = sum(float(e["actual_amount"]) for e in expenses)
        remaining_budget = max(0.0, total_budget - total_actual)
        budget_utilization = round((total_actual / total_budget) * 100.0, 1) if total_budget > 0 else 0

        # Guest count metrics
        confirmed_attendees = sum(g["attendees_count"] for g in guests if g["rsvp_status"] == "Attending")
        total_invited = sum(g["attendees_count"] for g in guests)

        # Countdown
        today = datetime.now().date()
        try:
            ev_date = datetime.strptime(event["event_date"], "%Y-%m-%d").date()
            days_left = (ev_date - today).days
        except Exception:
            days_left = None

        # Overdue check on tasks
        for t in tasks:
            t["is_overdue"] = False
            if t["due_date"] and not t["is_completed"]:
                try:
                    due = datetime.strptime(t["due_date"], "%Y-%m-%d").date()
                    if due < today:
                        t["is_overdue"] = True
                except Exception:
                    pass

        # Progress calculation
        completed_tasks = len([t for t in tasks if t["is_completed"]])
        task_percent = round((completed_tasks / len(tasks)) * 100) if tasks else 0

        completed_checklist = len([c for c in checklist if c["is_completed"]])
        checklist_percent = round((completed_checklist / len(checklist)) * 100) if checklist else 0

        booked_vendors = len([v for v in vendors if v["booking_status"] in ["Booked", "Completed"]])
        vendor_percent = round((booked_vendors / len(vendors)) * 100) if vendors else 0

        active_tab = request.args.get("tab", "overview")

        return render_template(
            "dashboard.html",
            event=event,
            expenses=expenses,
            tasks=tasks,
            vendors=vendors,
            guests=guests,
            checklist=checklist,
            ideas=ideas,
            chat_history=chat_history,
            total_budget=total_budget,
            total_planned=total_planned,
            total_actual=total_actual,
            remaining_budget=remaining_budget,
            budget_utilization=budget_utilization,
            confirmed_attendees=confirmed_attendees,
            total_invited=total_invited,
            days_left=days_left,
            task_percent=task_percent,
            checklist_percent=checklist_percent,
            vendor_percent=vendor_percent,
            active_tab=active_tab
        )

    @app.route("/events/<int:event_id>/delete", methods=["POST"])
    @login_required
    def delete_event(event_id):
        """Delete an event."""
        user_id = session.get("user_id")
        EventModel.delete_event(event_id, user_id)
        flash("Event deleted successfully.", "info")
        return redirect(url_for("my_events"))

    @app.route("/api/events/<int:event_id>/regenerate", methods=["POST"])
    @login_required
    def api_regenerate_plan(event_id):
        """Regenerate event plan with AI."""
        user_id = session.get("user_id")
        event = EventModel.get_event(event_id, user_id)
        if not event:
            return jsonify({"success": False, "message": "Event not found"}), 404

        plan = generate_event_plan(event)
        EventModel.populate_ai_plan(event_id, plan)
        
        return jsonify({
            "success": True,
            "message": "Plan regenerated successfully!",
            "is_demo": plan.get("is_demo", False),
            "mode_label": plan.get("mode_label", "")
        })

    # =========================================================================
    # REST API FOR INTERACTIVE DASHBOARD TABS
    # =========================================================================

    # --- EXPENSES ---
    @app.route("/api/events/<int:event_id>/expenses", methods=["POST"])
    @login_required
    def api_add_expense(event_id):
        data = request.get_json() or {}
        category = data.get("category", "General").strip()
        title = data.get("title", "").strip()
        planned = float(data.get("planned_amount", 0))
        actual = float(data.get("actual_amount", 0))
        status = data.get("status", "Planned")
        notes = data.get("notes", "")

        if not title:
            return jsonify({"success": False, "message": "Title is required"}), 400

        expense_id = EventModel.add_expense(event_id, category, title, planned, actual, status, notes)
        return jsonify({"success": True, "expense_id": expense_id})

    @app.route("/api/events/<int:event_id>/expenses/<int:expense_id>", methods=["PUT", "DELETE"])
    @login_required
    def api_modify_expense(event_id, expense_id):
        if request.method == "DELETE":
            EventModel.delete_expense(expense_id, event_id)
            return jsonify({"success": True})
        else:
            data = request.get_json() or {}
            EventModel.update_expense(expense_id, event_id, data)
            return jsonify({"success": True})

    # --- TIMELINE TASKS ---
    @app.route("/api/events/<int:event_id>/tasks", methods=["POST"])
    @login_required
    def api_add_task(event_id):
        data = request.get_json() or {}
        title = data.get("title", "").strip()
        if not title:
            return jsonify({"success": False, "message": "Task title is required"}), 400

        task_id = EventModel.add_task(
            event_id,
            title=title,
            due_date=data.get("due_date", ""),
            priority=data.get("priority", "Medium"),
            category=data.get("category", "Preparation"),
            explanation=data.get("explanation", "")
        )
        return jsonify({"success": True, "task_id": task_id})

    @app.route("/api/events/<int:event_id>/tasks/<int:task_id>/toggle", methods=["POST"])
    @login_required
    def api_toggle_task(event_id, task_id):
        new_status = EventModel.toggle_task(task_id, event_id)
        return jsonify({"success": True, "is_completed": bool(new_status)})

    @app.route("/api/events/<int:event_id>/tasks/<int:task_id>", methods=["PUT", "DELETE"])
    @login_required
    def api_modify_task(event_id, task_id):
        if request.method == "DELETE":
            EventModel.delete_task(task_id, event_id)
            return jsonify({"success": True})
        else:
            data = request.get_json() or {}
            EventModel.update_task(task_id, event_id, data)
            return jsonify({"success": True})

    # --- VENDORS ---
    @app.route("/api/events/<int:event_id>/vendors", methods=["POST"])
    @login_required
    def api_add_vendor(event_id):
        data = request.get_json() or {}
        category = data.get("category", "General").strip()
        vendor_id = EventModel.add_vendor(
            event_id,
            category=category,
            name=data.get("name", ""),
            contact_info=data.get("contact_info", ""),
            estimated_cost=float(data.get("estimated_cost", 0)),
            actual_cost=float(data.get("actual_cost", 0)),
            booking_status=data.get("booking_status", "Needed"),
            payment_status=data.get("payment_status", "Unpaid"),
            deadline=data.get("deadline", ""),
            notes=data.get("notes", "")
        )
        return jsonify({"success": True, "vendor_id": vendor_id})

    @app.route("/api/events/<int:event_id>/vendors/<int:vendor_id>", methods=["PUT", "DELETE"])
    @login_required
    def api_modify_vendor(event_id, vendor_id):
        if request.method == "DELETE":
            EventModel.delete_vendor(vendor_id, event_id)
            return jsonify({"success": True})
        else:
            data = request.get_json() or {}
            EventModel.update_vendor(vendor_id, event_id, data)
            return jsonify({"success": True})

    # --- GUESTS ---
    @app.route("/api/events/<int:event_id>/guests", methods=["POST"])
    @login_required
    def api_add_guest(event_id):
        data = request.get_json() or {}
        name = data.get("name", "").strip()
        if not name:
            return jsonify({"success": False, "message": "Guest name is required"}), 400

        guest_id = EventModel.add_guest(
            event_id,
            name=name,
            email_or_phone=data.get("email_or_phone", ""),
            rsvp_status=data.get("rsvp_status", "Invited"),
            attendees_count=int(data.get("attendees_count", 1)),
            dietary_preference=data.get("dietary_preference", "No preference"),
            table_or_group=data.get("table_or_group", ""),
            notes=data.get("notes", "")
        )
        return jsonify({"success": True, "guest_id": guest_id})

    @app.route("/api/events/<int:event_id>/guests/<int:guest_id>", methods=["PUT", "DELETE"])
    @login_required
    def api_modify_guest(event_id, guest_id):
        if request.method == "DELETE":
            EventModel.delete_guest(guest_id, event_id)
            return jsonify({"success": True})
        else:
            data = request.get_json() or {}
            EventModel.update_guest(guest_id, event_id, data)
            return jsonify({"success": True})

    # --- CHECKLIST ITEMS ---
    @app.route("/api/events/<int:event_id>/checklist", methods=["POST"])
    @login_required
    def api_add_checklist_item(event_id):
        data = request.get_json() or {}
        item_name = data.get("item_name", "").strip()
        category = data.get("category", "General").strip()
        if not item_name:
            return jsonify({"success": False, "message": "Item name is required"}), 400

        item_id = EventModel.add_checklist_item(
            event_id,
            category=category,
            item_name=item_name,
            estimated_cost=float(data.get("estimated_cost", 0)),
            notes=data.get("notes", "")
        )
        return jsonify({"success": True, "item_id": item_id})

    @app.route("/api/events/<int:event_id>/checklist/<int:item_id>/toggle", methods=["POST"])
    @login_required
    def api_toggle_checklist_item(event_id, item_id):
        new_val = EventModel.toggle_checklist_item(item_id, event_id)
        return jsonify({"success": True, "is_completed": bool(new_val)})

    @app.route("/api/events/<int:event_id>/checklist/<int:item_id>", methods=["DELETE"])
    @login_required
    def api_delete_checklist_item(event_id, item_id):
        EventModel.delete_checklist_item(item_id, event_id)
        return jsonify({"success": True})

    # --- IDEAS ---
    @app.route("/api/events/<int:event_id>/ideas", methods=["POST"])
    @login_required
    def api_add_idea(event_id):
        data = request.get_json() or {}
        title = data.get("title", "").strip()
        description = data.get("description", "").strip()
        category = data.get("category", "General").strip()
        if not title:
            return jsonify({"success": False, "message": "Title is required"}), 400

        idea_id = EventModel.add_idea(event_id, category, title, description)
        return jsonify({"success": True, "idea_id": idea_id})

    @app.route("/api/events/<int:event_id>/ideas/<int:idea_id>/favorite", methods=["POST"])
    @login_required
    def api_toggle_favorite_idea(event_id, idea_id):
        new_val = EventModel.toggle_favorite_idea(idea_id, event_id)
        return jsonify({"success": True, "is_favorited": bool(new_val)})

    # --- CHAT ASSISTANT ---
    @app.route("/api/events/<int:event_id>/chat", methods=["GET", "POST"])
    @login_required
    def api_event_chat(event_id):
        user_id = session.get("user_id")
        event = EventModel.get_event(event_id, user_id)
        if not event:
            return jsonify({"success": False, "message": "Event not found"}), 404

        if request.method == "GET":
            history = EventModel.get_chat_history(event_id)
            return jsonify({"success": True, "messages": history})

        data = request.get_json() or {}
        message = data.get("message", "").strip()
        if not message:
            return jsonify({"success": False, "message": "Message text is required"}), 400

        # Save user message
        EventModel.add_chat_message(event_id, "user", message)

        # Retrieve current context
        expenses = EventModel.get_expenses(event_id)
        tasks = EventModel.get_tasks(event_id)

        # Generate response
        result = answer_event_chat(event_id, message, event, expenses, tasks)
        reply = result.get("reply", "I have received your request.")
        proposal = result.get("action_proposal")

        # Save assistant message
        EventModel.add_chat_message(event_id, "assistant", reply, action_proposal=proposal)

        return jsonify({
            "success": True,
            "reply": reply,
            "action_proposal": proposal
        })

    # --- APPLY ACTION PROPOSAL FROM CHAT ---
    @app.route("/api/events/<int:event_id>/chat/apply-action", methods=["POST"])
    @login_required
    def api_apply_chat_action(event_id):
        """Allows user to explicitly confirm and apply a proposed budget or task change from chat."""
        data = request.get_json() or {}
        action_type = data.get("type")
        
        if action_type == "add_expense":
            cat = data.get("category", "General")
            title = data.get("title", "Proposed Expense")
            amt = float(data.get("planned_amount", 0))
            notes = data.get("notes", "Applied from AI chat proposal")
            expense_id = EventModel.add_expense(event_id, cat, title, planned_amount=amt, notes=notes)
            return jsonify({"success": True, "message": f"Added expense '{title}' ({amt})", "expense_id": expense_id})

        elif action_type == "add_task":
            title = data.get("title", "Proposed Task")
            due = data.get("due_date", "")
            prio = data.get("priority", "Medium")
            cat = data.get("category", "Preparation")
            exp = data.get("explanation", "Applied from AI chat proposal")
            task_id = EventModel.add_task(event_id, title, due_date=due, priority=prio, category=cat, explanation=exp)
            return jsonify({"success": True, "message": f"Added task '{title}'", "task_id": task_id})

        return jsonify({"success": False, "message": "Unknown action type"}), 400

    # =========================================================================
    # ERROR HANDLERS
    # =========================================================================
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_error(e):
        logger.exception("Internal Server Error")
        return render_template("500.html"), 500

    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
