<script setup lang="ts">
import CommandView from '@/components/CommandForm.vue'

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
      <v-breadcrumbs :items="breadcrumbs" density="comfortable" class="pb-0" />
      <div class="d-flex flex-column mx-4 flex-grow-1">
        <div class="d-flex ga-2 my-2">
          <slot name="title">
            <h2>{{ props.title }}</h2>
            <slot name="after_title"></slot>
          </slot>
        </div>
        <slot name="default" />
      </div>
    </div>
  </v-responsive>
</template>
