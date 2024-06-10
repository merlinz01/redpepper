<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import Fetch from './fetcher'
import { useToast } from './toast'

const router = useRouter()
const toast = useToast()

const failed = ref(false)

function logout() {
  failed.value = false
  const busy = toast.new('Logging out...', 'info')
  Fetch('/api/v1/logout')
    .onError((error) => {
      console.log(error)
      busy.close()
      toast.new('Failed to log out: ' + error, 'error')
      failed.value = true
    })
    .onSuccess((data) => {
      if (data.success) {
        busy.close()
        toast.new('Logged out.', 'success', { timeout: 1000 })
        router.push('/login')
      } else {
        failed.value = true
        throw new Error(data.detail)
      }
    })
    .credentials('same-origin')
    .post()
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
