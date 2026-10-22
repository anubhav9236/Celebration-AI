/**
 * CelebrationAI - In-Dashboard Conversational Event Assistant
 */

document.addEventListener("DOMContentLoaded", () => {
    const eventIdMeta = document.getElementById("event-meta-id");
    if (!eventIdMeta) return;
    const eventId = eventIdMeta.value;

    const chatToggleBtn = document.getElementById("chat-toggle-btn");
    const chatCloseBtn = document.getElementById("chat-close-btn");
    const chatPanel = document.getElementById("chat-panel");
    const chatForm = document.getElementById("chat-form");
    const chatInput = document.getElementById("chat-input");
    const chatMessages = document.getElementById("chat-messages");

    if (chatToggleBtn && chatPanel) {
        chatToggleBtn.addEventListener("click", () => {
            chatPanel.classList.toggle("open");
            if (chatPanel.classList.contains("open")) {
                chatInput.focus();
                scrollChatToBottom();
            }
        });
    }

    if (chatCloseBtn && chatPanel) {
        chatCloseBtn.addEventListener("click", () => {
            chatPanel.classList.remove("open");
        });
    }

    function scrollChatToBottom() {
        if (chatMessages) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }

    // Quick prompt chip click handler
    document.querySelectorAll(".quick-prompt-chip").forEach(chip => {
        chip.addEventListener("click", () => {
            const promptText = chip.getAttribute("data-prompt");
            if (chatInput && promptText) {
                chatInput.value = promptText;
                chatForm.dispatchEvent(new Event("submit"));
            }
        });
    });

    // Handle Sending Message
    if (chatForm) {
        chatForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const message = chatInput.value.trim();
            if (!message) return;

            // Append User Bubble
            appendMessage("user", message);
            chatInput.value = "";
            chatInput.disabled = true;

            // Append Typing Indicator
            const typingBubble = document.createElement("div");
            typingBubble.className = "chat-bubble assistant";
            typingBubble.id = "typing-indicator";
            typingBubble.innerHTML = `<span style="display:inline-flex; align-items:center; gap:4px; color:var(--color-text-light);">
                <i data-lucide="sparkles" style="width:14px; height:14px;"></i> Thinking...
            </span>`;
            chatMessages.appendChild(typingBubble);
            if (window.lucide) window.lucide.createIcons();
            scrollChatToBottom();

            try {
                const res = await fetch(`/api/events/${eventId}/chat`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ message: message })
                });

                typingBubble.remove();
                chatInput.disabled = false;
                chatInput.focus();

                const data = await res.json();
                if (data.success) {
                    appendMessage("assistant", data.reply, data.action_proposal);
                } else {
                    appendMessage("assistant", data.message || "I apologize, I encountered an error answering that. Please try again.");
                }
            } catch (err) {
                typingBubble.remove();
                chatInput.disabled = false;
                appendMessage("assistant", "Unable to connect to the assistant. Please check your connection.");
            }
        });
    }

    function appendMessage(sender, content, proposal = null) {
        const bubble = document.createElement("div");
        bubble.className = `chat-bubble ${sender}`;

        // Basic markdown formatting: bold, bullets, newlines
        let formatted = content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n\s*-\s*(.*?)/g, '<br>&bull; $1')
            .replace(/\n\n/g, '<br><br>')
            .replace(/\n/g, '<br>');

        bubble.innerHTML = formatted;

        // Render Action Proposal Box if present
        if (proposal) {
            const proposalBox = document.createElement("div");
            proposalBox.className = "action-proposal-box";
            
            const isExpense = proposal.type === "add_expense";
            proposalBox.innerHTML = `
                <div style="font-weight:600; font-size:0.8rem; color:var(--color-plum-800); margin-bottom:4px;">
                    <i data-lucide="${isExpense ? 'receipt' : 'calendar-plus'}" style="width:13px; height:13px;"></i>
                    Proposed Action: ${isExpense ? 'Add Expense' : 'Add Timeline Task'}
                </div>
                <div style="font-size:0.825rem; margin-bottom:8px;">
                    <strong>${proposal.title || ''}</strong>
                    ${proposal.planned_amount ? ` &bull; Amount: ₹${Number(proposal.planned_amount).toLocaleString()}` : ''}
                    ${proposal.due_date ? ` &bull; Due: ${proposal.due_date}` : ''}
                </div>
                <button class="btn btn-sm btn-primary apply-proposal-btn" style="width:100%; font-size:0.8rem;">
                    Apply to Event Plan
                </button>
            `;

            const applyBtn = proposalBox.querySelector(".apply-proposal-btn");
            applyBtn.addEventListener("click", async () => {
                applyBtn.disabled = true;
                applyBtn.textContent = "Applying...";

                try {
                    const res = await fetch(`/api/events/${eventId}/chat/apply-action`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(proposal)
                    });
                    const resData = await res.json();
                    if (resData.success) {
                        applyBtn.className = "btn btn-sm btn-outline";
                        applyBtn.innerHTML = `✓ Applied to Plan`;
                        showToast(resData.message, "success");
                    } else {
                        applyBtn.disabled = false;
                        applyBtn.textContent = "Failed. Try Again";
                    }
                } catch (e) {
                    applyBtn.disabled = false;
                    applyBtn.textContent = "Error";
                }
            });

            bubble.appendChild(proposalBox);
        }

        chatMessages.appendChild(bubble);
        if (window.lucide) window.lucide.createIcons();
        scrollChatToBottom();
    }
});
