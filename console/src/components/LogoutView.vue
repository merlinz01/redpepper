<script setup lang="ts">
const router = useRouter()
const notifications = useNotifications()
const messages = useMessages()
const failed = ref(false)
const user = useUser()

function logout() {
  failed.value = false
  const busy = messages.addMessage({ text: 'Logging out...', timeout: 0 })
  axios
    .post('/api/v1/logout')
    .then((response) => {
      if (response!.data.success) {
        messages.addMessage({ text: 'Logged out.' })
        user.user = null
        router.push({ name: 'home' })
      } else {
        failed.value = true
        throw new Error(response!.data.detail)
      }
    })
    .catch((error) => {
      notifications.post({ text: 'Failed to log out: ' + error, type: 'error' })
      failed.value = true
    })
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
