
import { createApp } from 'vue'
import { createRouter, createWebHashHistory } from 'vue-router'
import { createPinia } from 'pinia'
import { createVuetify } from 'vuetify'

import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'

import App from '@/App.vue'

import HomeView from '@/components/HomeView.vue'
import LoginView from '@/components/LoginView.vue'
import TOTPView from '@/components/TOTPView.vue'
import LogoutView from '@/components/LogoutView.vue'
import AgentsView from '@/components/AgentsView.vue'
import EventsView from '@/components/EventsView.vue'
import CommandsView from '@/components/CommandsView.vue'
import DataEditorView from '@/components/DataEditorView.vue'
import HelpView from '@/components/HelpView.vue'

const routes = [
  { path: '/', component: HomeView },
  { path: '/login', component: LoginView },
  { path: '/totp', component: TOTPView },
  { path: '/logout', component: LogoutView },
  { path: '/agents', component: AgentsView },
  { path: '/events', component: EventsView },
  { path: '/commands', component: CommandsView },
  { path: '/data', component: DataEditorView },
  { path: '/help', component: HelpView }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

const vuetify = createVuetify({
  icons: {
    defaultSet: 'mdi'
  },
  theme: {
    themes: {
      light: {
        dark: false,
        colors: {
          primary: '#900000',
          secondary: '#80e000'
        }
      },
      dark: {
        dark: true,
        colors: {
          primary: '#a02020',
          secondary: '#80e000',
          error: '#d03030'
        }
      }
    }
  }
})

createApp(App).use(router).use(vuetify).use(createPinia()).mount('body')
