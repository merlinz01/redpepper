<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import dayjs from 'dayjs'
import { Confirm } from './dialogs'
import { useToast } from './toast'

const toast = useToast()

const logs = ref([])
const filterEvent = ref('')
const filterAgent = ref('')
const filteredLogs = computed(() => {
  return logs.value.filter((log) => {
    if (filterAgent.value && log.agent && log.agent != filterAgent.value) {
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

function clear() {
  logs.value = []
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
    res['Secret hash'] = log.secret_hash
  } else if (log.type === 'command_result') {
    res.ID = log.id
    if (log.status == 1) {
      res.Status = 'Success'
    } else if (log.status == 2) {
      res.Status = 'Failed'
    } else if (log.status == 3) {
      res.Status = 'Canceled'
    } else {
      res.Status = log.status
    }
    res.Changed = log.changed
  } else if (log.type === 'command_progress') {
    res.ID = log.id
    res.Progress = log.progress_current + '/' + log.progress_total
    res.Message = log.message
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
  } else if (log.type === 'command_result') {
    if (log.status == 1) {
      return 'color: var(--color-green);'
    } else if (log.status == 2) {
      return 'color: var(--color-red);'
    } else if (log.status == 3) {
      return 'color: var(--color-orange);'
    } else {
      return 'color: var(--color-blue);'
    }
  } else if (log.type === 'command_progress') {
    return 'color: var(--color-blue);'
  } else if (log.type === 'auth_success') {
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
    Confirm('If not, you will have to refresh the page before you can get real-time updates.')
      .title('Retried WebSocket connection 10 times. Continue?')
      .onConfirm(() => {
        numRetries.value = 0
        connect()
      })
      .onCancel(() => {
        toast.new(
          'Failed to connect to WebSocket. Please check your network connection and refresh the page.',
          'error',
          {
            timeout: -1
          }
        )
        document.getElementById('connection_spinner').classList.add('hidden')
      })
      .showModal()
    return
  }
  const busy = toast.new('Connecting to WebSocket...', 'info')
  ws.value = new WebSocket('/api/v1/events/ws')
  ws.value.addEventListener('open', () => {
    busy.close()
    document.getElementById('connection_spinner').classList.add('hidden')
    document.getElementById('connection_status').textContent = '\u2714'
    numRetries.value = 0
  })
  ws.value.onmessage = (event) => {
    const data = JSON.parse(event.data)
    logs.value.unshift(data)
  }
  ws.value.addEventListener('error', (event) => {
    console.log(event)
    busy.close()
    toast.new('Failed to connect to WebSocket.', 'error')
  })
  ws.value.onclose = () => {
    console.log('WebSocket closed')
    const spinner = document.getElementById('connection_spinner')
    if (spinner) {
      spinner.classList.remove('hidden')
    }
    const status = document.getElementById('connection_status')
    if (status) {
      status.textContent = '\u2716'
    }
    ws.value = null
    setTimeout(() => {
      connect()
    }, 1000)
  }
}

onMounted(() => {
  numRetries.value = 0
  document.getElementById('connection_status').textContent = '\u2716'
  connect()
})

onUnmounted(() => {
  if (ws.value) {
    ws.value.onclose = null
    ws.value.close()
  }
})
</script>

<template>
  <div id="log-view" class="gapped left-aligned column">
    <h1 class="gapped row">
      Events
      <div id="connection_status" style="color: var(--color-gray)"></div>
      <div class="spinner" id="connection_spinner"></div>
    </h1>
    <div class="gapped centered row">
      <button type="button" @click="clear">Clear</button>
      Agent:
      <select
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
          <th style="width: 15%">Time</th>
          <th style="width: 15%">Agent</th>
          <th style="width: 15%">Event</th>
          <th>Data</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="log in filteredLogs" :key="log.id" :style="getStyle(log)">
          <td>{{ formatDate(log.time) }}</td>
          <td>{{ log.agent || '(N/A)' }}</td>
          <td>{{ log.type }}</td>
          <td>
            <div class="event-attrs column">
              <span v-for="(v, k) in formatData(log)" :key="k">
                <span style="color: var(--color-gray)">{{ k }}: </span>{{ v }}</span
              >
              <pre
                class="command-output"
                v-if="log.type === 'command_result' && log.output"
                style="max-height: 2.5em; overflow: hidden; cursor: pointer"
                @click="
                  (event) => {
                    event.target.style.maxHeight = null
                    event.target.style.overflow = null
                    event.target.style.cursor = null
                  }
                "
                @dblclick="
                  (event) => {
                    event.target.style.maxHeight = '2.5em'
                    event.target.style.overflow = 'hidden'
                    event.target.style.cursor = 'pointer'
                  }
                "
                >{{ log.output }}</pre
              >
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.command-output {
  color: var(--color-text);
}
</style>
