<script setup lang="ts">
import { ref, computed } from 'vue'
import { Selector } from './selection.js'

const props = defineProps({
  selector: {
    type: Selector,
    required: true
  },
  parentPath: {
    type: Array,
    required: true
  },
  model: {
    type: Object,
    required: true
  }
})

const thisPath = computed(() => {
  return [...props.parentPath, props.model.name]
})

const isParent = computed(() => {
  if (props.model.children) {
    return true
  }
  return false
})

const isOpen = ref(false)

function onClick(event: any) {
  props.selector.select(event.target.parentElement, thisPath.value, isParent.value)
  if (props.model.children) {
    isOpen.value = !isOpen.value
  }
}
</script>
<template>
  <li class="tree-item-li">
    <div class="tree-item" @click.prevent="onClick">
      <div class="tree-item-indicator" v-show="!isOpen && model.children">+</div>
      <div class="tree-item-indicator" v-show="isOpen && model.children">-</div>
      <div class="tree-item-label">{{ model.name }}</div>
    </div>
    <ol class="tree-item-children" v-if="model.children" v-show="isOpen">
      <TreeItem
        v-for="child in model.children"
        :model="child"
        :selector="props.selector"
        :parent-path="thisPath"
        :key="child.name"
      />
    </ol>
  </li>
</template>

<style scoped>
.tree-item-li {
  list-style-type: none;
  margin: 1px;
  margin-right: 0;
}
.tree-item {
  margin: 0;
  padding: 0;
  cursor: pointer;
  display: flex;
  flex-direction: row;
  align-items: center;
  background-color: darkgray;
  border-radius: 4px;
}
.tree-item.selected {
  background-color: lightgray;
}
.tree-item-indicator {
  text-align: center;
  font-weight: bold;
  min-width: 2em;
}
.tree-item-label {
  display: flex;
  padding: 0.25em 0.5em;
  min-width: 100%;
  align-items: center;
}
.tree-item-children {
  padding-left: 1em;
}
</style>
