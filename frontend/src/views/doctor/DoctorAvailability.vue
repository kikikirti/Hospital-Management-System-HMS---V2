<template>
  <div class="row g-3">
    <div class="col-lg-5">
      <div class="card shadow-sm">
        <div class="card-header">
          <h2 class="h5 mb-0">Provide Availability</h2>
          <small class="text-muted">Add slots for the next 7 days</small>
        </div>

        <div class="card-body">
          <div v-if="days.length" class="mb-3">
            <p class="text-muted mb-1">Quick pick:</p>
            <div class="d-flex flex-wrap gap-2">
              <button
                v-for="d in days"
                :key="d.iso"
                class="btn btn-sm"
                :class="form.date === d.iso ? 'btn-success' : 'btn-outline-secondary'"
                @click="selectDate(d.iso)"
                type="button"
              >
                {{ d.label }}
              </button>
            </div>
          </div>

          <form @submit.prevent="submit">
            <div class="mb-3">
              <label class="form-label">Date</label>
              <input class="form-control" type="date" v-model="form.date" required />
            </div>

            <div class="mb-3">
              <label class="form-label">Start Time</label>
              <input class="form-control" type="time" v-model="form.start_time" required />
            </div>

            <div class="mb-3">
              <label class="form-label">End Time</label>
              <input class="form-control" type="time" v-model="form.end_time" required />
            </div>

            <div class="d-grid">
              <button class="btn btn-primary" type="submit" :disabled="submitting">
                {{ submitting ? "Adding..." : "Add Slot" }}
              </button>
            </div>
          </form>

          <div v-if="error" class="alert alert-danger mt-3 mb-0">{{ error }}</div>
        </div>
      </div>
    </div>

    <div class="col-lg-7">
      <div class="card shadow-sm">
        <div class="card-header">
          <h2 class="h5 mb-0">My Upcoming Slots (Next 7 Days)</h2>
        </div>

        <div class="card-body p-0">
          <div v-if="loading" class="p-3 text-muted">Loading...</div>

          <div v-else-if="slots.length" class="table-responsive">
            <table class="table table-striped table-hover table-sm mb-0 align-middle">
              <thead class="table-light">
                <tr>
                  <th>Date</th>
                  <th>From</th>
                  <th>To</th>
                  <th class="text-end">Action</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="s in slots" :key="s.id">
                  <td>{{ s.avail_date }}</td>
                  <td>{{ s.start_time }}</td>
                  <td>{{ s.end_time }}</td>
                  <td class="text-end">
                    <button
                      class="btn btn-sm btn-outline-danger"
                      @click="removeSlot(s.id)"
                      :disabled="deletingId === s.id"
                    >
                      {{ deletingId === s.id ? "Deleting..." : "Delete" }}
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <p v-else class="m-3 text-muted">No upcoming slots found. Add availability on the left.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import api from "@/services/api";
import { flash } from "@/stores/flash";

const days = ref([]);
const slots = ref([]);
const loading = ref(false);
const submitting = ref(false);
const deletingId = ref(null);
const error = ref("");

const form = reactive({
  date: "",
  start_time: "",
  end_time: "",
});

function buildNext7Days() {
  const out = [];
  const now = new Date();

  for (let i = 1; i <= 7; i++) {
    const d = new Date(now);
    d.setDate(now.getDate() + i);

    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    const iso = `${year}-${month}-${day}`;

    const label = d.toLocaleDateString(undefined, {
      weekday: "short",
      day: "2-digit",
      month: "short",
    });

    out.push({ iso, label });
  }

  days.value = out;
}

function selectDate(iso) {
  form.date = iso;
}

function sortSlots() {
  slots.value.sort((a, b) => {
    const da = `${a.avail_date} ${a.start_time}`;
    const db = `${b.avail_date} ${b.start_time}`;
    return da.localeCompare(db);
  });
}

async function load() {
  loading.value = true;
  try {
    const r = await api.get("/doctor/availability", {
      params: { _ts: Date.now() },
    });
    slots.value = r.data.slots || [];
    sortSlots();
  } catch (e) {
    flash.push("danger", e?.response?.data?.error || "Failed to load availability");
  } finally {
    loading.value = false;
  }
}

async function submit() {
  error.value = "";
  submitting.value = true;

  try {
    const r = await api.post("/doctor/availability", { ...form });
    flash.push("success", "Availability added");

    const created = r?.data?.slot;
    if (created) {
      slots.value.push(created);
      sortSlots();
    } else {
      await load();
    }

    form.start_time = "";
    form.end_time = "";
  } catch (e) {
    error.value = e?.response?.data?.error || "Failed to add availability";
  } finally {
    submitting.value = false;
  }
}

async function removeSlot(id) {
  deletingId.value = id;
  try {
    await api.delete(`/doctor/availability/${id}`);
    slots.value = slots.value.filter((s) => s.id !== id);
    flash.push("success", "Availability deleted");
  } catch (e) {
    flash.push("danger", e?.response?.data?.error || "Failed to delete availability");
  } finally {
    deletingId.value = null;
  }
}

onMounted(() => {
  buildNext7Days();
  load();
});
</script>