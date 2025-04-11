document.addEventListener("DOMContentLoaded", function() {
    // Theme toggle functionality
    const themeToggle = document.getElementById("theme-toggle");
    const body = document.body;

    // Check for saved theme preference or respect OS preference
    const prefersDarkMode = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;

    // Use saved theme or fallback to OS preference
    const savedTheme = localStorage.getItem("theme") || (prefersDarkMode ? "dark" : "light");

    if (savedTheme === "dark") {
        body.classList.add("dark-mode");
    }

    themeToggle.addEventListener("click", function() {
        // Toggle dark mode class
        body.classList.toggle("dark-mode");

        // Save preference to localStorage
        const isDark = body.classList.contains("dark-mode");
        localStorage.setItem("theme", isDark ? "dark" : "light");

        // Prevent default to avoid focusing on button (blue outline)
        event.preventDefault();
    });

    // Sidebar toggle functionality
    const sidebarToggle = document.getElementById("sidebar-toggle");
    const sidebarClose = document.getElementById("sidebar-close");
    const sidebar = document.getElementById("sidebar");

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener("click", function(event) {
            sidebar.classList.toggle("sidebar-open");
            event.preventDefault();
        });
    }

    if (sidebarClose && sidebar) {
        sidebarClose.addEventListener("click", function(event) {
            sidebar.classList.remove("sidebar-open");
            event.preventDefault();
        });
    }

    // Close sidebar when clicking outside on mobile
    document.addEventListener("click", function(event) {
        const isMobile = window.innerWidth < 768;
        const isClickInsideSidebar = sidebar && sidebar.contains(event.target);
        const isClickOnSidebarToggle = sidebarToggle && sidebarToggle.contains(event.target);

        if (isMobile && sidebar && sidebar.classList.contains("sidebar-open") && !isClickInsideSidebar && !isClickOnSidebarToggle) {
            sidebar.classList.remove("sidebar-open");
        }
    });

    // Handle modal close for confirmation dialogs
    const modals = document.querySelectorAll(".modal");

    modals.forEach(modal => {
        // Close modal when clicking outside the content
        modal.addEventListener("click", function(event) {
            if (event.target === modal) {
                modal.style.display = "none";
            }
        });

        // Handle "ESC" key press to close modals
        document.addEventListener("keydown", function(event) {
            if (event.key === "Escape" && modal.style.display === "flex") {
                modal.style.display = "none";
            }
        });
    });

    // Auto-hide flash messages after 5 seconds
    const alerts = document.querySelectorAll(".alert");

    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = "0";
            setTimeout(() => {
                alert.style.display = "none";
            }, 300);
        }, 5000);
    });

    // Handle page transitions smoothly
    document.querySelectorAll("a:not([target='_blank'])").forEach(link => {
        link.addEventListener("click", function() {
            document.body.classList.add("page-transition");
        });
    });
});
