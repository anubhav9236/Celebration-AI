/**
 * CelebrationAI - Event Dashboard Interactive Tab Logic & Visualizations
 */

document.addEventListener("DOMContentLoaded", () => {
    const eventIdMeta = document.getElementById("event-meta-id");
    if (!eventIdMeta) return;
    const eventId = eventIdMeta.value;

    // =========================================================================
    // TAB NAVIGATION
    // =========================================================================
    const tabButtons = document.querySelectorAll(".tab-btn");
    const tabPanes = document.querySelectorAll(".tab-pane");

    function switchTab(targetTabId) {
        tabButtons.forEach(btn => {
            btn.classList.toggle("active", btn.dataset.tab === targetTabId);
        });
        tabPanes.forEach(pane => {
            pane.classList.toggle("active", pane.id === `tab-${targetTabId}`);
        });

        // Update URL query string without reloading
        const url = new URL(window.location);
        url.searchParams.set("tab", targetTabId);
        window.history.replaceState({}, "", url);

        if (window.lucide) window.lucide.createIcons();

        // Trigger chart render if budget tab is selected
        if (targetTabId === "budget" && window.renderBudgetCharts) {
            window.renderBudgetCharts();
        }
    }

    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            switchTab(btn.dataset.tab);
        });
    });

    // Check URL query param on page load
    const initialTab = new URLSearchParams(window.location.search).get("tab") || "overview";
    switchTab(initialTab);

    // =========================================================================
    // MODAL HELPERS
    // =========================================================================
    window.openModal = function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add("open");
            if (window.lucide) window.lucide.createIcons();
        }
    };

    window.closeModal = function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) modal.classList.remove("open");
    };

    // Close modal on background click
    document.querySelectorAll(".modal-overlay").forEach(overlay => {
        overlay.addEventListener("click", (e) => {
            if (e.target === overlay) overlay.classList.remove("open");
        });
    });

    // =========================================================================
    // EXPENSE MANAGEMENT
    // =========================================================================
    const expenseForm = document.getElementById("form-add-expense");
    if (expenseForm) {
        expenseForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const payload = {
                category: document.getElementById("exp_category").value,
                title: document.getElementById("exp_title").value.trim(),
                planned_amount: parseFloat(document.getElementById("exp_planned").value || 0),
                actual_amount: parseFloat(document.getElementById("exp_actual").value || 0),
                status: document.getElementById("exp_status").value,
                notes: document.getElementById("exp_notes").value.trim()
            };

            try {
                const res = await fetch(`/api/events/${eventId}/expenses`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (data.success) {
                    showToast("Expense item added successfully!", "success");
                    setTimeout(() => window.location.reload(), 600);
                } else {
                    showToast(data.message || "Failed to add expense.", "danger");
                }
            } catch (err) {
                showToast("Network error. Please try again.", "danger");
            }
        });
    }

    window.deleteExpense = async function(expenseId) {
        if (!confirm("Are you sure you want to remove this expense item?")) return;
        try {
            const res = await fetch(`/api/events/${eventId}/expenses/${expenseId}`, { method: "DELETE" });
            const data = await res.json();
            if (data.success) {
                showToast("Expense removed.", "info");
                setTimeout(() => window.location.reload(), 500);
            }
        } catch (err) {
            showToast("Failed to delete expense.", "danger");
        }
    };

    // =========================================================================
    // TIMELINE TASK MANAGEMENT
    // =========================================================================
    const taskForm = document.getElementById("form-add-task");
    if (taskForm) {
        taskForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const payload = {
                title: document.getElementById("task_title").value.trim(),
                due_date: document.getElementById("task_due_date").value,
                priority: document.getElementById("task_priority").value,
                category: document.getElementById("task_category").value,
                explanation: document.getElementById("task_explanation").value.trim()
            };

            try {
                const res = await fetch(`/api/events/${eventId}/tasks`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (data.success) {
                    showToast("Timeline milestone added!", "success");
                    setTimeout(() => window.location.reload(), 600);
                } else {
                    showToast(data.message || "Failed to add task.", "danger");
                }
            } catch (err) {
                showToast("Network error.", "danger");
            }
        });
    }

    window.toggleTask = async function(taskId, el) {
        try {
            const res = await fetch(`/api/events/${eventId}/tasks/${taskId}/toggle`, { method: "POST" });
            const data = await res.json();
            if (data.success) {
                const row = document.getElementById(`task-row-${taskId}`);
                if (row) {
                    row.style.opacity = data.is_completed ? "0.6" : "1";
                    row.classList.toggle("completed-task", data.is_completed);
                }
                showToast(data.is_completed ? "Task completed! 🎉" : "Task marked pending.", "success");
            }
        } catch (err) {
            showToast("Failed to toggle task.", "danger");
        }
    };

    window.deleteTask = async function(taskId) {
        if (!confirm("Are you sure you want to delete this task?")) return;
        try {
            const res = await fetch(`/api/events/${eventId}/tasks/${taskId}`, { method: "DELETE" });
            const data = await res.json();
            if (data.success) {
                showToast("Task removed.", "info");
                setTimeout(() => window.location.reload(), 500);
            }
        } catch (err) {
            showToast("Failed to remove task.", "danger");
        }
    };

    // =========================================================================
    // VENDOR MANAGEMENT
    // =========================================================================
    const vendorForm = document.getElementById("form-add-vendor");
    if (vendorForm) {
        vendorForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const payload = {
                category: document.getElementById("vendor_category").value,
                name: document.getElementById("vendor_name").value.trim(),
                contact_info: document.getElementById("vendor_contact").value.trim(),
                estimated_cost: parseFloat(document.getElementById("vendor_est_cost").value || 0),
                actual_cost: parseFloat(document.getElementById("vendor_act_cost").value || 0),
                booking_status: document.getElementById("vendor_booking_status").value,
                payment_status: document.getElementById("vendor_payment_status").value,
                deadline: document.getElementById("vendor_deadline").value,
                notes: document.getElementById("vendor_notes").value.trim()
            };

            try {
                const res = await fetch(`/api/events/${eventId}/vendors`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (data.success) {
                    showToast("Vendor profile added!", "success");
                    setTimeout(() => window.location.reload(), 600);
                } else {
                    showToast(data.message || "Failed to add vendor.", "danger");
                }
            } catch (err) {
                showToast("Network error.", "danger");
            }
        });
    }

    window.updateVendorStatus = async function(vendorId, newStatus) {
        try {
            const res = await fetch(`/api/events/${eventId}/vendors/${vendorId}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ booking_status: newStatus })
            });
            const data = await res.json();
            if (data.success) {
                showToast("Vendor status updated.", "success");
            }
        } catch (err) {
            showToast("Failed to update vendor.", "danger");
        }
    };

    window.deleteVendor = async function(vendorId) {
        if (!confirm("Are you sure you want to remove this vendor record?")) return;
        try {
            const res = await fetch(`/api/events/${eventId}/vendors/${vendorId}`, { method: "DELETE" });
            const data = await res.json();
            if (data.success) {
                showToast("Vendor removed.", "info");
                setTimeout(() => window.location.reload(), 500);
            }
        } catch (err) {
            showToast("Failed to remove vendor.", "danger");
        }
    };

    // =========================================================================
    // GUEST MANAGEMENT
    // =========================================================================
    const guestForm = document.getElementById("form-add-guest");
    if (guestForm) {
        guestForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const payload = {
                name: document.getElementById("guest_name").value.trim(),
                email_or_phone: document.getElementById("guest_contact").value.trim(),
                rsvp_status: document.getElementById("guest_rsvp").value,
                attendees_count: parseInt(document.getElementById("guest_count_input").value || "1", 10),
                dietary_preference: document.getElementById("guest_diet").value,
                table_or_group: document.getElementById("guest_group").value.trim(),
                notes: document.getElementById("guest_notes").value.trim()
            };

            try {
                const res = await fetch(`/api/events/${eventId}/guests`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (data.success) {
                    showToast("Guest added to registry!", "success");
                    setTimeout(() => window.location.reload(), 600);
                } else {
                    showToast(data.message || "Failed to add guest.", "danger");
                }
            } catch (err) {
                showToast("Network error.", "danger");
            }
        });
    }

    window.updateGuestRsvp = async function(guestId, status) {
        try {
            const res = await fetch(`/api/events/${eventId}/guests/${guestId}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ rsvp_status: status })
            });
            const data = await res.json();
            if (data.success) {
                showToast(`RSVP updated to ${status}`, "success");
            }
        } catch (err) {
            showToast("Failed to update RSVP.", "danger");
        }
    };

    window.deleteGuest = async function(guestId) {
        if (!confirm("Are you sure you want to remove this guest?")) return;
        try {
            const res = await fetch(`/api/events/${eventId}/guests/${guestId}`, { method: "DELETE" });
            const data = await res.json();
            if (data.success) {
                showToast("Guest removed.", "info");
                setTimeout(() => window.location.reload(), 500);
            }
        } catch (err) {
            showToast("Failed to remove guest.", "danger");
        }
    };

    // =========================================================================
    // CHECKLIST MANAGEMENT
    // =========================================================================
    const checklistForm = document.getElementById("form-add-checklist");
    if (checklistForm) {
        checklistForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const payload = {
                category: document.getElementById("chk_category").value,
                item_name: document.getElementById("chk_name").value.trim(),
                estimated_cost: parseFloat(document.getElementById("chk_cost").value || 0),
                notes: document.getElementById("chk_notes").value.trim()
            };

            try {
                const res = await fetch(`/api/events/${eventId}/checklist`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (data.success) {
                    showToast("Checklist item added!", "success");
                    setTimeout(() => window.location.reload(), 600);
                } else {
                    showToast(data.message || "Failed to add item.", "danger");
                }
            } catch (err) {
                showToast("Network error.", "danger");
            }
        });
    }

    window.toggleChecklistItem = async function(itemId) {
        try {
            const res = await fetch(`/api/events/${eventId}/checklist/${itemId}/toggle`, { method: "POST" });
            const data = await res.json();
            if (data.success) {
                const el = document.getElementById(`checklist-item-${itemId}`);
                if (el) {
                    el.classList.toggle("completed-item", data.is_completed);
                }
                showToast(data.is_completed ? "Item marked completed!" : "Item unmarked.", "success");
            }
        } catch (err) {
            showToast("Failed to toggle checklist item.", "danger");
        }
    };

    window.deleteChecklistItem = async function(itemId) {
        if (!confirm("Remove this checklist item?")) return;
        try {
            const res = await fetch(`/api/events/${eventId}/checklist/${itemId}`, { method: "DELETE" });
            const data = await res.json();
            if (data.success) {
                showToast("Item removed.", "info");
                setTimeout(() => window.location.reload(), 500);
            }
        } catch (err) {
            showToast("Failed to remove item.", "danger");
        }
    };

    // =========================================================================
    // IDEAS MANAGEMENT (Favorites & Custom Idea)
    // =========================================================================
    window.toggleFavoriteIdea = async function(ideaId, btn) {
        try {
            const res = await fetch(`/api/events/${eventId}/ideas/${ideaId}/favorite`, { method: "POST" });
            const data = await res.json();
            if (data.success) {
                btn.classList.toggle("favorited", data.is_favorited);
                btn.innerHTML = data.is_favorited ?
                    `<i data-lucide="bookmark-check" style="color:var(--color-gold-500)"></i> Saved` :
                    `<i data-lucide="bookmark"></i> Save Idea`;
                if (window.lucide) window.lucide.createIcons();
                showToast(data.is_favorited ? "Idea saved to favorites! ⭐" : "Removed from favorites.", "info");
            }
        } catch (err) {
            showToast("Failed to bookmark idea.", "danger");
        }
    };

    const ideaForm = document.getElementById("form-add-idea");
    if (ideaForm) {
        ideaForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const payload = {
                category: document.getElementById("idea_category").value,
                title: document.getElementById("idea_title").value.trim(),
                description: document.getElementById("idea_desc").value.trim()
            };

            try {
                const res = await fetch(`/api/events/${eventId}/ideas`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (data.success) {
                    showToast("Custom idea added!", "success");
                    setTimeout(() => window.location.reload(), 600);
                }
            } catch (err) {
                showToast("Failed to add idea.", "danger");
            }
        });
    }

    // =========================================================================
    // REGENERATE PLAN HANDLER
    // =========================================================================
    const regenBtn = document.getElementById("btn-regenerate-plan");
    if (regenBtn) {
        regenBtn.addEventListener("click", async () => {
            if (!confirm("Regenerating with AI will replace existing expenses, timeline tasks, and ideas with a newly generated plan. Do you wish to continue?")) {
                return;
            }

            regenBtn.disabled = true;
            regenBtn.innerHTML = `<i data-lucide="loader-2" class="spin"></i> Generating...`;
            if (window.lucide) window.lucide.createIcons();

            try {
                const res = await fetch(`/api/events/${eventId}/regenerate`, { method: "POST" });
                const data = await res.json();
                if (data.success) {
                    showToast(data.message || "Plan regenerated with AI!", "success");
                    setTimeout(() => window.location.reload(), 800);
                } else {
                    showToast(data.message || "Regeneration failed.", "danger");
                    regenBtn.disabled = false;
                }
            } catch (err) {
                showToast("Network error.", "danger");
                regenBtn.disabled = false;
            }
        });
    }

    // =========================================================================
    // CHART.JS VISUALIZATION
    // =========================================================================
    let categoryChart = null;
    let comparisonChart = null;

    window.renderBudgetCharts = function() {
        if (!window.Chart) return;

        const catCanvas = document.getElementById("budgetCategoryChart");
        const compCanvas = document.getElementById("budgetComparisonChart");

        // Parse category breakdown data from embedded JSON script tag
        const chartDataScript = document.getElementById("chart-data-expenses");
        if (!chartDataScript) return;

        let expensesData = [];
        try {
            expensesData = JSON.parse(chartDataScript.textContent);
        } catch (e) {
            return;
        }

        // Aggregate by category
        const catMap = {};
        expensesData.forEach(exp => {
            const cat = exp.category || "General";
            if (!catMap[cat]) catMap[cat] = { planned: 0, actual: 0 };
            catMap[cat].planned += parseFloat(exp.planned_amount || 0);
            catMap[cat].actual += parseFloat(exp.actual_amount || 0);
        });

        const labels = Object.keys(catMap);
        const plannedVals = labels.map(l => catMap[l].planned);
        const actualVals = labels.map(l => catMap[l].actual);

        const colors = [
            "#4A1525", "#C5A059", "#721D3B", "#D4AF37", "#5E1931",
            "#9B7830", "#3A5A40", "#E76F51", "#2A724A", "#1D5E8A"
        ];

        // 1. Doughnut Chart (Planned Allocation)
        if (catCanvas) {
            if (categoryChart) categoryChart.destroy();
            categoryChart = new Chart(catCanvas, {
                type: "doughnut",
                data: {
                    labels: labels,
                    datasets: [{
                        data: plannedVals,
                        backgroundColor: colors.slice(0, labels.length),
                        borderWidth: 2,
                        borderColor: "#FFFFFF"
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: "right", labels: { boxWidth: 12, font: { family: "Plus Jakarta Sans", size: 12 } } }
                    },
                    cutout: "65%"
                }
            });
        }

        // 2. Bar Chart (Planned vs Actual)
        if (compCanvas) {
            if (comparisonChart) comparisonChart.destroy();
            comparisonChart = new Chart(compCanvas, {
                type: "bar",
                data: {
                    labels: labels,
                    datasets: [
                        { label: "Planned", data: plannedVals, backgroundColor: "#4A1525", borderRadius: 4 },
                        { label: "Actual", data: actualVals, backgroundColor: "#C5A059", borderRadius: 4 }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { beginAtZero: true, grid: { color: "rgba(0,0,0,0.05)" } },
                        x: { grid: { display: false } }
                    },
                    plugins: {
                        legend: { position: "top", labels: { font: { family: "Plus Jakarta Sans" } } }
                    }
                }
            });
        }
    };

    // Render charts if on budget tab initially
    if (initialTab === "budget") {
        setTimeout(window.renderBudgetCharts, 200);
    }
});
