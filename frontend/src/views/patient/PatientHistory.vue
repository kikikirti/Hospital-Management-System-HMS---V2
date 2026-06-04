<template>
  <div>
    <div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
      <h2 class="h4 mb-0">Treatment History</h2>

      <div class="d-flex gap-2">
        <button
          class="btn btn-primary btn-sm"
          :disabled="exportLoading"
          @click="triggerExport"
        >
          {{ exportLoading ? "Generating..." : "Export CSV" }}
        </button>

        <button class="btn btn-outline-secondary btn-sm" @click="loadExports">
          Refresh Export Status
        </button>
      </div>
    </div>

    <div v-if="latestExport" class="alert" :class="exportAlertClass">
      <div><strong>Latest Export Status:</strong> {{ latestExport.status }}</div>
      <div v-if="latestExport.file_name">File: {{ latestExport.file_name }}</div>
      <div v-if="latestExport.error_message" class="text-danger">
        Error: {{ latestExport.error_message }}
      </div>
      <div v-if="latestExport.download_url" class="mt-2">
        <button
          class="btn btn-success btn-sm"
          @click="downloadExport(latestExport)"
        >
          Download CSV
        </button>
      </div>
    </div>

    <div v-if="appointments.length" class="card shadow-sm">
      <div class="card-body p-0">
        <div class="table-responsive">
          <table class="table table-striped table-hover table-sm mb-0 align-middle">
            <thead class="table-light">
              <tr>
                <th>Date</th>
                <th>Time</th>
                <th>Doctor</th>
                <th>Diagnosis</th>
                <th>Prescription</th>
                <th>Notes</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="a in appointments" :key="a.id">
                <td>{{ a.appt_date }}</td>
                <td>{{ a.appt_time }}</td>
                <td>Dr. {{ a.doctor_name }}</td>
                <td>{{ a.diagnosis || "N/A" }}</td>
                <td>{{ a.prescription || "N/A" }}</td>
                <td>{{ a.notes || "N/A" }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <p v-else class="text-muted">No treatment history available.</p>

    <div class="mt-4" v-if="exports.length">
      <h3 class="h6">Previous Export Jobs</h3>
      <div class="card shadow-sm">
        <div class="table-responsive">
          <table class="table table-sm mb-0 align-middle">
            <thead class="table-light">
              <tr>
                <th>ID</th>
                <th>Status</th>
                <th>Created</th>
                <th>File</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="job in exports" :key="job.id">
                <td>{{ job.id }}</td>
                <td>{{ job.status }}</td>
                <td>{{ job.created_at }}</td>
                <td>{{ job.file_name || "—" }}</td>
                <td>
                  <button
                    v-if="job.download_url"
                    class="btn btn-success btn-sm"
                    @click="downloadExport(job)"
                  >
                    Download
                  </button>
                  <span v-else class="text-muted">Not ready</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import api from "@/services/api";
import { flash } from "@/stores/flash";

const appointments = ref([]);
const exports = ref([]);
const exportLoading = ref(false);

const latestExport = computed(() => exports.value.length ? exports.value[0] : null);

const exportAlertClass = computed(() => {
  const status = latestExport.value?.status;
  if (status === "completed") return "alert-success";
  if (status === "failed") return "alert-danger";
  return "alert-info";
});

async function load() {
  try {
    const r = await api.get("/patient/history");
    appointments.value = r.data.appointments || [];
  } catch (e) {
    flash.push("danger", e?.response?.data?.error || "Failed to load treatment history");
  }
}

async function loadExports() {
  try {
    const r = await api.get("/patient/exports");
    exports.value = r.data.exports || [];
  } catch (e) {
    flash.push("danger", e?.response?.data?.error || "Failed to load export jobs");
  }
}

async function triggerExport() {
  exportLoading.value = true;
  try {
    const r = await api.post("/patient/exports/treatments");
    flash.push("success", r?.data?.message || "Export job created");
    await loadExports();
  } catch (e) {
    flash.push("danger", e?.response?.data?.error || "Failed to create export job");
  } finally {
    exportLoading.value = false;
  }
}

async function downloadExport(job) {
  try {
    if (!job?.download_url) {
      flash.push("warning", "Export file is not ready yet");
      return;
    }

    const requestUrl = job.download_url.replace(/^\/api/, "");

    const response = await api.get(requestUrl, {
      responseType: "blob",
    });

    const blob = new Blob([response.data], { type: "text/csv;charset=utf-8;" });
    const url = window.URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.download = job.file_name || `patient_export_${job.id}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);

    flash.push("success", "CSV downloaded successfully");
  } catch (e) {
    console.error("Download CSV error:", e);

    if (e?.response?.data instanceof Blob) {
      try {
        const text = await e.response.data.text();
        const parsed = JSON.parse(text);
        flash.push("danger", parsed?.error || parsed?.msg || "Failed to download CSV");
        return;
      } catch {
        flash.push("danger", "Failed to download CSV");
        return;
      }
    }

    flash.push("danger", e?.response?.data?.error || e?.response?.data?.msg || e?.message || "Failed to download CSV");
  }
}

onMounted(async () => {
  await load();
  await loadExports();
});
</script>