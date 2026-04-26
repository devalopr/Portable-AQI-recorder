const BLE = {
  service: "7b46a200-fd8a-4a28-8f4b-4b3e7c4f0001",
  live: "7b46a201-fd8a-4a28-8f4b-4b3e7c4f0001",
  status: "7b46a202-fd8a-4a28-8f4b-4b3e7c4f0001",
};

const fields = [
  { key: "aqi", label: "AQI", unit: "", color: "#166f6b" },
  { key: "pm1p0", label: "PM1.0", unit: "ug/m3", color: "#3178c6" },
  { key: "pm2p5", label: "PM2.5", unit: "ug/m3", color: "#c85b32" },
  { key: "pm4p0", label: "PM4.0", unit: "ug/m3", color: "#7d4fc7" },
  { key: "pm10p0", label: "PM10", unit: "ug/m3", color: "#b58600" },
  { key: "humidity", label: "Humidity", unit: "%", color: "#178f76" },
  { key: "temperature", label: "Temperature", unit: "C", color: "#d04747" },
  { key: "vocIndex", label: "VOC", unit: "index", color: "#5f7fca" },
  { key: "noxIndex", label: "NOx", unit: "index", color: "#8b6f47" },
];

const state = {
  device: null,
  server: null,
  liveCharacteristic: null,
  connected: false,
  recording: false,
  samples: [],
  selectedFields: new Set(["aqi", "pm2p5", "pm10p0"]),
  latest: null,
};

const els = {
  connectButton: document.querySelector("#connectButton"),
  themeToggle: document.querySelector("#themeToggle"),
  connectionStatus: document.querySelector("#connectionStatus"),
  sensorName: document.querySelector("#sensorName"),
  sampleCount: document.querySelector("#sampleCount"),
  lastUpdate: document.querySelector("#lastUpdate"),
  aqiBand: document.querySelector("#aqiBand"),
  aqiValue: document.querySelector("#aqiValue"),
  aqiCategory: document.querySelector("#aqiCategory"),
  metricGrid: document.querySelector("#metricGrid"),
  chartControls: document.querySelector("#chartControls"),
  chart: document.querySelector("#historyChart"),
  sampleTable: document.querySelector("#sampleTable"),
  recordButton: document.querySelector("#recordButton"),
  clearButton: document.querySelector("#clearButton"),
  exportButton: document.querySelector("#exportButton"),
};

const ctx = els.chart.getContext("2d");
const formatter = new Intl.DateTimeFormat(undefined, {
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
});

init();

function init() {
  loadTheme();
  renderMetricCards();
  renderChartControls();
  bindEvents();
  drawChart();

  if (!("bluetooth" in navigator)) {
    setStatus("Web Bluetooth unavailable");
    els.connectButton.disabled = true;
  }
}

function bindEvents() {
  els.connectButton.addEventListener("click", connect);
  els.themeToggle.addEventListener("click", toggleTheme);
  els.recordButton.addEventListener("click", toggleRecording);
  els.clearButton.addEventListener("click", clearSamples);
  els.exportButton.addEventListener("click", exportCsv);
  window.addEventListener("resize", drawChart);
}

async function connect() {
  if (state.connected && state.device?.gatt?.connected) {
    state.device.gatt.disconnect();
    return;
  }

  try {
    setStatus("Choosing device");
    const device = await navigator.bluetooth.requestDevice({
      filters: [{ namePrefix: "AQI" }],
      optionalServices: [BLE.service],
    });

    state.device = device;
    device.addEventListener("gattserverdisconnected", onDisconnected);

    setStatus("Connecting");
    state.server = await device.gatt.connect();
    let service;
    try {
      service = await state.server.getPrimaryService(BLE.service);
    } catch {
      setStatus("AQI service not found");
      throw new Error("The selected BLE device does not expose the AQI web service. Flash the latest firmware, then power-cycle the recorder and reconnect.");
    }
    state.liveCharacteristic = await service.getCharacteristic(BLE.live);

    try {
      const statusChar = await service.getCharacteristic(BLE.status);
      const value = await statusChar.readValue();
      const text = new TextDecoder().decode(value);
      const status = JSON.parse(text);
      els.sensorName.textContent = status.sensor || "Detected";
    } catch {
      els.sensorName.textContent = "Detected";
    }

    await state.liveCharacteristic.startNotifications();
    state.liveCharacteristic.addEventListener("characteristicvaluechanged", onSample);
    state.connected = true;
    els.connectButton.textContent = "Disconnect";
    setStatus("Connected");
  } catch (error) {
    console.error(error);
    if (error.name === "NotFoundError") {
      setStatus("No device selected");
    } else if (error.name === "SecurityError") {
      setStatus("Click Connect directly");
    } else if (error.message.includes("AQI web service")) {
      setStatus("Flash latest firmware");
    } else {
      setStatus("Connection failed");
    }
  }
}

function onDisconnected() {
  state.connected = false;
  state.liveCharacteristic = null;
  els.connectButton.textContent = "Connect";
  setStatus("Disconnected");
}

function onSample(event) {
  const sample = parseSample(event.target.value);
  state.latest = sample;

  if (!els.sensorName.textContent || els.sensorName.textContent === "Waiting") {
    els.sensorName.textContent = sample.sensor;
  }

  if (state.recording) {
    state.samples.push(sample);
    if (state.samples.length > 7200) {
      state.samples.shift();
    }
  }

  renderLatest(sample);
  renderTable();
  drawChart();
}

function parseSample(data) {
  let offset = 0;
  const readU16 = () => {
    const value = data.getUint16(offset, true);
    offset += 2;
    return value;
  };
  const readI16 = () => {
    const value = data.getInt16(offset, true);
    offset += 2;
    return value;
  };
  
  const timestamp = data.getUint32(offset, true);
  offset += 4;

  const sample = {
    receivedAt: Date.now(),
    deviceMillis: timestamp,
    pm1p0: readU16() / 10,
    pm2p5: readU16() / 10,
    pm4p0: readU16() / 10,
    pm10p0: readU16() / 10,
    humidity: readU16() / 100,
    temperature: readI16() / 100,
    vocIndex: readU16(),
    noxIndex: readU16(),
    aqi: readU16(),
    sensor: sensorName(data.getUint8(offset)),
  };
  
  return sample;
}

function sensorName(code) {
  if (code === 50) return "SEN50";
  if (code === 54) return "SEN54";
  if (code === 55) return "SEN55";
  return "Unknown";
}

function renderMetricCards() {
  els.metricGrid.innerHTML = fields.map((field) => `
    <article class="metric-card" data-field="${field.key}">
      <span class="label">${field.label}</span>
      <strong>--</strong>
      <span>${field.unit}</span>
    </article>
  `).join("");
}

function renderLatest(sample) {
  els.sampleCount.textContent = state.samples.length.toLocaleString();
  els.lastUpdate.textContent = formatter.format(sample.receivedAt);
  els.sensorName.textContent = sample.sensor;
  els.aqiValue.textContent = Math.round(sample.aqi);
  els.aqiCategory.textContent = aqiCategory(sample.aqi);
  els.aqiBand.style.borderLeftColor = aqiColor(sample.aqi);

  fields.forEach((field) => {
    const card = els.metricGrid.querySelector(`[data-field="${field.key}"]`);
    const value = card.querySelector("strong");
    value.textContent = formatValue(sample[field.key], field.key);
  });
}

function renderChartControls() {
  els.chartControls.innerHTML = fields.map((field) => `
    <label>
      <input type="checkbox" value="${field.key}" ${state.selectedFields.has(field.key) ? "checked" : ""}>
      ${field.label}
    </label>
  `).join("");

  els.chartControls.addEventListener("change", (event) => {
    if (event.target.checked) {
      state.selectedFields.add(event.target.value);
    } else {
      state.selectedFields.delete(event.target.value);
    }
    drawChart();
  });
}

function renderTable() {
  const rows = state.samples.slice(-40).reverse();
  els.sampleTable.innerHTML = rows.map((sample) => `
    <tr>
      <td>${formatter.format(sample.receivedAt)}</td>
      <td>${Math.round(sample.aqi)}</td>
      <td>${sample.pm1p0.toFixed(1)}</td>
      <td>${sample.pm2p5.toFixed(1)}</td>
      <td>${sample.pm4p0.toFixed(1)}</td>
      <td>${sample.pm10p0.toFixed(1)}</td>
      <td>${sample.humidity.toFixed(1)}</td>
      <td>${sample.temperature.toFixed(1)}</td>
      <td>${sample.vocIndex}</td>
      <td>${sample.noxIndex}</td>
    </tr>
  `).join("");
}

function drawChart() {
  const rect = els.chart.getBoundingClientRect();
  const scale = window.devicePixelRatio || 1;
  els.chart.width = Math.max(320, Math.floor(rect.width * scale));
  els.chart.height = Math.max(240, Math.floor(rect.height * scale));
  ctx.setTransform(scale, 0, 0, scale, 0, 0);

  const width = rect.width;
  const height = rect.height;
  const padding = { top: 18, right: 18, bottom: 38, left: 54 };
  const plotW = width - padding.left - padding.right;
  const plotH = height - padding.top - padding.bottom;
  const styles = getComputedStyle(document.documentElement);
  const text = styles.getPropertyValue("--text").trim();
  const muted = styles.getPropertyValue("--muted").trim();
  const line = styles.getPropertyValue("--line").trim();

  ctx.clearRect(0, 0, width, height);
  ctx.font = "12px system-ui, sans-serif";
  ctx.lineWidth = 1;
  ctx.strokeStyle = line;
  ctx.fillStyle = muted;

  for (let i = 0; i <= 4; i += 1) {
    const y = padding.top + (plotH / 4) * i;
    ctx.beginPath();
    ctx.moveTo(padding.left, y);
    ctx.lineTo(width - padding.right, y);
    ctx.stroke();
  }

  const samples = state.samples.length ? state.samples : state.latest ? [state.latest] : [];
  const selected = fields.filter((field) => state.selectedFields.has(field.key));

  if (samples.length < 2 || selected.length === 0) {
    ctx.fillStyle = muted;
    ctx.textAlign = "center";
    ctx.fillText("Start recording to build a chart.", width / 2, height / 2);
    return;
  }

  let min = Infinity;
  let max = -Infinity;
  selected.forEach((field) => {
    samples.forEach((sample) => {
      const value = sample[field.key];
      if (Number.isFinite(value)) {
        min = Math.min(min, value);
        max = Math.max(max, value);
      }
    });
  });
  if (min === max) {
    min -= 1;
    max += 1;
  }
  const pad = (max - min) * 0.1;
  min -= pad;
  max += pad;

  ctx.fillStyle = muted;
  ctx.textAlign = "right";
  for (let i = 0; i <= 4; i += 1) {
    const value = max - ((max - min) / 4) * i;
    const y = padding.top + (plotH / 4) * i + 4;
    ctx.fillText(formatAxis(value), padding.left - 8, y);
  }

  selected.forEach((field) => {
    ctx.strokeStyle = field.color;
    ctx.lineWidth = 2;
    ctx.beginPath();
    samples.forEach((sample, index) => {
      const x = padding.left + (plotW * index) / (samples.length - 1);
      const y = padding.top + plotH - ((sample[field.key] - min) / (max - min)) * plotH;
      if (index === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
  });

  const first = samples[0].receivedAt;
  const last = samples[samples.length - 1].receivedAt;
  ctx.fillStyle = muted;
  ctx.textAlign = "left";
  ctx.fillText(formatter.format(first), padding.left, height - 14);
  ctx.textAlign = "right";
  ctx.fillText(formatter.format(last), width - padding.right, height - 14);

  ctx.textAlign = "left";
  let legendX = padding.left;
  selected.forEach((field) => {
    ctx.fillStyle = field.color;
    ctx.fillRect(legendX, 10, 10, 10);
    ctx.fillStyle = text;
    ctx.fillText(field.label, legendX + 16, 19);
    legendX += ctx.measureText(field.label).width + 42;
  });
}

function toggleRecording() {
  state.recording = !state.recording;
  els.recordButton.textContent = state.recording ? "Stop Recording" : "Start Recording";
  if (state.recording && state.latest) {
    state.samples.push(state.latest);
  }
  setStatus(state.connected ? "Connected" : "Recording locally");
  renderTable();
  drawChart();
}

function clearSamples() {
  state.samples = [];
  els.sampleCount.textContent = "0";
  renderTable();
  drawChart();
}

function exportCsv() {
  if (!state.samples.length) return;
  const header = ["time_iso", "device_millis", ...fields.map((field) => field.key), "sensor"];
  const rows = state.samples.map((sample) => [
    new Date(sample.receivedAt).toISOString(),
    sample.deviceMillis,
    ...fields.map((field) => sample[field.key]),
    sample.sensor,
  ]);
  const csv = [header, ...rows]
    .map((row) => row.map(csvCell).join(","))
    .join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `aqi-recording-${new Date().toISOString().replace(/[:.]/g, "-")}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}

function csvCell(value) {
  const text = String(value ?? "");
  return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

function toggleTheme() {
  const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = next;
  localStorage.setItem("aqi-theme", next);
  drawChart();
}

function loadTheme() {
  const saved = localStorage.getItem("aqi-theme");
  const prefersDark = window.matchMedia?.("(prefers-color-scheme: dark)").matches;
  document.documentElement.dataset.theme = saved || (prefersDark ? "dark" : "light");
}

function setStatus(value) {
  els.connectionStatus.textContent = value;
}

function formatValue(value, key) {
  if (!Number.isFinite(value)) return "--";
  if (key === "aqi" || key === "vocIndex" || key === "noxIndex") return Math.round(value);
  return value.toFixed(1);
}

function formatAxis(value) {
  if (Math.abs(value) >= 100) return value.toFixed(0);
  if (Math.abs(value) >= 10) return value.toFixed(1);
  return value.toFixed(2);
}

function aqiCategory(aqi) {
  if (aqi <= 50) return "Good";
  if (aqi <= 100) return "Moderate";
  if (aqi <= 150) return "Unhealthy for sensitive groups";
  if (aqi <= 200) return "Unhealthy";
  if (aqi <= 300) return "Very unhealthy";
  return "Hazardous";
}

function aqiColor(aqi) {
  const styles = getComputedStyle(document.documentElement);
  if (aqi <= 50) return styles.getPropertyValue("--good");
  if (aqi <= 100) return styles.getPropertyValue("--moderate");
  if (aqi <= 150) return styles.getPropertyValue("--sensitive");
  if (aqi <= 200) return styles.getPropertyValue("--unhealthy");
  if (aqi <= 300) return styles.getPropertyValue("--very-unhealthy");
  return styles.getPropertyValue("--hazardous");
}
