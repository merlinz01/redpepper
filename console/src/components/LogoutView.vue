<script setup lang="ts">
import Fetch from '@/fetcher'
import useMessages from '@/stores/messages'
import useNotifications from '@/stores/notifications'

const router = useRouter()
const notifications = useNotifications()
const messages = useMessages()
const failed = ref(false)

function logout() {
  failed.value = false
  const busy = messages.addMessage({ text: 'Logging out...', timeout: 0 })
  Fetch('/api/v1/logout')
    .onError((error: any) => {
      console.log(error)
      notifications.post({ text: 'Failed to log out: ' + error, type: 'error' })
      failed.value = true
    })
    .onSuccess((data: any) => {
      if (data.success) {
        messages.addMessage({ text: 'Logged out.' })
        router.push('/login')
      } else {
        failed.value = true
        throw new Error(data.detail)
      }
    })
    .credentials('same-origin')
    .post()
    .finally(() => {
      messages.removeMessage(busy)
    })
}

onMounted(() => {
  logout()
})
</script>

<template>
  <div id="logout-view" class="padded gapped centered column">
    <h1 v-if="failed">Logout failed.</h1>
    <button type="button" @click="logout" v-if="failed">Retry Logout</button>
    <h1 v-else>Logging out...</h1>
  </div>
</template>
