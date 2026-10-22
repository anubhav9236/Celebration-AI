import json
import logging
import re
from datetime import datetime, timedelta
from config import Config

logger = logging.getLogger(__name__)

def sanitize_json_response(raw_text: str) -> str:
    """Extract JSON object from potential markdown wrapping or text."""
    text = raw_text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()

def calculate_budget_breakdown(total_budget: float, services_needed: list, budget_tier: str = "balanced", event_type: str = "Wedding") -> list:
    """
    Computes mathematically rigorous, realistic budget allocations ensuring
    total spending + contingency strictly <= total_budget.
    """
    total = max(1000.0, float(total_budget))
    
    # Base weight allocations based on event type and selected services
    weights = {
        "Venue": 25.0,
        "Catering": 30.0,
        "Decoration": 15.0,
        "Photography": 10.0,
        "Videography": 5.0,
        "Music or DJ": 5.0,
        "Invitations": 2.0,
        "Cake and desserts": 3.0,
        "Transportation": 2.0,
        "Accommodation": 5.0,
        "Gifts and favors": 3.0,
    }

    # Adjust if specific services were requested
    active_services = [s for s in services_needed if s in weights] if services_needed else list(weights.keys())[:6]
    
    # Add contingency reserve (8% for balanced, 10% for premium, 5% for budget)
    contingency_pct = 10.0 if budget_tier == "premium" else (5.0 if budget_tier == "budget" else 8.0)
    allocable_pct = 100.0 - contingency_pct

    # Filter weights to active services
    selected_weights = {k: weights[k] for k in active_services}
    if not selected_weights:
        selected_weights = {"Venue": 30.0, "Catering": 40.0, "Decoration": 20.0, "Photography": 10.0}

    total_weight = sum(selected_weights.values())
    
    breakdown = []
    accumulated_spent = 0.0

    for idx, (cat, w) in enumerate(selected_weights.items()):
        pct = round((w / total_weight) * allocable_pct, 1)
        amt = round(total * (pct / 100.0), 2)
        accumulated_spent += amt
        
        reasons = {
            "Venue": f"Securing optimal space for {budget_tier} experience and guest comfort",
            "Catering": "Curated multi-course dining, beverages, service staff and table setup",
            "Decoration": "Stage backdrop, table centerpieces, entryway floral arrangements and lighting",
            "Photography": "Professional candid and portrait event coverage and edited deliverables",
            "Videography": "Cinematic highlights reel and full ceremony documentary video",
            "Music or DJ": "Sound system, lighting rig, curated playlist or live performer",
            "Invitations": "Digital interactive invitations and formal print stationery",
            "Cake and desserts": "Custom themed celebration cake and assorted dessert bar",
            "Transportation": "Guest shuttle or VIP family transport logistics",
            "Accommodation": "Reserved rooms for key out-of-town guests",
            "Gifts and favors": "Personalized return gifts and keepsake tokens of appreciation"
        }

        breakdown.append({
            "category": cat,
            "title": f"{cat} Reservation & Setup",
            "percentage": pct,
            "estimated_amount": amt,
            "reason": reasons.get(cat, f"Allocation for professional {cat.lower()} services")
        })

    # Add Contingency Reserve
    contingency_amt = round(total - accumulated_spent, 2)
    if contingency_amt > 0:
        breakdown.append({
            "category": "Contingency Fund",
            "title": "Emergency & Miscellaneous Buffer",
            "percentage": round((contingency_amt / total) * 100.0, 1),
            "estimated_amount": contingency_amt,
            "reason": "Reserved buffer for last-minute guest additions, weather adjustments, or tips"
        })

    return breakdown

def generate_date_aware_timeline(event_date_str: str, event_type: str = "Wedding") -> list:
    """Generates chronologically aligned milestones counting back from the target event date."""
    try:
        event_date = datetime.strptime(event_date_str, "%Y-%m-%d").date()
    except Exception:
        event_date = (datetime.now() + timedelta(days=60)).date()

    today = datetime.now().date()
    days_until = (event_date - today).days

    if days_until < 0:
        note_prefix = "Note: Target date is in the past. Update date for future planning. "
    else:
        note_prefix = ""

    # Scale milestone steps depending on lead time
    milestones = []
    
    if days_until > 90 or event_type in ["Wedding", "College Festival"]:
        m_dates = [
            (days_until - 120, "Venue & Date Finalization", "High", "Booking", "Lock down venue contract and verify deposit terms."),
            (days_until - 90, "Primary Catering & Photographer Tasting", "High", "Booking", "Sample menu items, review photo portfolio, and confirm dietary options."),
            (days_until - 60, "Invitations Dispatched & RSVP Tracking", "Medium", "Invitations", "Send out digital and physical invitations; open RSVP portal."),
            (days_until - 30, "Theme Decor & Floral Design Sign-off", "Medium", "Preparation", "Review mockups for stage, florals, color swatches, and lighting."),
            (days_until - 14, "Vendor Coordination & Schedule Briefing", "High", "Coordination", "Distribute minute-by-minute rundown to all coordinators and vendors."),
            (days_until - 3, "Final Headcount & Rehearsal", "High", "Final Prep", "Confirm final attendee count with caterer and check audiovisual systems."),
            (0, "Event Day Execution & Welcome", "High", "Day-Of", "Setup inspection, welcome drinks, program execution, and memorable celebration!"),
            (-1, "Vendor Settlement & Thank You Notes", "Low", "Post-Event", "Clear remaining balance invoices and dispatch thank-you messages to attendees.")
        ]
    else:
        # Shorter lead time (e.g. Birthday, Anniversary, Dinner)
        m_dates = [
            (max(1, int(days_until * 0.8)), "Select Theme & Book Venue", "High", "Booking", "Choose venue space or home arrangement matching theme."),
            (max(1, int(days_until * 0.6)), "Send Invitations & Confirm Cake", "High", "Invitations", "Share invite link and pre-order customized celebration cake."),
            (max(1, int(days_until * 0.4)), "Plan Menu & Entertainment Playlist", "Medium", "Preparation", "Finalize snacks, main course, party games, and playlist."),
            (max(1, int(days_until * 0.2)), "Decorations Shopping & Pickups", "Medium", "Shopping", "Purchase party supplies, balloons, lighting, and return favors."),
            (1, "Day-Before Preparation & Room Setup", "High", "Final Prep", "Decorate space, test audio speaker, chill beverages."),
            (0, "Celebration Time!", "High", "Day-Of", "Host guests, capture photos, cut cake, and enjoy the party!"),
            (-1, "Photo Sharing & Clean-up", "Low", "Post-Event", "Send photo album link to guests and wrap up equipment.")
        ]

    for offset, title, prio, cat, exp in m_dates:
        target_d = event_date - timedelta(days=offset)
        milestones.append({
            "task": title,
            "due_date": target_d.strftime("%Y-%m-%d"),
            "priority": prio,
            "category": cat,
            "explanation": f"{note_prefix}{exp}"
        })

    return milestones

def generate_local_plan(event_data: dict) -> dict:
    """
    Intelligent contextual rule-based planner generating bespoke plans
    when GEMINI_API_KEY is not configured or offline.
    """
    event_type = event_data.get("event_type", "Celebration")
    title = event_data.get("title", f"{event_type} Celebration")
    budget = float(event_data.get("total_budget", 50000.0))
    currency = event_data.get("currency", "INR")
    currency_symbol = "₹" if currency == "INR" else ("$" if currency == "USD" else currency)
    guests = int(event_data.get("guest_count", 50))
    tier = event_data.get("budget_tier", "balanced")
    food_pref = event_data.get("food_preference", "Mixed")
    location = event_data.get("location", "Local Venue")
    services = event_data.get("services_needed", [])

    # Thematic concepts based on celebration type
    theme_catalog = {
        "Wedding": {
            "theme": "Regal Blossom & Ivory Splendor",
            "palette": ["#4A1525", "#C5A059", "#FAF8F5", "#8E2848", "#E6CA65"],
            "decor": "Rich burgundy velvet drapes, warm golden ambient fairy lighting, brass urns with fresh jasmine and blush roses, and a geometric floral archway.",
            "atmosphere": "Elegantly grand, romantic, and culturally resonant with comfortable lounge seating and acoustic instrumentals.",
            "tips": f"For {guests} guests, buffet stations with staggered live counters prevent queuing. Booking your venue 3 months ahead unlocks early bird discounts."
        },
        "Birthday": {
            "theme": "Golden Hour Garden Soirée",
            "palette": ["#5E1931", "#E6CA65", "#FFFDF9", "#3A5A40", "#DDA15E"],
            "decor": "Fairy lights strung across open-air pergolas, custom neon name signage, botanical greenery walls, and rustic wooden accent tables.",
            "atmosphere": "Lively, celebratory, and photogenic with interactive mocktail stations and curated background beats.",
            "tips": f"A dedicated photo booth backdrop with polaroid prints doubles as both guest entertainment and take-home party favors."
        },
        "Anniversary": {
            "theme": "Silver & Champagne Candlelit Symphony",
            "palette": ["#4A1525", "#D4AF37", "#F5F1EB", "#6B1D36", "#C0C0C0"],
            "decor": "Taper candles in vintage glass holders, cascading white orchid arrangements, mirrored table runners, and personalized memory timeline board.",
            "atmosphere": "Intimate, warm, and sophisticated celebrating shared milestones with a curated retrospective video and champagne toast.",
            "tips": "Request a quiet enclave or semi-private terrace dining to keep speeches and toasts personal and audible."
        },
        "College Festival": {
            "theme": "Neon Horizon: Future Beats & Culture",
            "palette": ["#721D3B", "#FF6B6B", "#4ECDC4", "#1A1A24", "#FFE66D"],
            "decor": "UV reactive banners, modular stage trusses with laser effects, graffiti art photo installations, and eco-friendly crowd seating.",
            "atmosphere": "High energy, creative, and collaborative with battle of bands, hackathon pavilions, and student food pop-ups.",
            "tips": "Appoint student volunteer heads for stage, sound, security, and registration to ensure crisp schedule transitions."
        },
        "Community Gathering": {
            "theme": "Harmony & Heritage Community Feast",
            "palette": ["#6B1D36", "#C5A059", "#2B4C3F", "#F7F2EB", "#E76F51"],
            "decor": "Festive fabric canopies, community story boards, sustainable bamboo table settings, and colorful hanging lanterns.",
            "atmosphere": "Inclusive, warm, intergenerational, and community-affirming with shared storytelling and local artisan showcases.",
            "tips": "Ensure barrier-free wheelchair access, clear signage in multiple languages, and shaded seating for elderly community members."
        }
    }

    concept = theme_catalog.get(event_type, theme_catalog["Wedding"])

    # Compute mathematically verified budget breakdown
    breakdown = calculate_budget_breakdown(budget, services, budget_tier=tier, event_type=event_type)
    
    # Calculate totals
    total_planned = sum(item["estimated_amount"] for item in breakdown)
    remaining = round(budget - total_planned, 2)
    utilization = round((total_planned / budget) * 100.0, 1)

    # Date-aware timeline
    timeline = generate_date_aware_timeline(event_data.get("event_date", ""), event_type=event_type)

    # Vendor checklist tailored to event
    vendors = [
        {
            "category": "Venue & Facilities",
            "why_needed": f"Accommodates {guests} guests with proper ventilation, washrooms, and parking",
            "deadline": "6-8 weeks before event",
            "estimated_budget": next((b["estimated_amount"] for b in breakdown if b["category"] == "Venue"), budget * 0.25),
            "status": "Needed"
        },
        {
            "category": "Catering & Beverages",
            "why_needed": f"Provides curated {food_pref} menu with high food safety and warm hospitality",
            "deadline": "4 weeks before event",
            "estimated_budget": next((b["estimated_amount"] for b in breakdown if b["category"] == "Catering"), budget * 0.30),
            "status": "Needed"
        },
        {
            "category": "Decor & Lighting",
            "why_needed": f"Executes the {concept['theme']} aesthetic, stage, backdrop, and table florals",
            "deadline": "3 weeks before event",
            "estimated_budget": next((b["estimated_amount"] for b in breakdown if b["category"] == "Decoration"), budget * 0.15),
            "status": "Needed"
        },
        {
            "category": "Photographer / Videographer",
            "why_needed": "Captures spontaneous candid memories, ceremony milestones, and group portraits",
            "deadline": "4 weeks before event",
            "estimated_budget": next((b["estimated_amount"] for b in breakdown if b["category"] == "Photography"), budget * 0.10),
            "status": "Needed"
        },
        {
            "category": "Music & Audio",
            "why_needed": "Professional sound amplification, speech microphones, and celebratory playlist",
            "deadline": "2 weeks before event",
            "estimated_budget": next((b["estimated_amount"] for b in breakdown if b["category"] == "Music or DJ"), budget * 0.05),
            "status": "Needed"
        }
    ]

    # Personalized ideas
    ideas = [
        {
            "category": "Decor",
            "title": f"Focal Photo Backdrop: {concept['theme']}",
            "description": "Construct an arched floral frame adorned with warm Edison bulbs and personalized monogram lettering for iconic guest photos."
        },
        {
            "category": "Food & Menu",
            "title": f"Signature {food_pref} Tasting Stations",
            "description": "Pair traditional regional delicacies with interactive live counters (e.g. chaat/tapas, artisanal beverages, and miniature warm desserts)."
        },
        {
            "category": "Activities",
            "title": "Interactive Memory Guestbook & Trivia",
            "description": "Set up a visual memory clothesline where guests pin polaroids with handwritten wishes and solve an event trivia quiz."
        },
        {
            "category": "Entertainment",
            "title": "Acoustic Melody Transitioning to High Energy",
            "description": "Begin with acoustic guitar or instrumental sitar during guest arrival, transitioning into an upbeat playlist for the celebration finale."
        },
        {
            "category": "Return Gifts",
            "title": "Eco-friendly Artisan Favors",
            "description": "Offer guests potted succulent plants or handmade scented soy wax candles in brass tins with custom thank-you tags."
        },
        {
            "category": "Budget Savings",
            "title": "Smart Repurposing & Digital Stationery",
            "description": "Transition ceremony floral arrangements into dinner table centerpieces to save up to 20% on decoration expenses."
        }
    ]

    # Checklist items
    checklist = [
        {"category": "Stationery", "item": "Design & send digital RSVP invitation links", "estimated_cost": 500.0, "notes": "Track dietary needs"},
        {"category": "Attire", "item": "Finalize celebration outfits and fittings", "estimated_cost": 0.0, "notes": "Allow 1 week buffer for alterations"},
        {"category": "Decor", "item": "Source fairy lights, candles, and signage stands", "estimated_cost": 2500.0, "notes": "Test lighting beforehand"},
        {"category": "Food", "item": "Sample and finalize cake flavor & tiered presentation", "estimated_cost": 3000.0, "notes": "Include eggless/gluten-free slice if needed"},
        {"category": "Logistics", "item": "Prepare emergency kit (safety pins, tapes, first aid, power banks)", "estimated_cost": 800.0, "notes": "Keep at registration table"},
        {"category": "Favors", "item": "Package return gifts with custom handwritten notes", "estimated_cost": 3500.0, "notes": "Count matched to confirmed RSVPs"}
    ]

    return {
        "success": True,
        "is_demo": True,
        "mode_label": "Local Rule-Based Heuristics (Configure GEMINI_API_KEY for live Gemini 2.5 Flash)",
        "message": "Plan generated using CelebrationAI's intelligent local planning engine. To enable live Gemini generation, add your GEMINI_API_KEY to .env.",
        "concept": concept,
        "budget_breakdown": breakdown,
        "budget_summary": {
            "total_budget": budget,
            "planned_expenses": total_planned,
            "remaining_budget": remaining,
            "utilization_percent": utilization,
            "currency": currency,
            "currency_symbol": currency_symbol
        },
        "timeline": timeline,
        "vendors": vendors,
        "ideas": ideas,
        "checklist": checklist
    }

def generate_gemini_plan(event_data: dict, api_key: str) -> dict:
    """
    Calls Google Gemini using the official google.genai SDK to generate
    a comprehensive structured event plan.
    """
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        prompt = f"""
You are CelebrationAI, an expert luxury and community event planner. Generate a comprehensive, realistic, and culturally sensitive event plan in valid JSON format.

Event Specifications:
- Title: {event_data.get('title')}
- Type of Event: {event_data.get('event_type')}
- Event Date: {event_data.get('event_date')}
- Location: {event_data.get('location')}
- Setting: {event_data.get('indoor_outdoor', 'Indoor')}
- Expected Guests: {event_data.get('guest_count', 50)}
- Total Budget: {event_data.get('currency', 'INR')} {event_data.get('total_budget')}
- Budget Tier: {event_data.get('budget_tier', 'balanced')}
- Preferred Theme/Style: {event_data.get('theme', 'Personalized & Elegant')}
- Dietary / Food Preferences: {event_data.get('food_preference', 'Mixed')}
- Cultural Traditions: {event_data.get('cultural_traditions', 'Respectful of attendee traditions')}
- Entertainment: {event_data.get('entertainment_preference', 'Music & social')}
- Services Needed: {event_data.get('services_needed', [])}
- Additional Notes: {event_data.get('additional_notes', '')}

CRITICAL RULES:
1. Return ONLY valid JSON with no markdown wrapping or extra commentary.
2. The total sum of estimated expenses in budget_breakdown MUST NOT EXCEED the total budget.
3. Reserve a contingency buffer of approximately 5-10% of total budget.
4. Do NOT invent real company names, phone numbers, or fake URLs.
5. All dates in the timeline must be relative to the event date ({event_data.get('event_date')}). Format as YYYY-MM-DD.
6. Provide specific, culturally respectful food items and creative decor matching the user's specific inputs.

Return this EXACT JSON structure:
{{
  "concept": {{
    "theme": "Specific personalized theme name",
    "palette": ["#HEX1", "#HEX2", "#HEX3", "#HEX4", "#HEX5"],
    "decor": "Detailed decoration concept including stage, floral, lighting, and entry",
    "atmosphere": "Detailed description of the mood and guest journey",
    "tips": "Practical budget-maximizing suggestions"
  }},
  "budget_breakdown": [
    {{
      "category": "Venue",
      "title": "Venue Hall / Grounds Booking",
      "percentage": 25.0,
      "estimated_amount": 25000.0,
      "reason": "Detailed justification"
    }}
  ],
  "timeline": [
    {{
      "task": "Task name",
      "due_date": "YYYY-MM-DD",
      "priority": "High|Medium|Low",
      "category": "Booking|Preparation|Shopping|Day-Of|Post-Event",
      "explanation": "Why this must be completed by this date"
    }}
  ],
  "vendors": [
    {{
      "category": "Category name",
      "why_needed": "Explanation",
      "deadline": "Suggested timeframe",
      "estimated_budget": 10000.0,
      "status": "Needed"
    }}
  ],
  "ideas": [
    {{
      "category": "Decor|Food & Menu|Activities|Entertainment|Return Gifts|Budget Savings",
      "title": "Idea headline",
      "description": "Specific actionable description"
    }}
  ],
  "checklist": [
    {{
      "category": "Supplies|Attire|Gifts|Stationery|Day-of Essentials",
      "item": "Checklist item",
      "estimated_cost": 500.0,
      "notes": "Actionable tip"
    }}
  ]
}}
"""

        response = client.models.generate_content(
            model=Config.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.7,
            )
        )

        clean_text = sanitize_json_response(response.text)
        data = json.loads(clean_text)

        # Enforce server-side arithmetic sanity check
        total_budget = float(event_data.get("total_budget", 50000.0))
        breakdown = data.get("budget_breakdown", [])
        
        # Verify and rebalance if AI math is off
        total_planned = sum(float(item.get("estimated_amount", 0.0)) for item in breakdown)
        if total_planned > total_budget or len(breakdown) == 0:
            logger.info("Rebalancing AI budget breakdown to strictly honor total budget constraint.")
            breakdown = calculate_budget_breakdown(
                total_budget,
                event_data.get("services_needed", []),
                budget_tier=event_data.get("budget_tier", "balanced"),
                event_type=event_data.get("event_type", "Celebration")
            )
            data["budget_breakdown"] = breakdown
            total_planned = sum(item["estimated_amount"] for item in breakdown)

        currency = event_data.get("currency", "INR")
        currency_symbol = "₹" if currency == "INR" else ("$" if currency == "USD" else currency)

        return {
            "success": True,
            "is_demo": False,
            "mode_label": f"Live Gemini AI ({Config.GEMINI_MODEL})",
            "message": "Personalized event plan successfully generated using Google Gemini AI.",
            "concept": data.get("concept", {}),
            "budget_breakdown": breakdown,
            "budget_summary": {
                "total_budget": total_budget,
                "planned_expenses": total_planned,
                "remaining_budget": round(total_budget - total_planned, 2),
                "utilization_percent": round((total_planned / total_budget) * 100.0, 1),
                "currency": currency,
                "currency_symbol": currency_symbol
            },
            "timeline": data.get("timeline", []),
            "vendors": data.get("vendors", []),
            "ideas": data.get("ideas", []),
            "checklist": data.get("checklist", [])
        }

    except Exception as e:
        logger.warning(f"Gemini API invocation failed or key invalid: {str(e)}. Falling back to local planner heuristics.")
        fallback = generate_local_plan(event_data)
        fallback["mode_label"] = "Local Heuristics (Gemini API unavailable or key expired)"
        fallback["message"] = f"Generated via local planning engine: {str(e)[:120]}"
        return fallback

def generate_event_plan(event_data: dict) -> dict:
    """
    Main entry point for generating an event plan.
    Routes to live Gemini if GEMINI_API_KEY is present; otherwise routes to local planner.
    """
    api_key = Config.GEMINI_API_KEY
    if api_key and api_key != "your_gemini_api_key_here":
        return generate_gemini_plan(event_data, api_key)
    else:
        return generate_local_plan(event_data)
