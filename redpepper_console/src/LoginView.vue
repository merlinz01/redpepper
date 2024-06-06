<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Fetch from './fetcher'
import { Alert } from './dialogs'

const router = useRouter()

onMounted(() => {
  document.getElementById('username').focus()
})

function submitLogin(event) {
  event.preventDefault()
  Fetch('/api/v1/login')
    .onError((error) => {
      console.log(error)
      Alert(error).title('Failed to log in').showModal()
    })
    .onStatus(401, () => {
      console.log('Unauthorized. Redirecting to login page.')
      router.push('/login')
    })
    .onSuccess((data) => {
      if (data.success) {
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
