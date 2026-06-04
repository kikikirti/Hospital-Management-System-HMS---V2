<template>
  <div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
    <div>
      <h1 class="h3 mb-0">Admin Dashboard</h1>
      <span class="text-muted small">System snapshot</span>
    </div>

    <div class="d-flex gap-2 flex-wrap">
      <button
        class="btn btn-outline-primary btn-sm"
        :disabled="runningDaily || trackingJob"
        @click="runDailyReminder"
      >
        {{ runningDaily ? "Running Daily Reminders..." : "Trigger Daily Reminder Job" }}
      </button>

      <button
        class="btn btn-outline-success btn-sm"
        :disabled="runningMonthly || trackingJob"
        @click="runMonthlyReport"
      >
        {{ runningMonthly ? "Running Monthly Reports..." : "Trigger Monthly Report Job" }}
      </button>
    </div>
  </div>

  <div v-if="jobMessage" class="alert alert-info">
    {{ jobMessage }}
  </div>

  <div v-if="trackingJob" class="alert alert-warning">
    <div><strong>Tracking:</strong> {{ currentTaskType }}</div>
    <div><strong>Task ID:</strong> {{ currentTaskId }}</div>
    <div><strong>Status:</strong> {{ currentTaskState }}</div>
  </div>

  <div v-if="error" class="alert alert-danger">{{ error }}</div>

  <section class="mb-4">
    <div class="row g-3">
      <div class="col-md-4" v-for="c in cards" :key="c.title">
        <div class="card shadow-sm h-100">
          <div class="card-body">
            <h5 class="card-title">{{ c.title }}</h5>
            <p class="display-6 mb-0">{{ c.value }}</p>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, onBeforeUnmount, ref } from "vue";
import { api } from "@/services/api";
import { flash } from "@/stores/flash";

const summary = ref(null);
const error = ref("");
const jobMessage = ref("");

const runningDaily = ref(false);
const runningMonthly = ref(false);

const currentTaskId = ref("");
const currentTaskType = ref("");
const currentTaskState = ref("");
const trackingJob = ref(false);

let pollTimer = null;

const cards = computed(() => {
  if (!summary.value) return [];
  return [
    { title: "Total Doctors", value: summary.value.total_doctors },
    { title: "Total Patients", value: summary.value.total_patients },
    { title: "Total Appointments", value: summary.value.total_appts },
    { title: "Live (Booked)", value: summary.value.booked_appts },
    { title: "Completed", value: summary.value.completed_appts },
    { title: "Cancelled", value: summary.value.cancelled_appts },
  ];
});

async function load() {
  error.value = "";
  try {
    const res = await api.get("/admin/summary");
    summary.value = res.data;
  } catch (e) {
    error.value = e?.response?.data?.error || "Failed to load dashboard";
  }
}

async function checkJobStatus(taskId) {
  try {
    const res = await api.get(`/admin/jobs/${taskId}/status`);
    currentTaskState.value = res.data?.state || "UNKNOWN";

    if (res.data?.ready) {
      trackingJob.value = false;

      if (pollTimer) {
        clearInterval(pollTimer);
        pollTimer = null;
      }

      if (res.data?.successful) {
        const resultText = res.data?.result ? ` Result: ${JSON.stringify(res.data.result)}` : "";
        jobMessage.value = `${currentTaskType.value} finished successfully.${resultText}`;
        flash.push("success", `${currentTaskType.value} finished successfully`);
      } else {
        jobMessage.value = `${currentTaskType.value} failed.`;
        flash.push("danger", `${currentTaskType.value} failed`);
      }
    }
  } catch (e) {
    trackingJob.value = false;

    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }

    jobMessage.value = e?.response?.data?.error || "Failed to check background job status";
    flash.push("danger", "Failed to check background job status");
  }
}

function startPolling(taskId, taskType) {
  currentTaskId.value = taskId;
  currentTaskType.value = taskType;
  currentTaskState.value = "PENDING";
  trackingJob.value = true;

  if (pollTimer) {
    clearInterval(pollTimer);
  }

  pollTimer = setInterval(() => {
    checkJobStatus(taskId);
  }, 2000);
}

async function runDailyReminder() {
  runningDaily.value = true;
  jobMessage.value = "";

  try {
    const res = await api.post("/admin/jobs/daily-reminders/run");
    const taskId = res.data?.task_id;

    jobMessage.value = res.data?.message || "Daily reminder job queued";
    flash.push("success", "Daily reminder job triggered successfully");

    if (taskId) {
      startPolling(taskId, "Daily reminder job");
    }
  } catch (e) {
    const msg = e?.response?.data?.error || "Failed to trigger daily reminder job";
    jobMessage.value = msg;
    flash.push("danger", msg);
  } finally {
    runningDaily.value = false;
  }
}

async function runMonthlyReport() {
  runningMonthly.value = true;
  jobMessage.value = "";

  try {
    const res = await api.post("/admin/jobs/monthly-reports/run");
    const taskId = res.data?.task_id;

    jobMessage.value = res.data?.message || "Monthly report job queued";
    flash.push("success", "Monthly report job triggered successfully");

    if (taskId) {
      startPolling(taskId, "Monthly report job");
    }
  } catch (e) {
    const msg = e?.response?.data?.error || "Failed to trigger monthly report job";
    jobMessage.value = msg;
    flash.push("danger", msg);
  } finally {
    runningMonthly.value = false;
  }
}

onMounted(load);

onBeforeUnmount(() => {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
});
</script>