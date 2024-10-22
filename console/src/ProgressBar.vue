<script setup lang="ts">
const props = defineProps({
  progress: {
    type: Number,
    required: true
  },
  background: {
    type: String,
    default: 'var(--color-primary)'
  }
})
</script>

<template>
  <div class="progress-bar" :style="`border-color: ${props.background}`">
    <div
      class="progress-bar-inner"
      :style="`width: ${props.progress}%;background: ${props.background}`"
    ></div>
  </div>
</template>

<style scoped>
.progress-bar {
  background: var(--color-background-accent);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius);
  height: 1rem;
  padding: 2px;
  width: 100%;
  margin: 0.25rem;
}
.progress-bar-inner {
  background: var(--color-background-input);
  border-radius: var(--border-radius);
  height: 100%;
  transition:
    width 0.5s,
    background-color 0.5s;
}
</style>
