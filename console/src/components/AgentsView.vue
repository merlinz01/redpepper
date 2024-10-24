<script setup lang="ts">
import DashboardPage from '@/components/DashboardPage.vue'

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
  axios
    .get('/api/v1/agents')
    .then((response) => {
      agents.value = response!.data.agents
    })
    .catch((error) => {
      if (error.response?.status == 401) {
        notifications.post({ text: 'Please log in', type: 'error' })
        router.push('/login')
        return
      }
      agents.value = [{ id: '[Failed to fetch agents]', connected: '' }]
      notifications.post({ text: 'Failed to fetch agents: ' + error, type: 'error' })
    })
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
