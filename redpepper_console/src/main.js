import './assets/main.css'

import { createApp } from 'vue'
import { createRouter, createWebHashHistory } from 'vue-router'

import App from './App.vue'

import HomeView from './HomeView.vue'
import LoginView from './LoginView.vue'
import TOTPView from './TOTPView.vue'
import LogoutView from './LogoutView.vue'
import AgentsView from './AgentsView.vue'
import EventsView from './EventsView.vue'
import DataEditorView from './DataEditorView.vue'
import HelpView from './HelpView.vue'

const routes = [
  { path: '/', component: HomeView },
  { path: '/login', component: LoginView },
  { path: '/totp', component: TOTPView },
  { path: '/logout', component: LogoutView },
  { path: '/agents', component: AgentsView },
  { path: '/events', component: EventsView },
  { path: '/data', component: DataEditorView },
  { path: '/help', component: HelpView }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})
createApp(App).use(router).mount('body')
