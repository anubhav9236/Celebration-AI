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
        mobileBtn.addEventListener("click", () => {
            if (navLinks.style.display === "flex") {
                navLinks.style.display = "none";
            } else {
                navLinks.style.display = "flex";
                navLinks.style.flexDirection = "column";
                navLinks.style.position = "absolute";
                navLinks.style.top = "68px";
                navLinks.style.left = "0";
                navLinks.style.right = "0";
                navLinks.style.background = "#FFFFFF";
                navLinks.style.padding = "1.5rem";
                navLinks.style.borderBottom = "1px solid var(--color-border)";
                navLinks.style.boxShadow = "var(--shadow-md)";
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
