<script setup lang="ts">
import CommandView from '@/components/CommandView.vue'

const props = defineProps<{
  title: string
}>()

const breadcrumbs = computed(() => [
  { title: 'Home', disabled: false, to: '/' },
  { title: props.title, disabled: true }
])
</script>
<template>
  <v-responsive class="h-100">
    <div class="d-flex flex-column h-100">
      <slot name="commandview">
        <CommandView />
      </slot>
      <v-breadcrumbs :items="breadcrumbs" />
      <div class="d-flex flex-column mx-4 flex-grow-1">
        <slot name="title">
          <h2>{{ props.title }}</h2>
        </slot>
        <slot name="default" />
      </div>
    </div>
  </v-responsive>
</template>
