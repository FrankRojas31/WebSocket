document.addEventListener("DOMContentLoaded", () => {
  var defaultBgColor = "rgb(153, 102, 255)";
  var defaultBorderColor = "rgb(153, 102, 255)";
  const websocket = new WebSocket("ws://localhost:8765");

  websocket.onopen = () => {
    console.log("Conectado al servidor WebSocket");
    websocket.send(JSON.stringify({ type: "command", value: "getAll" }));
    setInterval(() => {
      websocket.send(JSON.stringify({ type: "command", value: "getAll" }));
    }, 500);
  };

  websocket.onmessage = event => {
    const message = JSON.parse(event.data);
    console.log("Mensaje recibido:", message);

    if (message.type === "state") {
      const toggleBtn = document.getElementById("toggleBtn");
      const led = document.getElementById("led");
      const titulo = document.getElementById("titulo")

      if (message.value === "1") {
        toggleBtn.checked = true;
        led.src = "./img/ROJO-OFF.svg";
        titulo.classList.remove("texto-blanco");
        titulo.classList.add("mb-4", "texto-negro");
      } else if (message.value === "0") {
        toggleBtn.checked = false;
        led.src = "./img/ROJO-ON.svg";
        titulo.classList.remove("texto-negro");
        titulo.classList.add("mb-4", "texto-blanco");
      }
    } else if (message.type === "data") {
      updateBarChart(message.value);
    }
  };

  document.getElementById("toggleBtn").addEventListener("change", function () {
    const command = this.checked ? "1" : "0";
    websocket.send(JSON.stringify({ type: "command", value: command }));
    console.log("Enviado:", command);
  });

  const initBarChart = () => {
    const ctx = document.getElementById("barChartCanvas").getContext("2d");
    const barChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels: [],
        datasets: [{
          label: "Datos Sensor",
          data: [],
          backgroundColor: defaultBgColor,
          borderColor: defaultBorderColor,
        }]
      },
      options: {},
    });

    return barChart;
  };

  let barChart = initBarChart();

  function updateBarChart(data) {
    try {
      const parsedData = JSON.parse(data);

      barChart.data.labels = [];
      barChart.data.datasets[0].data = [];

      parsedData.forEach(item => {
        barChart.data.labels.push(item.fecha);
        barChart.data.datasets[0].data.push(item.estado === 'Encendido' ? 1 : 0);
      });

      barChart.update();
    } catch (error) {
      console.error("Error al analizar los datos JSON:", error);
    }
  }
});
