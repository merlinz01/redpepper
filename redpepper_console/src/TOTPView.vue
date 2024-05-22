<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
const router = useRouter()

onMounted(() => {
  document.getElementById('totp').focus()
})

const submitLogin = (event) => {
  event.preventDefault()
  fetch('https://localhost:8080/api/v1/verify_totp', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    credentials: 'include',
    body: JSON.stringify({
      totp: event.target.totp.value
    })
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        router.push('/agents')
      } else {
        alert('Verification failed!')
      }
    })
    .catch((error) => {
      alert('Verification failed: ' + error)
      console.log(error)
      router.push('/login')
    })
  event.target.totp.value = ''
}

const verify_totp_on_change = () => {
  // const totp = document.getElementById('totp').value
  // if (totp.length === 6) {
  //   document.getElementById('totp-view').submit()
  // }
}
</script>

<template>
  <form id="totp-view" @submit="submitLogin" class="padded gapped centered column">
    <h3>Enter TOTP</h3>
    <label for="username">Six-digit code from your authenticator app:</label>
    <input
      type="text"
      id="totp"
      name="totp"
      required
      placeholder="XXXXXXX"
      v-on:change="verify_totp_on_change"
    />
    <button type="submit">Verify</button>
    <button type="button" @click="router.push('/login')">Back</button>
  </form>
</template>
