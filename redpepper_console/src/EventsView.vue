<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import dayjs from 'dayjs'
import CommandView from './CommandView.vue'

const router = useRouter()

const logs = ref([])
const filterEvent = ref('')
const filterAgent = ref('')
const filteredLogs = computed(() => {
  return logs.value.filter((log) => {
    if (filterAgent.value && log.agent != filterAgent.value) {
      return false
    }
    if (filterEvent.value && !log.type.includes(filterEvent.value)) {
      return false
    }
    return true
  })
})
const agentsPresent = computed(() => {
  const agents = new Set()
  logs.value.forEach((log) => {
    if (log.agent) {
      agents.add(log.agent)
    }
  })
  return Array.from(agents)
})

const ws = ref(null)

const numRetries = ref(0)

const refresh = () => {
  const url = new URL('https://localhost:8080/api/v1/events/since')
  url.searchParams.append(
    'since',
    new Date(document.getElementById('since').value).getTime() / 1000
  )
  fetch(url, {
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
        logs.value = data.events
      })
    })
    .catch((error) => {
      console.log(error)
      alert(error)
    })
}

function formatDate(date) {
  date = date * 1000
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

function formatData(log) {
  let res = {}
  if (log.type === 'connected') {
    res.IP = log.ip
  } else if (log.type === 'disconnected') {
    res.IP = log.ip
  } else if (log.type === 'auth_success') {
    res.IP = log.ip
  } else if (log.type === 'auth_failure') {
    res.IP = log.ip
    res['Certificate hash'] = log.cert_hash
    res['Secret hash'] = log.secret_hash
  } else if (log.type === 'command_status') {
    res.ID = log.command_id
    if (log.status == 0) {
      res.Status = 'Pending'
    } else if (log.status == 1) {
      res.Status = 'Success'
    } else if (log.status == 2) {
      res.Status = 'Failed'
    } else {
      res.Status = log.status
    }
    res.Progress = log.progress_current + '/' + log.progress_total
    res.Output = '\n' + log.output
  } else if (log.type == 'command') {
    res.ID = log.id
    res.Command = log.command
    res.Arguments = log.args
    res.Parameters = log.kw
  } else {
    res = log
  }
  return res
}

function getStyle(log) {
  if (log.type === 'command') {
    return 'color: var(--color-blue);'
  } else if (log.type === 'command_status') {
    if (log.status == 1) {
      return 'color: var(--color-green);'
    } else if (log.status == 2) {
      return 'color: var(--color-red);'
    } else {
      return 'color: var(--color-gray);'
    }
  }
  if (log.type === 'auth_success') {
    return 'color: var(--color-purple);'
  } else if (log.type === 'auth_failure') {
    return 'color: var(--color-red);'
  } else if (log.type == 'disconnected') {
    return 'color: var(--color-orange);'
  } else if (log.type == 'connected') {
    return 'color: var(--color-brown);'
  } else {
    return ''
  }
}

function connect() {
  if (ws.value) {
    ws.value.close()
  }
  numRetries.value++
  if (numRetries.value >= 10) {
    if (
      confirm(
        'Retried WebSocket connection 10 times. Continue?\nIf not, you will have to refresh the page before you can get real-time updates.'
      )
    ) {
      numRetries.value = 0
    } else {
      return
    }
  }
  console.log('Connecting to WebSocket...')
  ws.value = new WebSocket('wss://localhost:8080/api/v1/events/ws')
  ws.value.onmessage = (event) => {
    const data = JSON.parse(event.data)
    logs.value.unshift(data)
  }
  ws.value.onclose = () => {
    console.log('WebSocket closed')
    ws.value = null
    setTimeout(() => {
      connect()
    }, 1000)
  }
}

onMounted(() => {
  document.getElementById('since').value = dayjs().subtract(1, 'day').format('YYYY-MM-DDTHH:mm:ss')
  connect()
  refresh()
})

onUnmounted(() => {
  if (ws.value) {
    ws.value.onclose = null
    ws.value.close()
  }
})
</script>

<template>
  <CommandView />
  <div id="log-view" class="well-padded gapped left-aligned column">
    <h1>Events</h1>
    <div class="gapped centered row">
      <button type="button" @click="refresh">Refresh</button>
      <label for="date">Since:</label>
      <input type="datetime-local" id="since" />
      Agent:
      <select
        type="search"
        id="filter_agent"
        name="filter_agent"
        placeholder="Filter by agent"
        v-model="filterAgent"
      >
        <option value="">All</option>
        <option v-for="agent in agentsPresent" :key="agent" :value="agent">
          {{ agent }}
        </option>
      </select>
      <input
        type="search"
        id="filter_event"
        name="filter_event"
        placeholder="Filter by event type"
        v-model="filterEvent"
      />
    </div>
    <table class="full-width">
      <thead>
        <tr>
          <th style="width: 2em">ID</th>
          <th>Time</th>
          <th>Agent</th>
          <th>Event</th>
          <th>Data</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="log in filteredLogs" :key="log.id" :style="getStyle(log)">
          <td>{{ log.id }}</td>
          <td>{{ formatDate(log.time) }}</td>
          <td>{{ log.agent || '(N/A)' }}</td>
          <td>{{ log.type }}</td>
          <td>
            <pre v-for="(v, k) in formatData(log)" :key="k">{{ k }}: {{ v }}</pre>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
