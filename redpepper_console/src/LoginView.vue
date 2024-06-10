<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Fetch from './fetcher'
import { useToast } from './toast'

const router = useRouter()
const toast = useToast()

onMounted(() => {
  document.getElementById('username').focus()
})

function submitLogin(event) {
  event.preventDefault()
  const busy = toast.new('Logging in...', 'info')
  Fetch('/api/v1/login')
    .onError((error) => {
      busy.close()
      console.log(error)
      toast.new('Failed to log in: ' + error, 'error')
    })
    .onSuccess((data) => {
      if (data.success) {
        busy.close()
        toast.new('Logged in successfully.', 'success', { timeout: 1000 })
        router.push('/totp')
      } else {
        throw new Error(data.detail)
      }
    })
    .credentials('same-origin')
    .post({
      username: event.target.username.value,
      password: event.target.password.value
    })
  event.target.password.value = ''
}
</script>

<template>
  <form id="login-view" @submit="submitLogin" class="gapped centered column">
    <h1>Log in to RedPepper</h1>
    <label for="username">Username</label>
    <input type="text" id="username" name="username" required placeholder="Username" />
    <label for="password">Password</label>
    <input type="password" id="password" name="password" required placeholder="Password" />
    <button type="submit">Login</button>
  </form>
</template>
