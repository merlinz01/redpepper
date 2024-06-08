<script setup>
const props = defineProps({
  progress: Number
})
</script>

<template>
  <div class="progress-bar">
    <div class="progress-bar-inner" :style="`width: ${props.progress}%`"></div>
  </div>
</template>

<style scoped>
.progress-bar {
  background: var(--color-background-accent);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius);
  height: 2rem;
  padding: 2px;
  width: 100%;
}
.progress-bar-inner {
  background: var(--color-background-input);
  border-radius: var(--border-radius);
  height: 100%;
  transition: width 0.5s;
}
</style>
