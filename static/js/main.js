/**
 * CelebrationAI - Global UI Interactions & Helpers
 */

document.addEventListener("DOMContentLoaded", () => {
    // Initialize Lucide icons if available
    if (window.lucide) {
        window.lucide.createIcons();
    }

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll(".alert");
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = "0";
            alert.style.transform = "translateX(20px)";
            alert.style.transition = "all 0.4s ease";
            setTimeout(() => alert.remove(), 400);
        }, 5000);
    });

    // Mobile Navigation Toggle
    const mobileBtn = document.querySelector(".mobile-menu-btn");
    const navLinks = document.querySelector(".nav-links");
    if (mobileBtn && navLinks) {
        mobileBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            navLinks.classList.toggle("mobile-open");
        });

        // Close menu on click outside
        document.addEventListener("click", (e) => {
            if (!navLinks.contains(e.target) && !mobileBtn.contains(e.target)) {
                navLinks.classList.remove("mobile-open");
            }
        });
    }
});

// Toast notification helper
function showToast(message, type = "info") {
    let container = document.querySelector(".alert-container");
    if (!container) {
        container = document.createElement("div");
        container.className = "alert-container";
        document.body.appendChild(container);
    }

    const alert = document.createElement("div");
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `
        <div style="display:flex; align-items:center; gap:0.5rem;">
            <span>${message}</span>
        </div>
        <button class="alert-close" onclick="this.parentElement.remove()">&times;</button>
    `;
    container.appendChild(alert);

    if (window.lucide) {
        window.lucide.createIcons();
    }

    setTimeout(() => {
        alert.style.opacity = "0";
        alert.style.transform = "translateX(20px)";
        alert.style.transition = "all 0.4s ease";
        setTimeout(() => alert.remove(), 400);
    }, 4500);
}
