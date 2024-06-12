<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import dayjs from 'dayjs'
import Fetch from './fetcher'
import { Confirm } from './dialogs'
import ProgressBar from './ProgressBar.vue'
import { useToast } from './toast'

const router = useRouter()
const toast = useToast()

const commands = ref([])

const filterAgent = ref('')
const filteredCommands = computed(() => {
  if (filterAgent.value === '') {
    return commands.value
  }
  return commands.value.filter((command) => {
    return command.agent === filterAgent.value
  })
})
const agentsPresent = computed(() => {
  const agents = new Set()
  commands.value.forEach((command) => {
    agents.add(command.agent)
  })
  return agents
})

const ws = ref(null)

const numRetries = ref(0)

function refresh() {
  const busy = toast.new('Fetching latest commands...', 'info')
  Fetch('/api/v1/commands/last')
    .query('max', 100)
    .onError((error) => {
      busy.close()
      commands.value = []
      toast.new('Failed to fetch commands: ' + error, 'error')
    })
    .onStatus(401, () => {
      busy.close()
      toast.new('Please log in.', 'error')
      router.push('/login')
    })
    .onSuccess((data) => {
      busy.close()
      commands.value = data.commands
    })
    .credentials('same-origin')
    .get()
}

function handleEvent(data) {
  if (data.type === 'command') {
    data = {
      id: data.id,
      time: data.time,
      agent: data.agent,
      command: { command: data.command, args: data.args, kw: data.kw },
      progress_current: 0,
      progress_total: undefined,
      status: 0,
      output: ''
    }
    commands.value.unshift(data)
  } else if (data.type === 'command_progress') {
    const command = commands.value.find((command) => command.id === data.id)
    if (command) {
      command.progress_current = data.progress_current
      command.progress_total = data.progress_total
      command.output = data.message
    } else {
      data.agent = 'Unknown'
      data.command = { command: 'Unknown', args: 'Unknown', kw: 'Unknown' }
      data.status = 0
      data.output = data.message
      commands.value.unshift(data)
    }
  } else if (data.type === 'command_result') {
    const command = commands.value.find((command) => command.id === data.id)
    if (command) {
      command.status = data.status
      command.output = data.output
    } else {
      data.agent = 'Unknown'
      data.command = { command: 'Unknown', args: 'Unknown', kw: 'Unknown' }
      data.progress_current = 0
      data.progress_total = undefined
      commands.value.unshift(data)
    }
  }
}

function formatDate(date) {
  date = date * 1000
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

function getStatusText(status) {
  if (status === 0) {
    return 'Pending'
  } else if (status === 1) {
    return 'Succeeded'
  } else if (status === 2) {
    return 'Failed'
  } else if (status === 3) {
    return 'Canceled'
  } else {
    return status
  }
}

function getProgress(command) {
  if (command.progress_total == undefined) {
    return 0
  }
  if (command.progress_total == 0) {
    return 100
  }
  return (command.progress_current / command.progress_total) * 100
}

function getBackground(command) {
  if (command.status === 0) {
    // Pending
    return 'var(--color-blue)'
  } else if (command.status === 1) {
    // Success
    return 'var(--color-green)'
  } else if (command.status === 2) {
    // Failed
    return 'var(--color-red)'
  } else if (command.status === 3) {
    // Canceled
    return 'var(--color-orange)'
  } else {
    return 'var(--color-background-input)'
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
    handleEvent(data)
  }
  ws.value.onerror = (event) => {
    console.log(event)
    busy.close()
    toast.new('Failed to connect to WebSocket.', 'error')
  }
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
  document.getElementById('connection_spinner').classList.remove('hidden')
  document.getElementById('connection_status').textContent = '\u231B'
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
  <div id="log-view" class="gapped left-aligned column">
    <h1 class="gapped row">
      Commands
      <div id="connection_status" style="color: var(--color-gray)"></div>
      <div class="spinner hidden" id="connection_spinner"></div>
    </h1>
    <div class="gapped centered row">
      <button type="button" @click="refresh">Refresh</button>
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
    </div>
    <table class="full-width">
      <thead>
        <tr>
          <th style="width: 30%; min-width: 20em">Command</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="command in filteredCommands" :key="command.id">
          <td>
            <div class="column">
              <span>Command ID: {{ command.id }}</span>
              <span>Time: {{ formatDate(command.time) }}</span>
              <span>Agent: {{ command.agent }}</span>
              <span>Command: {{ command.command.command }}</span>
              <span>Arguments: {{ command.command.args }}</span>
              <span>Parameters: {{ command.command.kw }}</span>
            </div>
          </td>
          <td>
            <div class="centered column">
              <span>
                {{ getStatusText(command.status) }} {{ command.progress_current }} /
                {{ command.progress_total }}
              </span>
              <ProgressBar :progress="getProgress(command)" :background="getBackground(command)" />
              <pre
                class="full-width command-output"
                v-if="command.status !== 0"
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
                >{{ command.output }}</pre
              >
              <span v-else>{{ command.output }}</span>
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
tbody tr {
  animation: fade-in 0.5s;
}
@keyframes fade-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
</style>
