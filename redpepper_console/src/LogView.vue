<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const logs = ref([])
const lastrefresh = ref(0)

const refresh = () => {
  fetch('https://localhost:8080/api/v1/logs', {
    credentials: 'include'
  })
    .then((response) => {
      if (response.status == 401) {
        router.push('/login')
        return
      }
      if (!response.ok) {
        throw new Error('Failed to fetch logs')
      }
      response.json().then((data) => {
        logs.value = data.logs
        lastrefresh.value = Date.now()
      })
    })
    .catch((error) => {
      console.log(error)
      alert(error)
    })
}
</script>

<template>
  <div id="log-view" class="padded gapped left-aligned column">
    <h1>Agent Logs</h1>
    <button type="button" @click="refresh">Refresh</button>
    <p>
      Last refreshed: {{ lastrefresh === 0 ? 'Never' : new Date(lastrefresh).toLocaleString() }}
    </p>
    <input type="text" id="filter" name="filter" placeholder="Filter" />
    <table class="full-width">
      <thead>
        <tr>
          <th style="width: 20%">Time</th>
          <th style="width: 20%">Agent</th>
          <th>Event</th>
          <th>Data</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="log in logs" :key="log.id">
          <td>{{ new Date(log.time).toLocaleString() }}</td>
          <td>{{ log.agent }}</td>
          <td>{{ log.event }}</td>
          <td>{{ log.data }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
