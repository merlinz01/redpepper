<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import CommandView from './CommandView.vue'
const router = useRouter()

const agents = ref([{ id: '[Please click Refresh]', connected: false }])

const refresh = () => {
  fetch('/api/v1/agents', {
    credentials: 'include'
  })
    .then((response) => {
      if (response.status == 401) {
        router.push('/login')
        return
      }
      if (!response.ok) {
        throw new Error('Failed to fetch agents')
      }
      response.json().then((data) => {
        agents.value = data.agents
      })
    })
    .catch((error) => {
      agents.value = [{ id: '[Failed to fetch agents]', connected: false }]
      console.log(error)
      alert(error)
    })
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
