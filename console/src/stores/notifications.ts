import { defineStore } from 'pinia'

export interface Message {
  text: string
  timeout?: number
  type?: 'success' | 'error' | 'warning' | 'info'
  id?: string
}

const useNotifications = defineStore('statusMessages', () => {
  const notifications = ref<Message[]>([])
  function post(message: Message): string {
    if (!message.id) {
      message.id = Math.random().toString(36)
    } else {
      remove(message.id)
    }
    if (message.timeout === undefined) message.timeout = 10000
    notifications.value.push(message)
    if (message.timeout !== 0) {
      setTimeout(() => {
        remove(message.id!)
      }, message.timeout)
    }
    return message.id
  }
  function remove(messageId: string) {
    notifications.value = notifications.value.filter((m) => m.id !== messageId)
  }
  return {
    notifications,
    post
  }
})

export default useNotifications
