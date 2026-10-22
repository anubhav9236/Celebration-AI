/**
 * CelebrationAI - Multi-step Event Wizard Logic & Generative AI Handler
 */

document.addEventListener("DOMContentLoaded", () => {
    let currentStep = 1;
    const totalSteps = 5;

    const stepNodes = document.querySelectorAll(".wizard-step-node");
    const stepPanes = document.querySelectorAll(".wizard-step-pane");
    const prevBtn = document.getElementById("wizard-prev-btn");
    const nextBtn = document.getElementById("wizard-next-btn");
    const generateBtn = document.getElementById("wizard-generate-btn");
    const loadingOverlay = document.getElementById("loading-overlay");
    const loadingMessage = document.getElementById("loading-status-text");

    // Service card toggle styling
    document.querySelectorAll(".service-check-box").forEach(box => {
        const input = box.querySelector("input[type='checkbox']");
        box.addEventListener("click", (e) => {
            if (e.target !== input) {
                input.checked = !input.checked;
            }
            box.classList.toggle("checked", input.checked);
        });
        if (input.checked) box.classList.add("checked");
    });

    function updateStepUI() {
        // Step Nodes
        stepNodes.forEach((node, index) => {
            const stepNum = index + 1;
            node.classList.remove("active", "completed");
            if (stepNum === currentStep) {
                node.classList.add("active");
            } else if (stepNum < currentStep) {
                node.classList.add("completed");
            }
        });

        // Step Panes
        stepPanes.forEach((pane, index) => {
            pane.classList.toggle("active", index + 1 === currentStep);
        });

        // Button States
        if (prevBtn) {
            prevBtn.style.visibility = currentStep === 1 ? "hidden" : "visible";
        }

        if (currentStep === totalSteps) {
            if (nextBtn) nextBtn.style.display = "none";
            if (generateBtn) generateBtn.style.display = "inline-flex";
            populateReviewSummary();
        } else {
            if (nextBtn) nextBtn.style.display = "inline-flex";
            if (generateBtn) generateBtn.style.display = "none";
        }

        window.scrollTo({ top: 120, behavior: "smooth" });
    }

    function validateCurrentStep() {
        const pane = document.querySelector(`.wizard-step-pane[data-step="${currentStep}"]`);
        if (!pane) return true;

        if (currentStep === 1) {
            const title = document.getElementById("event_title")?.value.trim();
            const date = document.getElementById("event_date")?.value.trim();
            const location = document.getElementById("event_location")?.value.trim();
            const guests = parseInt(document.getElementById("guest_count")?.value || "0", 10);

            if (!title) {
                showToast("Please enter an event name.", "warning");
                return false;
            }
            if (!date) {
                showToast("Please select an event date.", "warning");
                return false;
            }
            if (!location) {
                showToast("Please specify the event location or venue.", "warning");
                return false;
            }
            if (guests <= 0) {
                showToast("Please specify an expected guest count of at least 1.", "warning");
                return false;
            }
        } else if (currentStep === 2) {
            const budget = parseFloat(document.getElementById("total_budget")?.value || "0");
            if (isNaN(budget) || budget <= 0) {
                showToast("Please enter a valid total budget amount.", "warning");
                return false;
            }
        }
        return true;
    }

    function populateReviewSummary() {
        const title = document.getElementById("event_title")?.value || "";
        const type = document.getElementById("event_type")?.value || "";
        const date = document.getElementById("event_date")?.value || "";
        const location = document.getElementById("event_location")?.value || "";
        const setting = document.querySelector("input[name='indoor_outdoor']:checked")?.value || "Indoor";
        const guests = document.getElementById("guest_count")?.value || "50";
        const budget = document.getElementById("total_budget")?.value || "0";
        const currency = document.getElementById("currency")?.value || "INR";
        const tier = document.querySelector("input[name='budget_tier']:checked")?.value || "balanced";
        const theme = document.getElementById("theme")?.value || "Personalized Elegance";
        const food = document.getElementById("food_preference")?.value || "Mixed";

        const selectedServices = Array.from(document.querySelectorAll("input[name='services']:checked")).map(cb => cb.value);

        const reviewContainer = document.getElementById("review-summary-content");
        if (!reviewContainer) return;

        const currSym = currency === "INR" ? "₹" : currency;

        reviewContainer.innerHTML = `
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:1.5rem; margin-bottom:1.5rem;">
                <div style="background:var(--color-surface-soft); padding:1.25rem; border-radius:var(--radius-md);">
                    <h5 style="color:var(--color-plum-800); margin-bottom:0.75rem;">Celebration Basics</h5>
                    <p style="font-size:0.9rem; margin-bottom:0.35rem;"><strong>Name:</strong> ${title}</p>
                    <p style="font-size:0.9rem; margin-bottom:0.35rem;"><strong>Type:</strong> ${type} (${setting})</p>
                    <p style="font-size:0.9rem; margin-bottom:0.35rem;"><strong>Date:</strong> ${date}</p>
                    <p style="font-size:0.9rem; margin-bottom:0.35rem;"><strong>Location:</strong> ${location}</p>
                    <p style="font-size:0.9rem;"><strong>Guests:</strong> ${guests} attendees</p>
                </div>
                <div style="background:var(--color-surface-soft); padding:1.25rem; border-radius:var(--radius-md);">
                    <h5 style="color:var(--color-plum-800); margin-bottom:0.75rem;">Budget & Style</h5>
                    <p style="font-size:0.9rem; margin-bottom:0.35rem;"><strong>Target Budget:</strong> ${currSym} ${Number(budget).toLocaleString()}</p>
                    <p style="font-size:0.9rem; margin-bottom:0.35rem;"><strong>Tier:</strong> <span style="text-transform:capitalize;">${tier}</span></p>
                    <p style="font-size:0.9rem; margin-bottom:0.35rem;"><strong>Theme:</strong> ${theme}</p>
                    <p style="font-size:0.9rem;"><strong>Catering Style:</strong> ${food}</p>
                </div>
            </div>
            <div style="background:var(--color-champagne-light); padding:1.25rem; border-radius:var(--radius-md); border:1px solid var(--color-champagne);">
                <h5 style="color:var(--color-plum-800); margin-bottom:0.5rem;">Requested Services (${selectedServices.length})</h5>
                <p style="font-size:0.875rem; color:var(--color-text-main);">
                    ${selectedServices.length > 0 ? selectedServices.join(" • ") : "Standard comprehensive coordination (Venue, Catering, Decor, Photography)"}
                </p>
            </div>
        `;
    }

    if (nextBtn) {
        nextBtn.addEventListener("click", () => {
            if (validateCurrentStep()) {
                currentStep++;
                updateStepUI();
            }
        });
    }

    if (prevBtn) {
        prevBtn.addEventListener("click", () => {
            if (currentStep > 1) {
                currentStep--;
                updateStepUI();
            }
        });
    }

    // Handle Generation Submit
    if (generateBtn) {
        generateBtn.addEventListener("click", async () => {
            if (!validateCurrentStep()) return;

            // Collect form data
            const selectedServices = Array.from(document.querySelectorAll("input[name='services']:checked")).map(cb => cb.value);

            const payload = {
                title: document.getElementById("event_title")?.value.trim(),
                event_type: document.getElementById("event_type")?.value,
                event_date: document.getElementById("event_date")?.value,
                start_time: document.getElementById("start_time")?.value || "",
                end_time: document.getElementById("end_time")?.value || "",
                location: document.getElementById("event_location")?.value.trim(),
                indoor_outdoor: document.querySelector("input[name='indoor_outdoor']:checked")?.value || "Indoor",
                guest_count: parseInt(document.getElementById("guest_count")?.value || "50", 10),
                total_budget: parseFloat(document.getElementById("total_budget")?.value || "50000"),
                currency: document.getElementById("currency")?.value || "INR",
                budget_tier: document.querySelector("input[name='budget_tier']:checked")?.value || "balanced",
                theme: document.getElementById("theme")?.value.trim() || "",
                color_palette: document.getElementById("color_palette")?.value.trim() || "",
                food_preference: document.getElementById("food_preference")?.value || "Mixed",
                entertainment_preference: document.getElementById("entertainment")?.value.trim() || "",
                cultural_traditions: document.getElementById("traditions")?.value.trim() || "",
                accessibility_needs: document.getElementById("accessibility")?.value.trim() || "",
                additional_notes: document.getElementById("additional_notes")?.value.trim() || "",
                services_needed: selectedServices
            };

            // Show Loading Screen with Progressive Status
            if (loadingOverlay) {
                loadingOverlay.classList.add("active");
            }

            const statusUpdates = [
                "Crafting personalized concept and theme palette...",
                "Calculating budget allocation and reserving contingency...",
                "Assembling date-aware timeline and booking milestones...",
                "Drafting vendor checklist and shopping preparations...",
                "Finalizing your celebration dashboard..."
            ];

            let statusIdx = 0;
            const statusInterval = setInterval(() => {
                statusIdx = (statusIdx + 1) % statusUpdates.length;
                if (loadingMessage) {
                    loadingMessage.textContent = statusUpdates[statusIdx];
                }
            }, 1800);

            try {
                const response = await fetch("/api/events/generate", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    },
                    body: JSON.stringify(payload)
                });

                clearInterval(statusInterval);

                const result = await response.json();

                if (response.ok && result.success) {
                    window.location.href = result.redirect_url;
                } else {
                    if (loadingOverlay) loadingOverlay.classList.remove("active");
                    const errMsg = (result.errors && result.errors.join("\n")) || result.message || "Failed to generate plan. Please try again.";
                    showToast(errMsg, "danger");
                }
            } catch (err) {
                clearInterval(statusInterval);
                if (loadingOverlay) loadingOverlay.classList.remove("active");
                showToast("Network error while generating your plan. Please try again.", "danger");
            }
        });
    }

    // Initialize initial state
    updateStepUI();
});
