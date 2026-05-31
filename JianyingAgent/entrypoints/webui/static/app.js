const $ = (selector) => document.querySelector(selector);

const WORKFLOW_COPY = {
  script_first: {
    name: "先想内容再拍",
    short: "脚本规划",
    stageIndex: 0,
    description: "从选题、脚本和拍摄清单开始。",
    steps: ["选题", "脚本建议", "拍摄清单", "再去拍"],
  },
  material_first: {
    name: "先拍素材再提炼",
    short: "素材提炼",
    stageIndex: 1,
    description: "从已有素材里找这一期的主线。",
    steps: ["读取素材", "转写声音", "提炼方向", "生成建议"],
  },
  roughcut: {
    name: "直接自动粗剪",
    short: "自动粗剪",
    stageIndex: 4,
    description: "已有脚本和素材，先出剪映草稿。",
    steps: ["扫描素材", "转写", "筛片", "导出草稿"],
  },
};

const STAGES = ["定位", "素材理解", "可讲方向", "脚本/配音", "粗剪", "导出"];

const VIEW_TITLES = {
  home: "今天这期从哪里开始",
  project: "项目工作台",
  library: "资料库",
  settings: "设置",
};

const STATUS_COPY = {
  queued: "排队中",
  running: "执行中",
  success: "完成",
  error: "出错",
  blocked: "等待",
};

const state = {
  workflows: [],
  selectedWorkflow: null,
  latestAdvisor: null,
  pollers: new Map(),
  project: {
    name: "新一期",
    stageIndex: 0,
  },
};

async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || `Request failed: ${response.status}`);
  }
  return data;
}

function pretty(value) {
  return JSON.stringify(value, null, 2);
}

function escapeHtml(text) {
  return String(text ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function workflowById(id) {
  return state.workflows.find((item) => item.id === id);
}

function workflowCopy(id) {
  const remote = workflowById(id);
  return {
    id,
    ...(WORKFLOW_COPY[id] || {
      name: remote?.name || id || "未选择",
      short: remote?.name || id || "未选择",
      stageIndex: 0,
      description: remote?.description || "",
      steps: remote?.steps || [],
    }),
  };
}

function activateView(viewId) {
  document.querySelectorAll(".view").forEach((view) => {
    view.classList.toggle("active", view.id === `view-${viewId}`);
  });
  document.querySelectorAll(".nav-item").forEach((button) => {
    button.classList.toggle("active", button.dataset.viewTarget === viewId);
  });
  $("#view-title").textContent = VIEW_TITLES[viewId] || "项目工作台";
}

function renderStageRail(targetSelector, activeIndex = state.project.stageIndex) {
  const container = $(targetSelector);
  container.innerHTML = STAGES.map((stage, index) => {
    const className = [
      "stage-step",
      index < activeIndex ? "done" : "",
      index === activeIndex ? "active" : "",
    ]
      .filter(Boolean)
      .join(" ");
    return `
      <div class="${className}">
        <span>${index + 1}</span>
        <strong>${escapeHtml(stage)}</strong>
      </div>
    `;
  }).join("");
}

function updateProjectUi() {
  $("#active-project-name").textContent = state.project.name || "新一期";
  $("#project-title-input").value = state.project.name || "新一期";
  $("#project-stage-label").textContent = STAGES[state.project.stageIndex] || "定位";
  renderStageRail("#home-stage-rail");
  renderStageRail("#project-stage-rail");

  if (state.selectedWorkflow) {
    $("#current-workflow-badge").textContent = workflowCopy(state.selectedWorkflow).short;
  } else {
    $("#current-workflow-badge").textContent = "等待判断";
  }
}

function setSelectedWorkflow(workflowId, options = {}) {
  state.selectedWorkflow = workflowId || null;
  const selected = workflowId ? workflowCopy(workflowId) : null;

  document.querySelectorAll(".workflow-pane").forEach((panel) => {
    panel.classList.toggle("hidden", !workflowId || panel.id !== `panel-${workflowId.replaceAll("_", "-")}`);
  });

  $("#task-empty").classList.toggle("hidden", Boolean(workflowId));
  $("#workflow-form-title").textContent = selected ? selected.name : "等待判断";

  if (selected) {
    state.project.stageIndex = selected.stageIndex;
    if (options.prefill) {
      prefillWorkflow(workflowId, options.prefill);
    }
  }

  updateProjectUi();
  if (options.navigate !== false) {
    activateView("project");
  }
}

function setHealth(data) {
  $("#health-status").textContent = "已连接";
  $("#health-status").classList.add("is-ok");
  $("#health-meta").textContent = pretty(data);
  $("#profile-memory").value = data.memory_path || "";
}

function renderWorkflowCatalog(workflows) {
  const container = $("#workflow-catalog");
  container.innerHTML = workflows
    .map((workflow) => {
      const copy = workflowCopy(workflow.id);
      return `
        <article class="catalog-item">
          <strong>${escapeHtml(copy.name)}</strong>
          <p>${escapeHtml(copy.description)}</p>
          <div class="catalog-steps">${copy.steps.map((step) => `<span>${escapeHtml(step)}</span>`).join("")}</div>
        </article>
      `;
    })
    .join("");
}

function renderAdvisor(data) {
  state.latestAdvisor = data;
  const workflowId = data.recommended_workflow?.id;
  const copy = workflowCopy(workflowId);
  const modeMap = {
    llm: "大模型判断",
    constraint: "强信号判断",
    rules: "规则兜底",
    manual: "手动选择",
  };

  $("#advisor-card").classList.remove("empty");
  $("#advisor-card").innerHTML = `
    <strong>${escapeHtml(copy.name)}</strong>
    <span class="advisor-mode">${escapeHtml(modeMap[data.advisor_mode] || "系统判断")}</span>
    <p>${escapeHtml(data.reason || copy.description)}</p>
    <small>下一步：${escapeHtml(data.next_step || "补充当前阶段需要的信息。")}</small>
  `;

  const actions = $("#advisor-actions");
  actions.innerHTML = `
    <button class="primary-btn" id="continue-advisor-btn" type="button">按这个方向继续</button>
    <button class="secondary-btn" type="button" data-override-workflow="script_first">改为先想内容</button>
    <button class="secondary-btn" type="button" data-override-workflow="material_first">改为素材提炼</button>
    <button class="secondary-btn" type="button" data-override-workflow="roughcut">改为直接粗剪</button>
  `;

  $("#continue-advisor-btn").addEventListener("click", () => {
    setSelectedWorkflow(workflowId, { prefill: data.message || "" });
  });

  document.querySelectorAll("[data-override-workflow]").forEach((button) => {
    button.addEventListener("click", () => chooseWorkflow(button.dataset.overrideWorkflow));
  });
}

function renderManualChoice(workflowId) {
  const copy = workflowCopy(workflowId);
  renderAdvisor({
    recommended_workflow: { id: workflowId },
    reason: copy.description,
    next_step: "填写这一阶段需要的信息后即可执行。",
    advisor_mode: "manual",
  });
}

function prefillWorkflow(workflowId, message) {
  if (!message) return;
  if (workflowId === "script_first") {
    $("#script-first-idea").value = $("#script-first-idea").value || message;
  }
  if (workflowId === "material_first") {
    $("#material-notes").value = $("#material-notes").value || message;
  }
  if (workflowId === "roughcut") {
    $("#roughcut-script").value = $("#roughcut-script").value || message;
  }
}

function chooseWorkflow(workflowId) {
  renderManualChoice(workflowId);
  setSelectedWorkflow(workflowId);
}

async function loadHealth() {
  const data = await request("/api/health");
  setHealth(data);
}

async function loadWorkflows() {
  const data = await request("/api/workflows");
  state.workflows = data.workflows || [];
  renderWorkflowCatalog(state.workflows);
  updateProjectUi();
}

async function adviseWorkflow() {
  const message = $("#director-input").value.trim();
  if (!message) {
    $("#advisor-card").classList.remove("empty");
    $("#advisor-card").innerHTML = `<strong class="error-text">先写一句这期现在的状态。</strong>`;
    $("#advisor-actions").innerHTML = "";
    activateView("project");
    return;
  }

  try {
    const data = await request("/api/workflows/advise", {
      method: "POST",
      body: JSON.stringify({ message }),
    });
    renderAdvisor(data);
    setSelectedWorkflow(data.recommended_workflow?.id, { prefill: message });
  } catch (error) {
    $("#advisor-card").classList.remove("empty");
    $("#advisor-card").innerHTML = `<strong class="error-text">${escapeHtml(error.message)}</strong>`;
    $("#advisor-actions").innerHTML = "";
    activateView("project");
  }
}

async function loadProfile() {
  const memory = encodeURIComponent($("#profile-memory").value || "");
  $("#memory-output").textContent = "正在读取...";
  try {
    const data = await request(`/api/profile?memory=${memory}`);
    $("#memory-output").textContent = pretty(data);
  } catch (error) {
    $("#memory-output").textContent = error.message;
  }
}

async function ingestMemory() {
  $("#memory-output").textContent = "正在导入...";
  try {
    const data = await request("/api/ingest", {
      method: "POST",
      body: JSON.stringify({
        files: $("#ingest-files").value,
        out: $("#ingest-out").value,
      }),
    });
    $("#memory-output").textContent = pretty(data);
    if (data.output) {
      $("#profile-memory").value = data.output;
    }
  } catch (error) {
    $("#memory-output").textContent = error.message;
  }
}

function getWorkflowPayload(workflowId) {
  if (workflowId === "script_first") {
    return { idea: $("#script-first-idea").value };
  }
  if (workflowId === "material_first") {
    return {
      source_dir: $("#material-source-dir").value,
      project_name: $("#material-project-name").value || state.project.name,
      notes: $("#material-notes").value,
    };
  }
  if (workflowId === "roughcut") {
    const duration = Number($("#roughcut-duration").value || 180);
    const script = $("#roughcut-script").value.trim();
    return {
      source_dir: $("#roughcut-source-dir").value,
      project_name: $("#roughcut-project-name").value || state.project.name,
      script: script ? `${script}\n目标时长：约${duration}秒（${Math.floor(duration / 60)}分钟）` : "",
      subtitle_srt: $("#roughcut-srt").value,
      bgm_audio: $("#roughcut-bgm").value,
      voiceover_audio: $("#roughcut-voiceover").value,
      video_width: $("#roughcut-width").value,
      video_height: $("#roughcut-height").value,
      export_jcc: $("#roughcut-export-jcc").checked,
    };
  }
  return {};
}

async function runWorkflow(workflowId) {
  try {
    setSelectedWorkflow(workflowId, { navigate: false });
    $("#latest-result").textContent = "任务已提交，等待执行...";
    const data = await request("/api/workflows/run", {
      method: "POST",
      body: JSON.stringify({
        workflow_id: workflowId,
        payload: getWorkflowPayload(workflowId),
      }),
    });
    pollJob(data.job_id);
    loadJobs();
  } catch (error) {
    $("#latest-result").textContent = error.message;
  }
}

function renderLatestResult(job) {
  const block = $("#latest-result");
  if (!job) return;
  if (job.result) {
    block.textContent = pretty(job.result);
  } else if (job.error) {
    block.textContent = pretty(job.error);
  } else {
    block.textContent = pretty({
      workflow_id: job.workflow_id,
      status: job.status,
      message: job.message,
    });
  }
}

function updateStageFromJob(job) {
  if (job.status !== "success") return;
  if (job.workflow_id === "script_first") {
    state.project.stageIndex = 3;
  }
  if (job.workflow_id === "material_first") {
    state.project.stageIndex = 2;
  }
  if (job.workflow_id === "roughcut") {
    state.project.stageIndex = 5;
  }
  updateProjectUi();
}

function renderJob(job) {
  let node = document.querySelector(`[data-job-id="${job.id}"]`);
  if (!node) {
    node = $("#job-template").content.firstElementChild.cloneNode(true);
    node.dataset.jobId = job.id;
    $("#jobs-list").prepend(node);
  }

  const copy = workflowCopy(job.workflow_id);
  node.querySelector(".job-title").textContent = `${copy.name} · ${job.id}`;
  node.querySelector(".job-sub").textContent = `${job.created_at || ""}`;
  node.querySelector(".job-state").textContent = STATUS_COPY[job.status] || job.status;
  node.querySelector(".job-state").className = `job-state state-${job.status}`;
  node.querySelector(".job-message").textContent = job.message || "";
  node.querySelector(".job-result").textContent = job.result ? pretty(job.result) : "";
  node.querySelector(".job-logs").textContent = Array.isArray(job.logs) ? job.logs.join("\n") : "";
  renderLatestResult(job);
  updateStageFromJob(job);
}

async function loadJobs() {
  try {
    const data = await request("/api/jobs");
    (data.jobs || []).forEach(renderJob);
  } catch (error) {
    console.error(error);
  }
}

async function pollJob(jobId) {
  try {
    const job = await request(`/api/jobs/${jobId}`);
    renderJob(job);
    if (["queued", "running"].includes(job.status)) {
      const timer = setTimeout(() => pollJob(jobId), 2000);
      state.pollers.set(jobId, timer);
    } else {
      state.pollers.delete(jobId);
    }
  } catch (error) {
    console.error(error);
  }
}

function bindEvents() {
  document.querySelectorAll("[data-view-target]").forEach((button) => {
    button.addEventListener("click", () => activateView(button.dataset.viewTarget));
  });

  document.querySelectorAll("[data-pick-workflow]").forEach((button) => {
    button.addEventListener("click", () => chooseWorkflow(button.dataset.pickWorkflow));
  });

  $("#director-btn").addEventListener("click", adviseWorkflow);
  $("#refresh-jobs-btn").addEventListener("click", loadJobs);
  $("#profile-btn").addEventListener("click", loadProfile);
  $("#ingest-btn").addEventListener("click", ingestMemory);
  $("#project-title-input").addEventListener("input", (event) => {
    state.project.name = event.target.value.trim() || "新一期";
    updateProjectUi();
  });

  document.querySelectorAll("[data-run-workflow]").forEach((button) => {
    button.addEventListener("click", () => runWorkflow(button.dataset.runWorkflow));
  });
}

async function bootstrap() {
  bindEvents();
  renderStageRail("#home-stage-rail");
  renderStageRail("#project-stage-rail");

  try {
    await loadHealth();
    await loadWorkflows();
    await loadJobs();
  } catch (error) {
    $("#latest-result").textContent = error.message;
  }
}

bootstrap();
