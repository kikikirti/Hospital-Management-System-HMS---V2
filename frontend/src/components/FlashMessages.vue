<template>
  <div v-if="flash.messages.length" class="mb-3">
    <div
      v-for="m in flash.messages"
      :key="m.id"
      class="alert alert-dismissible fade show"
      :class="'alert-' + normalize(m.category)"
      role="alert"
    >
      {{ m.text }}
      <button type="button" class="btn-close" @click="flash.remove(m.id)" aria-label="Close"></button>
    </div>
  </div>
</template>

<script setup>
import { flash } from "@/stores/flash";

function normalize(cat) {
  return ["success", "danger", "warning", "info"].includes(cat) ? cat : "info";
}
</script>
