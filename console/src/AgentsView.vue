<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Fetch from './fetcher'
import { useToast } from './toast'

const router = useRouter()
const toast = useToast()

const agents = ref([{ id: '[Agents not loaded]', connected: '' }])

function refresh() {
  const busy = toast.new('Fetching agents...', 'info')
  Fetch('/api/v1/agents')
    .onError((error) => {
      busy.close()
      agents.value = [{ id: '[Failed to fetch agents]', connected: '' }]
      toast.new('Failed to fetch agents: ' + error, 'error')
    })
    .onStatus(401, () => {
      busy.close()
      toast.new('Please log in.', 'error')
      router.push('/login')
    })
    .onSuccess((data) => {
      busy.close()
      agents.value = data.agents
    })
    .credentials('same-origin')
    .get()
}

onMounted(() => {
  refresh()
})
</script>

<template>
  <div id="agents-view" class="gapped left-aligned column">
    <h1>Agents</h1>
    <button type="button" @click="refresh">Refresh</button>
    <table class="full-width">
      <thead>
        <tr>
          <th style="width: 50%">ID</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="agent in agents" :key="agent.id">
          <td>{{ agent.id }}</td>
          <td>{{ agent.connected ? 'Connected' : 'Not connected' }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
