import { reactive } from "vue";

export const flash = reactive({
  messages: [], // { id, category, text }

  push(category, text) {
    this.messages.push({ id: crypto.randomUUID(), category, text });
  },

  remove(id) {
    this.messages = this.messages.filter((m) => m.id !== id);
  },

  clear() {
    this.messages = [];
  },
});
