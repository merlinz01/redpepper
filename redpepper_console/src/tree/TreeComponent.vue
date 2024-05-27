<script setup>
import TreeItem from './TreeItem.vue'
import { Selector } from './selection.js'

// eslint-disable-next-line no-unused-vars
const props = defineProps({
  model: Array
})

const emit = defineEmits(['itemSelected'])

const selector = new Selector()
selector.onSelect = (element, path, isParent) => {
  emit('itemSelected', element, path, isParent)
}
</script>

<template>
  <div class="tree">
    <ol v-if="props.model && props.model.length">
      <TreeItem
        v-for="item in model"
        :key="item.name"
        :model="item"
        :selector="selector"
        :parentPath="[]"
      />
    </ol>
  </div>
</template>

<style scoped>
div.tree {
  padding: 0;
  border: 1px solid var(--color-border);
  background-color: var(--color-background-input);
  border-radius: var(--border-radius);
  overflow-y: auto;
  overflow-x: hidden;
}
div.tree > ol {
  padding: 0;
  margin: 0;
  list-style-type: none;
  margin-right: 1px;
}
</style>
