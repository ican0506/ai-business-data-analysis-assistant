async function showServiceStatus() {
  const target = document.querySelector("#service-status");
  try {
    const response = await fetch("/api/v1/health");
    const payload = await response.json();
    const status = payload.data.status;
    target.textContent = status === "ok" ? "服务与数据库连接正常" : "服务已启动，数据库暂不可用";
    target.classList.add(status);
  } catch {
    target.textContent = "无法连接后端服务，请稍后重试";
    target.classList.add("error");
  }
}

showServiceStatus();
