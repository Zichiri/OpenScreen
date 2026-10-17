const screen = document.getElementById("screen");
const placeholder = document.getElementById("placeholder");
const status = document.getElementById("status");
const viewer = document.getElementById("viewer");
const fullscreen = document.getElementById("fullscreen");
let retryTimer = null;
let attempts = 0;

function setStatus(message, kind = "") {
  status.textContent = message;
  status.className = `status ${kind}`;
}

function connect() {
  clearTimeout(retryTimer);
  setStatus("正在连接…");
  screen.src = `/stream?attempt=${++attempts}`;
}

screen.addEventListener("load", () => {
  screen.hidden = false;
  placeholder.hidden = true;
  setStatus("正在共享", "live");
});

screen.addEventListener("error", () => {
  screen.hidden = true;
  placeholder.hidden = false;
  setStatus("连接中断，正在重试", "error");
  retryTimer = setTimeout(connect, 2500);
});

fullscreen.addEventListener("click", async () => {
  if (document.fullscreenElement) {
    await document.exitFullscreen();
  } else {
    await viewer.requestFullscreen();
  }
});

document.addEventListener("fullscreenchange", () => {
  fullscreen.textContent = document.fullscreenElement ? "退出全屏" : "全屏查看";
});

async function checkStatus() {
  try {
    const response = await fetch("/status", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    if (!data.ok) {
      setStatus(data.error || "屏幕采集失败", "error");
    }
  } catch {
    if (screen.hidden) setStatus("服务暂不可用，正在重试", "error");
  }
}

connect();
checkStatus();
setInterval(checkStatus, 5000);
