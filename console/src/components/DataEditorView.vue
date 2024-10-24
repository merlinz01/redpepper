<script setup lang="ts">
import TreeComponent from '@/components/tree/TreeComponent.vue'
import { Prompt, Confirm } from '@/dialogs'
import DashboardPage from '@/components/DashboardPage.vue'

import ace from 'ace-builds'
ace.config.set('basePath', '/assets/ace_modules')
import ace_languages from '@/components/ace/languages'
import { lightThemes, darkThemes } from '@/components/ace/themes'
// import { VAceEditor } from 'vue3-ace-editor'
// import type { VAceEditorInstance } from 'vue3-ace-editor'
import AceEditor from '@/components/ace/AceEditor.vue'

const treeData = ref([])
const selectedPath = ref([])
const currentFile = ref('')
const currentFileContent = ref('')
const isSaved = ref(true)
const selectedLanguage = ref('plain_text')
const selectedTheme = ref(localStorage.getItem('aceEditorTheme') || 'chrome')
const editor = ref<typeof AceEditor>()
// const editor = ref<any>()
// const editor = ref<VAceEditorInstance>()
const editorReadonly = ref(true)
const router = useRouter()
const notifications = useNotifications()
const messages = useMessages()

onMounted(() => {
  refreshTree()
})

watchEffect(() => {
  localStorage.setItem('aceEditorTheme', selectedTheme.value)
})

function treeItemSelected(element: any, path: any, isParent: any) {
  selectedPath.value = path
  if (!isParent) {
    openFile(path)
  }
}

function refreshTree() {
  const busy = messages.addMessage({ text: 'Refreshing file tree...', timeout: 0 })
  axios
    .get('/api/v1/config/tree')
    .then((response) => {
      treeData.value = response!.data.tree
    })
    .catch((error) => {
      if (error.response?.status == 401) {
        notifications.post({ text: 'Please log in', type: 'error' })
        router.push('/login')
        return
      }
      notifications.post({
        text: 'Failed to fetch file tree: ' + error,
        type: 'error',
        id: 'data_editor.tree_error'
      })
    })
    .finally(() => {
      messages.removeMessage(busy)
    })
}

function openFile(path: any) {
  if (!path || path.length === 0) {
    return
  }
  const busy = messages.addMessage({ text: 'Opening file...', timeout: 0 })
  axios
    .get('/api/v1/config/file', { params: { path: path.join('/') } })
    .then((response) => {
      if (!response!.data.success) {
        throw new Error(response!.data.detail)
      }
      let thislang = ''
      const filename = path[path.length - 1].toLowerCase()
      for (let lang of ace_languages) {
        if (lang.filenames && lang.filenames.includes(filename)) {
          thislang = lang.id
          break
        }
      }
      if (thislang == '') {
        const ext = filename.split('.').pop()
        for (let lang of ace_languages) {
          if (lang.ext && lang.ext.includes(ext)) {
            thislang = lang.id
            break
          }
        }
      }
      if (thislang == '') {
        thislang = 'plain_text'
      }
      selectedLanguage.value = thislang
      currentFileContent.value = response!.data.content
      editor.value!.setSaved()
      editorReadonly.value = false
      currentFile.value = path.join('/')
    })
    .catch((error) => {
      if (error.response?.status == 401) {
        notifications.post({ text: 'Please log in', type: 'error' })
        router.push('/login')
        return
      }
      notifications.post({
        text: 'Failed to open file: ' + error,
        type: 'error',
        id: 'data_editor.open_error'
      })
    })
    .finally(() => {
      messages.removeMessage(busy)
    })
}

function saveFile() {
  if (currentFile.value === '') {
    return
  }
  const content = currentFileContent.value
  const busy = messages.addMessage({ text: 'Saving file...', timeout: 0 })
  axios
    .post('/api/v1/config/file', { data: content }, { params: { path: currentFile.value } })
    .then((response) => {
      if (response!.data.success) {
        messages.addMessage({
          text: 'File saved successfully: ' + currentFile.value,
          type: 'success'
        })
        editor.value!.setSaved()
      } else {
        throw new Error(response!.data.detail)
      }
    })
    .catch((error) => {
      if (error.response?.status == 401) {
        notifications.post({ text: 'Please log in', type: 'error' })
        router.push('/login')
        return
      }
      notifications.post({
        text: 'Failed to save file: ' + error,
        type: 'error',
        id: 'data_editor.save_error'
      })
    })
    .finally(() => {
      messages.removeMessage(busy)
    })
}

function newFile() {
  Prompt('Enter the name of the new file')
    .title('New file')
    .initialValue(selectedPath.value.join('/') + '/')
    .onSubmit((filename: any) => {
      const busy = messages.addMessage({ text: 'Saving file...', timeout: 0 })
      axios
        .put('/api/v1/config/file', undefined, { params: { path: filename, isdir: false } })
        .then((response) => {
          if (response!.data.success) {
            refreshTree()
            notifications.post({ text: 'File created successfully: ' + filename, type: 'success' })
          } else {
            throw new Error(response!.data.detail)
          }
        })
        .catch((error) => {
          if (error.response?.status == 401) {
            notifications.post({ text: 'Please log in', type: 'error' })
            router.push('/login')
            return
          }
          notifications.post({
            text: 'Failed to create file: ' + error,
            type: 'error',
            id: 'data_editor.newfile_error'
          })
        })
        .finally(() => {
          messages.removeMessage(busy)
        })
    })
    .showModal()
}

function newFolder() {
  Prompt('Enter the name of the new folder')
    .title('New folder')
    .initialValue(selectedPath.value.join('/') + '/')
    .onSubmit((foldername: any) => {
      const busy = messages.addMessage({ text: 'Creating folder...', timeout: 0 })
      axios
        .put('/api/v1/config/file', undefined, { params: { path: foldername, isdir: true } })
        .then((response) => {
          if (response!.data.success) {
            refreshTree()
            notifications.post({
              text: 'Folder created successfully: ' + foldername,
              type: 'success'
            })
          } else {
            throw new Error(response!.data.detail)
          }
        })
        .catch((error) => {
          if (error.response?.status == 401) {
            notifications.post({ text: 'Please log in', type: 'error' })
            router.push('/login')
            return
          }
          notifications.post({
            text: 'Failed to create folder: ' + error,
            type: 'error',
            id: 'data_editor.newfolder_error'
          })
        })
        .finally(() => {
          messages.removeMessage(busy)
        })
    })
    .showModal()
}

function deleteFileOrFolder() {
  if (selectedPath.value.length === 0) {
    return
  }
  Confirm('Are you sure you want to delete ' + selectedPath.value.join('/') + '?')
    .onConfirm(() => {
      const busy = messages.addMessage({ text: 'Deleting file or folder...', timeout: 0 })
      axios
        .delete('/api/v1/config/file', { params: { path: selectedPath.value.join('/') } })
        .then((response) => {
          if (response!.data.success) {
            refreshTree()
            notifications.post({
              text: 'File or folder deleted successfully: ' + selectedPath.value.join('/'),
              type: 'success'
            })
            if (selectedPath.value.join('/') === currentFile.value) {
              currentFileContent.value = 'Select a file to edit its content.'
              editorReadonly.value = true
              currentFile.value = ''
              selectedPath.value = []
            }
          } else {
            throw new Error(response!.data.detail)
          }
        })
        .catch((error) => {
          if (error.response?.status == 401) {
            notifications.post({ text: 'Please log in', type: 'error' })
            router.push('/login')
            return
          }
          notifications.post({
            text: 'Failed to delete file or folder: ' + error,
            type: 'error',
            id: 'data_editor.delete_error'
          })
        })
        .finally(() => {
          messages.removeMessage(busy)
        })
    })
    .showModal()
}

function renameFileOrFolder() {
  if (selectedPath.value.length === 0) {
    return
  }
  const oldPath = selectedPath.value.join('/')
  Prompt('Enter the new name for ' + oldPath)
    .title('Rename file or folder')
    .initialValue(oldPath)
    .onSubmit((newPath: any) => {
      const busy = messages.addMessage({ text: 'Renaming file or folder...', timeout: 0 })
      axios
        .patch('/api/v1/config/file', { path: newPath }, { params: { path: oldPath } })
        .then((response) => {
          if (response!.data.success) {
            refreshTree()
            notifications.post({
              text: 'File or folder renamed successfully: ' + oldPath + ' -> ' + newPath,
              type: 'success'
            })
            if (oldPath === currentFile.value) {
              currentFile.value = newPath
              selectedPath.value = []
            }
          } else {
            throw new Error(response!.data.detail)
          }
        })
        .catch((error) => {
          if (error.response?.status == 401) {
            notifications.post({ text: 'Please log in', type: 'error' })
            router.push('/login')
            return
          }
          notifications.post({
            text: 'Failed to rename file or folder: ' + error,
            type: 'error',
            id: 'data_editor.rename_error'
          })
        })
        .finally(() => {
          messages.removeMessage(busy)
        })
    })
    .showModal()
}
</script>

<template>
  <DashboardPage title="Data Editor" class="full-height column">
    <div>
      <div class="d-flex ga-1 align-center">
        <v-btn @click="refreshTree">Refresh</v-btn>
        <v-btn @click="newFile">+File</v-btn>
        <v-btn @click="newFolder">+Folder</v-btn>
        <v-btn
          @click="deleteFileOrFolder"
          v-show="selectedPath.length"
          style="color: var(--color-red)"
        >
          Delete
        </v-btn>
        <v-btn @click="renameFileOrFolder" v-show="selectedPath.length">Rename</v-btn>
        <v-btn
          @click="saveFile"
          v-show="!isSaved && currentFile !== ''"
          style="color: var(--color-green)"
        >
          Save
        </v-btn>
        <span v-show="currentFile !== '' && isSaved">&#10004; No changes</span>
      </div>
    </div>
    <div class="w-100 h-100 d-flex">
      <TreeComponent
        :model="treeData"
        id="file-tree"
        @item-selected="treeItemSelected"
        style="flex-grow: 0; overflow: hidden"
        class="flex-grow-0"
      />
      <div class="w-100 d-flex flex-column" id="data-editor-container">
        <span class="text-center">{{ currentFile }}</span>
        <AceEditor
          class="w-100 h-100 border rounded"
          style="font-size: 1.1rem; font-family: 'Courier New', Courier, monospace"
          v-model="currentFileContent"
          :mode="selectedLanguage"
          :theme="selectedTheme"
          :readonly="editorReadonly"
          v-model:saved="isSaved"
          ref="editor"
        />
        <div class="ga-1 align-center justify-center pa-1 d-flex">
          <v-select
            v-model="selectedLanguage"
            :items="ace_languages"
            item-title="name"
            item-value="id"
            density="compact"
            title="Select language"
            hide-details
          />
          <v-select
            v-model="selectedTheme"
            :items="[
              {
                props: { disabled: true, class: 'text-center', density: 'compact' },
                name: 'Light themes'
              },
              ...lightThemes,
              {
                props: { disabled: true, class: 'text-center', density: 'compact' },
                name: 'Dark themes'
              },
              ...darkThemes
            ]"
            item-title="name"
            item-value="id"
            item-props="props"
            density="compact"
            title="Select color theme"
            hide-details
          />
          <span class="pa-2"
            >Powered by <a href="https://ace.c9.io/" target="_blank">Ace Editor</a></span
          >
        </div>
      </div>
    </div>
  </DashboardPage>
</template>

<style scoped>
#file-tree {
  margin: 0.5rem 0;
  width: 25%;
}
#data-editor-container {
  margin: 0.5rem;
  width: 75%;
}
</style>
