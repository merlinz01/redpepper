<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
const router = useRouter()

const failed = ref(false)

const logout = () => {
  failed.value = false
  fetch('/api/v1/logout', {
    method: 'POST',
    credentials: 'same-origin'
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        router.push('/login')
      } else {
        alert('Logout failed!')
        failed.value = true
      }
    })
    .catch((error) => {
      alert('Logout failed: ' + error)
      console.log(error)
      failed.value = true
    })
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
