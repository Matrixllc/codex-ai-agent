const healthStatus = document.getElementById("healthStatus");
const healthDetail = document.getElementById("healthDetail");
const ingestForm = document.getElementById("ingestForm");
const searchForm = document.getElementById("searchForm");
const ingestOutput = document.getElementById("ingestOutput");
const searchOutput = document.getElementById("searchOutput");
const fillSampleUrl = document.getElementById("fillSampleUrl");
const ingestUrl = document.getElementById("ingestUrl");

const SAMPLE_URL = "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide";

function setBusy(button, busy, label) {
  button.disabled = busy;
  button.dataset.originalText ||= button.textContent;
  button.textContent = busy ? label : button.dataset.originalText;
}

async function requestJson(url, options) {
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
    ...options,
  });

  let data = null;
  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (!response.ok) {
    const message = data?.detail || response.statusText || "请求失败";
    throw new Error(Array.isArray(message) ? message.join(", ") : message);
  }

  return data;
}

function formatIngest(data) {
  return [
    `状态: ${data.status}`,
    `文章: ${data.title}`,
    `Article ID: ${data.article_id}`,
    `Chunk 数: ${data.chunk_count}`,
    `Markdown: ${data.markdown_path}`,
  ].join("\n");
}

function renderSearch(results) {
  if (!results.length) {
    searchOutput.innerHTML = '<div class="empty">没有找到匹配结果。</div>';
    return;
  }

  searchOutput.innerHTML = results
    .map(
      (item) => `
        <article class="result-card">
          <div class="result-meta">
            <span class="result-score">score ${(item.score ?? 0).toFixed(4)}</span>
            <span>${item.title}</span>
            <span>chunk #${item.chunk_index}</span>
          </div>
          <h3 class="result-title">${item.article_id}</h3>
          <p class="result-text">${item.text}</p>
          <p class="result-meta">${item.url}</p>
        </article>
      `
    )
    .join("");
}

async function checkHealth() {
  try {
    const data = await requestJson("/health");
    healthStatus.textContent = "在线";
    healthStatus.style.color = "var(--ok)";
    healthDetail.textContent = JSON.stringify(data);
  } catch (error) {
    healthStatus.textContent = "离线";
    healthStatus.style.color = "var(--warn)";
    healthDetail.textContent = error.message;
  }
}

ingestForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = ingestForm.querySelector("button");
  setBusy(button, true, "处理中...");
  ingestOutput.textContent = "正在抓取与入库，请稍候...";

  try {
    const url = ingestUrl.value.trim();
    const data = await requestJson("/ingest", {
      method: "POST",
      body: JSON.stringify({ url }),
    });
    ingestOutput.textContent = formatIngest(data);
  } catch (error) {
    ingestOutput.textContent = `失败：${error.message}`;
  } finally {
    setBusy(button, false);
  }
});

fillSampleUrl.addEventListener("click", () => {
  ingestUrl.value = SAMPLE_URL;
  ingestUrl.focus();
  ingestOutput.textContent = "已填入示例链接，点击“开始抓取并入库”即可测试。";
});

searchForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = searchForm.querySelector("button");
  setBusy(button, true, "搜索中...");
  searchOutput.innerHTML = '<div class="empty">正在搜索...</div>';

  try {
    const query = document.getElementById("searchQuery").value.trim();
    const topK = Number(document.getElementById("searchTopK").value || 5);
    const data = await requestJson("/search", {
      method: "POST",
      body: JSON.stringify({ query, top_k: topK }),
    });
    renderSearch(data.results || []);
  } catch (error) {
    searchOutput.innerHTML = `<div class="empty">失败：${error.message}</div>`;
  } finally {
    setBusy(button, false);
  }
});

checkHealth();
