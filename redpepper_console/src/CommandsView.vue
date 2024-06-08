<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import dayjs from 'dayjs'
import CommandView from './CommandView.vue'
import Fetch from './fetcher'
import { Alert } from './dialogs'
import ProgressBar from './ProgressBar.vue'

const router = useRouter()

const commands = ref([
  {
    id: '20240402144069002',
    agent: 'agent1',
    command: {
      command: 'git.UpToDate',
      args: [],
      kw: {}
    },
    status: 1,
    changed: 1,
    time: 1629780000,
    progress_current: 1,
    progress_total: 3,
    output: 'Operation completed successfully'
  },
  {
    id: '20240402144069003',
    agent: 'agent2',
    command: {
      command: 'git.UpToDate',
      args: [],
      kw: {}
    },
    status: 1,
    changed: 1,
    time: 1629780000,
    progress_current: 2,
    progress_total: 3,
    output: 'Operation completed successfully'
  },
  {
    id: '20240402144069004',
    agent: 'agent3',
    command: {
      command: 'git.UpToDate',
      args: [],
      kw: {}
    },
    status: 2,
    changed: 1,
    time: 1629780000,
    progress_current: 3,
    progress_total: 3,
    output: 'Operation completed successfully'
  }
])

const filterAgent = ref('')
const filteredCommands = computed(() => {
  return commands.value.filter((command) => {
    if (filterAgent.value && command.agent && command.agent != filterAgent.value) {
      return false
    }
    return true
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
  Fetch('/api/v1/commands/last')
    .query('max', 100)
    .onError((error) => {
      Alert(error).title('Failed to fetch events').showModal()
    })
    .onStatus(401, () => {
      console.log('Unauthorized. Redirecting to login page.')
      router.push('/login')
    })
    .onSuccess((data) => {
      commands.value = data.events
    })
    .credentials('same-origin')
    .get()
}

function formatDate(date) {
  date = date * 1000
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

// function connect() {
//   if (ws.value) {
//     ws.value.close()
//   }
//   numRetries.value++
//   if (numRetries.value >= 10) {
//     Confirm('If not, you will have to refresh the page before you can get real-time updates.')
//       .title('Retried WebSocket connection 10 times. Continue?')
//       .onConfirm(() => {
//         numRetries.value = 0
//         connect()
//       })
//       .onCancel(() => {
//         document.getElementById('connection_spinner').classList.add('hidden')
//       })
//       .showModal()
//     return
//   }
//   console.log('Connecting to WebSocket...')
//   ws.value = new WebSocket('/api/v1/events/ws')
//   ws.value.onmessage = (event) => {
//     const data = JSON.parse(event.data)
//     logs.value.unshift(data)
//   }
//   ws.value.onclose = () => {
//     console.log('WebSocket closed')
//     document.getElementById('connection_spinner').classList.remove('hidden')
//     document.getElementById('connection_status').textContent = '\u2716'
//     ws.value = null
//     setTimeout(() => {
//       connect()
//     }, 1000)
//   }
//   ws.value.onopen = () => {
//     console.log('WebSocket connected')
//     document.getElementById('connection_spinner').classList.add('hidden')
//     document.getElementById('connection_status').textContent = '\u2714'
//     numRetries.value = 0
//   }
// }

onMounted(() => {
  numRetries.value = 0
  // document.getElementById('connection_spinner').classList.remove('hidden')
  // document.getElementById('connection_status').textContent = '\u231B'
  // document.getElementById('since').value = dayjs().subtract(1, 'day').format('YYYY-MM-DDTHH:mm:ss')
  //connect()
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
          <th>Command</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="command in filteredCommands" :key="command.command_id">
          <td>
            <p>Command ID: {{ command.command_id }}</p>
            <p>Agent: {{ command.agent }}</p>
            <p>Time: {{ formatDate(command.time) }}</p>
            <p>Arguments: {{ command.args }}</p>
            <p>Parameters: {{ command.kw }}</p>
          </td>
          <td>
            <div class="centered column">
              <p>{{ command.progress_current }} / {{ command.progress_total }}</p>
              <ProgressBar :progress="(command.progress_current / command.progress_total) * 100" />
              <pre
                class="full-width command-output"
                v-if="command.status !== 0 && command.status !== 1"
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
  margin-top: 0.25em;
}
</style>
