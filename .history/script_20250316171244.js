document.addEventListener("DOMContentLoaded", function() {
    function fetchAlarms() {
        fetch("/get_upcoming_alarms")
            .then(response => response.json())
            .then(alarms => {
                const container = document.getElementById("upcoming-list");
                container.innerHTML = "";

                if (alarms.length === 0) {
                    container.innerHTML = "<p>No upcoming alarms.</p>";
                } else {
                    let alarmList = "<ul>";
                    alarms.forEach(alarm => {
                        alarmList += `<li>
                            <strong>🕒 ${alarm.time}</strong> - ${alarm.medicine}
                            ${alarm.image ? `<br><img src="${alarm.image}" alt="Medicine" width="100">` : ""}
                        </li>`;
                    });
                    alarmList += "</ul>";
                    container.innerHTML = alarmList;
                }
            })
            .catch(error => console.error("Error fetching alarms:", error));
    }

    fetchAlarms(); // Fetch alarms when the page loads
    setInterval(fetchAlarms, 5000); // Refresh every 5 seconds
});
