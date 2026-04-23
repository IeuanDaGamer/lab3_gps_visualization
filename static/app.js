async function loadData() {
    try {
        const response = await fetch("/api/data");
        const data = await response.json();

        const satellites = data.satellites || [];
        const analytic = data.analyticPosition;
        const numeric = data.numericPosition;
        const config = data.config || {};
        const zoneSize = Number(config.emulationZoneSize || 200);

        document.getElementById("status").textContent = "Статус: " + data.status;
        document.getElementById("satelliteCount").textContent =
            "Кількість валідних супутників: " + satellites.length;

        document.getElementById("lastMessage").textContent = JSON.stringify(data.lastMessage, null, 2);

        const traces = [];

        if (satellites.length > 0) {
            traces.push({
                x: satellites.map(s => s.x),
                y: satellites.map(s => s.y),
                mode: "markers+text",
                type: "scatter",
                name: "Супутники",
                text: satellites.map((s, i) => `S${i + 1}`),
                textposition: "top center",
                marker: {
                    size: 12,
                    color: "blue"
                },
                hovertext: satellites.map(s =>
                    `ID: ${s.id}<br>X: ${s.x.toFixed(2)}<br>Y: ${s.y.toFixed(2)}<br>Distance: ${s.distance.toFixed(2)}`
                ),
                hoverinfo: "text"
            });
        }

        if (analytic) {
            traces.push({
                x: [analytic.x],
                y: [analytic.y],
                mode: "markers+text",
                text: ["A"],
                textposition: "top right",
                type: "scatter",
                name: "Об'єкт (аналітичний)",
                marker: {
                    size: 28,
                    color: "red",
                    symbol: "circle",
                    line: {
                        width: 1,
                        color: "black"
                    }
                },
                hovertext: [`Аналітичний метод<br>X: ${analytic.x.toFixed(2)}<br>Y: ${analytic.y.toFixed(2)}`],
                hoverinfo: "text"
            });

            document.getElementById("analyticCoords").textContent =
                `X = ${analytic.x.toFixed(3)} км, Y = ${analytic.y.toFixed(3)} км`;
        } else {
            document.getElementById("analyticCoords").textContent = "Недостатньо даних для розрахунку";
        }

        if (numeric) {
            traces.push({
                x: [numeric.x],
                y: [numeric.y],
                mode: "markers+text",
                text: ["N"],
                textposition: "bottom right",
                type: "scatter",
                name: "Об'єкт (чисельний)",
                marker: {
                    size: 12,
                    color: "green",
                    symbol: "diamond",
                    line: {
                        width: 1,
                        color: "black"
                    }
                },
                hovertext: [`Чисельний метод<br>X: ${numeric.x.toFixed(2)}<br>Y: ${numeric.y.toFixed(2)}`],
                hoverinfo: "text"
            });

            document.getElementById("numericCoords").textContent =
                `X = ${numeric.x.toFixed(3)} км, Y = ${numeric.y.toFixed(3)} км`;
        } else {
            document.getElementById("numericCoords").textContent = "Недостатньо даних для розрахунку";
        }

        const layout = {
            title: "Положення супутників та об'єкта",
            xaxis: {
                title: "X (км)",
                range: [0, zoneSize]
            },
            yaxis: {
                title: "Y (км)",
                range: [0, zoneSize]
            },
            paper_bgcolor: "#ffffff",
            plot_bgcolor: "#ffffff",
            legend: {
                orientation: "h"
            }
        };

        Plotly.react("chart", traces, layout, { responsive: true });
    } catch (error) {
        document.getElementById("status").textContent = "Помилка завантаження даних";
    }
}

document.getElementById("configForm").addEventListener("submit", async function (e) {
    e.preventDefault();

    const payload = {
        emulationZoneSize: Number(document.getElementById("emulationZoneSize").value),
        messageFrequency: Number(document.getElementById("messageFrequency").value),
        satelliteSpeed: Number(document.getElementById("satelliteSpeed").value),
        objectSpeed: Number(document.getElementById("objectSpeed").value)
    };

    try {
        const response = await fetch("/api/config", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        const result = await response.json();
        document.getElementById("configResult").textContent = JSON.stringify(result, null, 2);
    } catch (error) {
        document.getElementById("configResult").textContent = "Помилка: " + error;
    }
});

loadData();
setInterval(loadData, 1000);