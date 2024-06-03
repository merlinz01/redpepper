<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import CommandView from './CommandView.vue'
import Fetch from './fetcher'

const router = useRouter()

const agents = ref([{ id: '[Agents not loaded]', connected: '' }])

function refresh() {
  Fetch('/api/v1/agents')
    .onError((error) => {
      agents.value = [{ id: '[Failed to fetch agents]', connected: '' }]
      console.log('Failed to fetch agents: ' + error)
      alert('Failed to fetch agents:\n' + error)
    })
    .onStatus(401, () => {
      console.log('Unauthorized. Redirecting to login page.')
      router.push('/login')
    })
    .onSuccess((data) => {
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
  <CommandView />
  <div id="agents-view" class="well-padded gapped left-aligned column">
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

<style scoped>
#agents-view {
  padding-top: 9rem;
}
</style>
