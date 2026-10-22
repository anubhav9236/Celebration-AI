import json
import logging
import re
from datetime import datetime
from config import Config
from services.ai_planner import sanitize_json_response

logger = logging.getLogger(__name__)

def generate_local_chat_response(event_data: dict, user_msg: str, expenses: list, tasks: list) -> dict:
    """Generate smart context-aware responses locally when Gemini API key is not present."""
    msg_lower = user_msg.lower()
    title = event_data.get("title", "Celebration")
    event_type = event_data.get("event_type", "Event")
    budget = float(event_data.get("total_budget", 50000.0))
    currency = event_data.get("currency", "INR")
    curr_sym = "₹" if currency == "INR" else ("$" if currency == "USD" else currency)
    guests = event_data.get("guest_count", 50)
    food_pref = event_data.get("food_preference", "Mixed")

    total_actual = sum(float(e.get("actual_amount", 0.0)) for e in expenses)
    total_planned = sum(float(e.get("planned_amount", 0.0)) for e in expenses)

    # 1. Budget Saving Inquiry (e.g. "How can I save ₹5,000 on this wedding?")
    if any(w in msg_lower for w in ["save", "cut cost", "reduce budget", "cheaper", "discount"]):
        reply = f"""Here are targeted strategies to save costs on **{title}** without compromising quality:

1. **Repurpose Floral & Stage Decor:** Transition entryway flowers into dining table centerpieces after the ceremony. This typically saves 15–20% on overall floral costs.
2. **Curated Buffet Timing:** For {guests} guests, standardizing the menu with 2 high-impact signature dishes rather than 6 overlapping gravies cuts catering costs by ~{curr_sym}4,000–{curr_sym}8,000.
3. **Digital-First Invitations:** Use digital interactive invitations with RSVP tracking, printing physical keepsakes only for immediate family elders.
4. **Daytime or Off-Peak Venue Slots:** Daytime celebrations significantly reduce heavy artificial stage lighting requirements.
5. **Corkage / Beverage Negotiation:** Bringing your own branded mocktail syrups or wholesale juices often saves {curr_sym}3,000+ over hotel bar rates."""
        return {"reply": reply, "action_proposal": None}

    # 2. Menu Suggestions (e.g. "Suggest a vegetarian menu for 50 guests")
    elif any(w in msg_lower for w in ["menu", "food", "catering", "vegetarian", "dish", "dishes", "snack"]):
        reply = f"""Here is a curated **{food_pref}** menu designed for **{guests} guests** at {title}:

* **Welcome Drinks:** Spiced Cranberry Punch, Fresh Mint-Lime Mojito, or Badam Milk.
* **Appetizers & Starters (Live Counter):**
  - Crispy Paneer/Tofu Tikka with mint chutney
  - Mini Vegetable Sliders or Corn Cheese Croquettes
  - Classic Sev Puri / Golgappa live counter
* **Main Course:**
  - Paneer Butter Masala or Rich Mughlai Kofta
  - Dal Makhani (slow cooked overnight) or Homestyle Tadka Dal
  - Seasonal Vegetable Melange / Kashmiri Dum Aloo
  - Assorted Breads (Butter Naan, Laccha Paratha, Roti)
  - Fragrant Dum Biryani / Jeera Rice with Cucumber Pomegranate Raita
* **Dessert Platter:** Warm Gulab Jamun paired with artisanal vanilla bean gelato, and Rasmalai bowls."""
        return {"reply": reply, "action_proposal": None}

    # 3. Rain or Weather Contingency (e.g. "Suggest indoor activities if it rains")
    elif any(w in msg_lower for w in ["rain", "weather", "indoor", "rainy", "storm", "wet"]):
        proposal = {
            "type": "add_task",
            "title": "Confirm Venue Rain Shield / Reserve Indoor Pavilion",
            "due_date": event_data.get("event_date", ""),
            "priority": "High",
            "category": "Preparation",
            "explanation": "Ensure indoor banquet hall or waterproof marquee is on standby for sudden rain."
        }
        reply = f"""### Weather & Rain Contingency Plan for {title}:

1. **Space Allocation:** Move social games and dining into the covered courtyard or main hall.
2. **Cozy Indoor Activities:**
   - **Interactive Trivia & Milestone Spotlight:** Project funny family photos or attendee trivia on a projector screen.
   - **Live Acoustic Station:** Create an unplugged acoustic music lounge with comfortable beanbags and floor cushions.
   - **Instant Polaroid Wall:** Hand guests instant cameras to capture indoor candid moments.
3. **Logistics Check:** Position umbrella drop buckets and non-slip mats at all entry thresholds.

*I have prepared an actionable task below. Click **Apply to Timeline** if you want to add it to your schedule.*"""
        return {"reply": reply, "action_proposal": proposal}

    # 4. Weekly Tasks / What should I complete (e.g. "What should I complete this week?")
    elif any(w in msg_lower for w in ["this week", "next", "what should i do", "task", "urgent", "upcoming"]):
        pending = [t for t in tasks if not t.get("is_completed")]
        if pending:
            task_list = "\n".join([f"- **{t.get('title')}** (Due: {t.get('due_date', 'TBD')} | Priority: {t.get('priority', 'Medium')})" for t in pending[:5]])
            reply = f"""Here are your priority action items for **{title}**:

{task_list}

**Tip:** Focus on finalizing contracts with key vendors first, as booking dates fill up quickly."""
        else:
            reply = f"Great news! All scheduled tasks for **{title}** are currently marked as complete. You are well ahead of schedule!"
        return {"reply": reply, "action_proposal": None}

    # 5. Budget Recalculation / Expense Addition (e.g. "Recalculate my budget after adding ₹2,000 for photography")
    elif any(w in msg_lower for w in ["recalculate", "add", "increase", "photography", "expense", "spend"]):
        # Extract amount if present
        amt_match = re.search(r"(\d+[\d,]*)", user_msg)
        add_amt = float(amt_match.group(1).replace(",", "")) if amt_match else 2000.0
        
        category = "Photography" if "photo" in msg_lower else ("Catering" if "food" in msg_lower or "cater" in msg_lower else "General")
        
        proposal = {
            "type": "add_expense",
            "category": category,
            "title": f"Additional {category} Allocation",
            "planned_amount": add_amt,
            "notes": f"Proposed via CelebrationAI Chat on {datetime.now().strftime('%b %d')}"
        }

        new_planned = total_planned + add_amt
        remaining = budget - new_planned

        reply = f"""I have modeled this budget adjustment for you:

* **Current Total Budget:** {curr_sym}{budget:,.2f}
* **Current Planned Total:** {curr_sym}{total_planned:,.2f}
* **Proposed Addition:** {curr_sym}{add_amt:,.2f} for **{category}**
* **Projected Planned Total:** {curr_sym}{new_planned:,.2f}
* **Projected Remaining Buffer:** {curr_sym}{remaining:,.2f} ({'Healthy buffer remaining' if remaining >= 0 else '⚠️ Exceeds current total budget by ' + curr_sym + str(abs(remaining))})

Review the proposed expense item below and click **Add Expense** to apply it safely."""
        return {"reply": reply, "action_proposal": proposal}

    # Generic Helpful Response
    else:
        reply = f"""I am here to help you coordinate every detail of **{title}** ({event_type} on {event_data.get('event_date', 'TBD')}).

You can ask me to:
- **Analyze expenses:** *"How can we optimize our budget?"*
- **Create menus:** *"Suggest a {food_pref} 3-course menu for {guests} guests"*
- **Solve logistics:** *"What should I prepare for day-of emergency kit?"*
- **Adjust numbers:** *"Add {curr_sym}3,000 for floral centerpiece upgrades"*

What aspect of your celebration would you like to refine next?"""
        return {"reply": reply, "action_proposal": None}

def answer_event_chat(event_id: int, user_message: str, event_data: dict, expenses: list, tasks: list) -> dict:
    """Processes event assistant chat, calling Gemini API if available with local fallback."""
    api_key = Config.GEMINI_API_KEY
    if not api_key or api_key == "your_gemini_api_key_here":
        return generate_local_chat_response(event_data, user_message, expenses, tasks)

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        context_summary = f"""
Event: {event_data.get('title')} ({event_data.get('event_type')})
Date: {event_data.get('event_date')}
Location: {event_data.get('location')}
Guests: {event_data.get('guest_count')}
Total Budget: {event_data.get('currency', 'INR')} {event_data.get('total_budget')}
Planned Expenses: {sum(float(e.get('planned_amount', 0)) for e in expenses)}
Actual Spent: {sum(float(e.get('actual_amount', 0)) for e in expenses)}
Food Preferences: {event_data.get('food_preference')}
Pending Tasks Count: {len([t for t in tasks if not t.get('is_completed')])}
"""

        prompt = f"""
You are CelebrationAI Assistant, an experienced, warm, and highly practical event planner.
Answer the user's inquiry based on this event's context:

{context_summary}

User Query: "{user_message}"

CRITICAL INSTRUCTIONS:
1. Provide a concise, polite, actionable response formatted with clean markdown.
2. If the user asks to modify, recalculate, or add an expense or task, DO NOT claim you edited the database. Instead, provide the proposed item inside the "action_proposal" field so the user can review and approve it.
3. Return ONLY valid JSON with keys:
   - "reply": "string markdown response"
   - "action_proposal": null OR {{"type": "add_expense"|"add_task", "category": "...", "title": "...", "planned_amount": 0.0, "notes": "..."}}
"""

        response = client.models.generate_content(
            model=Config.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.6,
            )
        )

        clean = sanitize_json_response(response.text)
        res = json.loads(clean)
        return {
            "reply": res.get("reply", "I have reviewed your celebration details."),
            "action_proposal": res.get("action_proposal")
        }

    except Exception as e:
        logger.warning(f"Gemini chat failed ({e}), using local rule engine.")
        return generate_local_chat_response(event_data, user_message, expenses, tasks)
