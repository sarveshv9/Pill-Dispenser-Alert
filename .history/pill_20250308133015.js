document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("pillForm");
    const errorMessage = document.getElementById("error-message");
    const fileInput = document.getElementById("pillPhoto");
    const upcomingAlarmDisplay = document.getElementById("upcoming-alarm");
    const stopAlarmButton = document.getElementById("stopAlarm");
    const alarmBox = document.getElementById("alarm-box");
    const pillImage = document.getElementById("pill-image");

    let imageUrl = "";

    // Ensure upcoming alarm element exists before updating it
    function safeUpdateUpcomingAlarm(message, color = "gray") {
        if (upcomingAlarmDisplay) {
            upcomingAlarmDisplay.textContent = message;
            upcomingAlarmDisplay.style.color = color;
        }
    }

    // Handle image upload and store URL
    fileInput.addEventListener("change", function () {
        const file = fileInput.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function (e) {
                imageUrl = e.target.result; // Store the image data URL
                localStorage.setItem("pillImage", imageUrl);
            };
            reader.readAsDataURL(file);
        }
    });

    form.addEventListener("submit", function (event) {
        event.preventDefault(); // Prevent form submission for now

        let name = document.getElementById("name").value.trim();
        let pillName = document.getElementById("pillName").value.trim();
        let startDate = document.getElementById("startDate").value;
        let endDate = document.getElementById("endDate").value;
        let alarmTime = document.getElementById("alarmTime").value;

        // Check if required fields are filled
        if (!name || !pillName || !startDate || !endDate || !alarmTime) {
            errorMessage.textContent = "Please fill out all required fields.";
            errorMessage.style.color = "red";
            return;
        }

        // Store alarm time and pill name in local storage
        localStorage.setItem("pillAlarmTime", alarmTime);
        localStorage.setItem("pillName", pillName);
        
        errorMessage.textContent = "Pill alarm set successfully!";
        errorMessage.style.color = "green";

        updateUpcomingAlarm();
        startAlarmCheck();
    });


    function startAlarmCheck() {
        setInterval(function () {
            let currentTime = new Date();
            let alarmTime = localStorage.getItem("pillAlarmTime");

            if (alarmTime) {
                let [alarmHours, alarmMinutes] = alarmTime.split(":");
                let alarmDate = new Date();
                alarmDate.setHours(alarmHours, alarmMinutes, 0, 0);

                if (
                    currentTime.getHours() === alarmDate.getHours() &&
                    currentTime.getMinutes() === alarmDate.getMinutes()
                ) {
                    triggerAlarm();
                    localStorage.removeItem("pillAlarmTime"); // Remove alarm after triggering
                    localStorage.removeItem("pillName");
                    updateUpcomingAlarm();
                }
            }
        }, 1000); // Check every second
    }

    function triggerAlarm() {
        let savedImageUrl = localStorage.getItem("pillImage");
        if (savedImageUrl) {
            pillImage.src = savedImageUrl;
            pillImage.style.display = "block";
        } else {
            pillImage.style.display = "none";
        }

        alarmBox.style.display = "block";
    }

    stopAlarmButton.addEventListener("click", function () {
        alarmBox.style.display = "none";
    });

    updateUpcomingAlarm(); // Show alarm info when the page loads
    startAlarmCheck(); // Start checking for alarms
});
