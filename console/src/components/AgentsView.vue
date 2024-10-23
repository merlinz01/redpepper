<script setup lang="ts">
import Fetch from '@/fetcher'
import DashboardPage from '@/components/DashboardPage.vue'
import useNotifications from '@/stores/notifications'
import useMessages from '@/stores/messages'

const router = useRouter()
const notifications = useNotifications()
const messages = useMessages()

const agents = ref([{ id: '[Agents not loaded]', connected: '' }])
const headers = [
  { title: 'ID', value: 'id' },
  { title: 'Status', value: 'connected' }
]

function refresh() {
  const busy = messages.addMessage({ text: 'Fetching agent list...', timeout: 0 })
  Fetch('/api/v1/agents')
    .onError((error: any) => {
      agents.value = [{ id: '[Failed to fetch agents]', connected: '' }]
      notifications.post({ text: 'Failed to fetch agents: ' + error, type: 'error' })
    })
    .onStatus(401, () => {
      notifications.post({ text: 'Please log in', type: 'error' })
      router.push('/login')
    })
    .onSuccess((data: any) => {
      agents.value = data.agents
    })
    .credentials('same-origin')
    .get()
    .finally(() => {
      messages.removeMessage(busy)
    })
}

onMounted(() => {
  refresh()
})
</script>

<template>
  <DashboardPage title="Agents">
    <v-btn type="button" @click="refresh" text="Refresh" class="my-1 me-auto" />
    <v-data-table :headers="headers" :items="agents" density="comfortable" class="rounded">
      <template #item.connected="{ item }">
        <v-chip
          label
          :color="item.connected ? 'success' : 'error'"
          :text="item.connected ? 'Connected' : 'Disconnected'"
          :prepend-icon="item.connected ? 'mdi-check' : 'mdi-close'"
        />
      </template>
    </v-data-table>
  </DashboardPage>
</template>
