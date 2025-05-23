<script setup lang="ts">
import dayjs from 'dayjs'
import DashboardPage from '@/components/DashboardPage.vue'

const logs = ref<any[]>([])
const messages = useMessages()
const connection_status = ref('')

const ws = ref<WebSocket | null>(null)

const numRetries = ref(0)

function clear() {
  logs.value = []
}

function formatDate(date: number) {
  date = date * 1000
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

function getStyle(log: any) {
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
  numRetries.value++
  if (numRetries.value >= 10) {
    if (
      confirm(
        'Retried WebSocket connection 10 times. Continue?\n' +
          'If not, you will have to refresh the page before you can get real-time updates.'
      )
    ) {
      numRetries.value = 0
      connect()
    } else {
      messages.addMessage({
        text: 'Failed to connect to WebSocket. Please check your network connection and refresh the page.',
        type: 'error',
        id: 'commands.connect_failed',
        timeout: 0
      })
      connection_status.value = '\u2716' // X
    }
    return
  }
  connection_status.value = '\u231B' // hourglass
  const busy = messages.addMessage({ text: 'Connecting to WebSocket...', id: 'events.ws' })
  ws.value = new WebSocket('/api/v1/events/ws')
  ws.value.onopen = () => {
    messages.removeMessage(busy)
    connection_status.value = '\u2714' // check mark
    numRetries.value = 0
  }
  ws.value.onmessage = (event) => {
    const data = JSON.parse(event.data)
    logs.value.unshift(data)
  }
  ws.value.onerror = (event) => {
    messages.removeMessage(busy)
    messages.addMessage({ text: 'Failed to connect to WebSocket.', type: 'error', id: 'events.ws' })
  }
  ws.value.onclose = () => {
    console.log('WebSocket closed')
    connection_status.value = '\u2716' // X
    ws.value = null
    setTimeout(() => {
      connect()
    }, 2000)
  }
}

onMounted(() => {
  numRetries.value = 0
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
  <DashboardPage title="Events">
    <template #after_title>
      <div>{{ connection_status }}</div>
    </template>
    <v-card>
      <v-card-text>
        <div class="d-flex flex-row">
          <v-btn type="button" @click="clear">Clear</v-btn>
        </div>
        <v-table density="compact" class="table-layout-fixed">
          <thead>
            <tr>
              <th style="width: 15%">Time</th>
              <th style="width: 10%">Agent</th>
              <th style="width: 15%">Event</th>
              <th style="width: 60%">Data</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="log in logs" :key="log.id" :style="getStyle(log)">
              <td>{{ formatDate(log.time) }}</td>
              <td>{{ log.agent || '(N/A)' }}</td>
              <td>{{ log.type }}</td>
              <td>
                <pre
                  v-text="JSON.stringify(log)"
                  class="text-wrap ma-1 pa-1 bg-surface-light rounded"
                />
              </td>
            </tr>
          </tbody>
        </v-table>
      </v-card-text>
    </v-card>
  </DashboardPage>
</template>
<style>
.table-layout-fixed table {
  table-layout: fixed;
}
</style>
