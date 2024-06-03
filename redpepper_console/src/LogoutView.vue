<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import Fetch from './fetcher'

const router = useRouter()

const failed = ref(false)

function logout() {
  failed.value = false
  Fetch('/api/v1/logout')
    .onError((error) => {
      console.log(error)
      alert('Logout failed: ' + error)
      failed.value = true
    })
    .onSuccess((data) => {
      if (data.success) {
        router.push('/login')
      } else {
        alert('Logout failed!')
        failed.value = true
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
    <button type="button" @click="logout" v-if="failed">Retry Logout</button>
    <h1 v-else>Logging out...</h1>
  </div>
</template>
