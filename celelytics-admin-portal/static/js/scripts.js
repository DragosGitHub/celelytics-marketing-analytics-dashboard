// ✅ Ensure all event listeners are registered after DOM loads
document.addEventListener("DOMContentLoaded", function () {
    console.log("✅ JS loaded");

    // ✅ Handle view full message popup with all info
    document.querySelectorAll(".view-btn").forEach(button => {
        button.addEventListener("click", function () {
            const name = this.getAttribute("data-name");
            const email = this.getAttribute("data-email");
            const date = this.getAttribute("data-date");
            const time = this.getAttribute("data-time");
            const message = this.getAttribute("data-message");

            document.getElementById("popup-name").textContent = name;
            document.getElementById("popup-email").textContent = email;
            document.getElementById("popup-date").textContent = date;
            document.getElementById("popup-time").textContent = time;
            document.getElementById("popup-message").textContent = message;

            document.getElementById("popup").classList.remove("hidden");
        });
    });

    // ✅ Handle popup close
    const closeBtn = document.querySelector(".close-btn");
    if (closeBtn) {
        closeBtn.addEventListener("click", function () {
            document.getElementById("popup").classList.add("hidden");
        });
    }
});

// ✅ Select all checkboxes
window.selectAll = function () {
    document.querySelectorAll(".select-box").forEach(box => box.checked = true);
};

// ✅ Delete selected messages using PartitionKey + RowKey
window.deleteSelected = async function () {
    const selected = Array.from(document.querySelectorAll(".select-box:checked"));

    if (selected.length === 0) {
        alert("No messages selected.");
        return;
    }

    if (!confirm(`Are you sure you want to delete ${selected.length} message(s)?`)) return;

    const messagesToDelete = selected.map(box => ({
        partition_key: box.dataset.partitionKey,
        row_key: box.dataset.rowKey
    }));

    try {
        const response = await fetch("/delete", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ messages: messagesToDelete })
        });

        const result = await response.json();
        if (result.status === "success") {
            alert("✅ Messages deleted successfully.");
            location.reload();
        } else {
            alert("❌ Failed to delete messages. Please try again.");
        }
    } catch (error) {
        console.error("❌ Error:", error);
        alert("An error occurred while deleting messages.");
    }
};

// ✅ Refresh the page
window.refreshMessages = function () {
    location.reload();
};
