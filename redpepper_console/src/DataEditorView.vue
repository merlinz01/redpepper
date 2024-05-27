<script setup>
import { ref, onMounted } from 'vue'
import TreeComponent from './tree/TreeComponent.vue'

import ace from 'ace-builds'
ace.config.set('basePath', 'node_modules/ace-builds/src-noconflict')
import ace_languages from './languages'
import { lightThemes, darkThemes } from './themes'

const editor = ref(null)
const treeData = ref([])
const selectedPath = ref([])
const currentFile = ref('')
const isChanged = ref(true)
const selectedLanguage = ref('plain_text')
const selectedTheme = ref('chrome')

onMounted(() => {
  refreshTree()
  editor.value = ace.edit('data-editor', {
    theme: 'ace/theme/' + selectedTheme.value,
    mode: 'ace/mode/' + selectedLanguage.value,
    readOnly: true
  })
  editor.value.session.setValue('Select a file to edit its content.')
})

function treeItemSelected(element, path, isParent) {
  selectedPath.value = path
  if (!isParent) {
    openFile(path)
  }
}

function refreshTree() {
  fetch('https://localhost:8080/api/v1/config/tree', {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json'
    }
  })
    .then((response) => response.json())
    .then((data) => {
      treeData.value = data.tree
    })
    .catch((error) => {
      alert('Error retrieving file tree: ', error)
    })
}

function getFileContent(path) {
  return fetch('https://localhost:8080/api/v1/config/file?path=' + path.join('/'), {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json'
    }
  })
    .then((response) => response.json())
    .then((data) => {
      return { success: true, content: data.data }
    })
    .catch((error) => {
      alert('Error retrieving file content: ', error)
      return { success: false, content: '' }
    })
}
async function openFile(path) {
  if (!path || path.length === 0) {
    return
  }
  const content = await getFileContent(path)
  if (!content.success) {
    return
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
  changeLanguage()
  editor.value.session.setValue(content.content)
  editor.value.setReadOnly(false)
  currentFile.value = path.join('/')
}

function changeLanguage() {
  const language = selectedLanguage.value
  editor.value.session.setMode('ace/mode/' + language)
}

function changeTheme() {
  const theme = selectedTheme.value
  editor.value.setTheme('ace/theme/' + theme)
}

function saveFile() {
  if (selectedPath.value.length === 0) {
    return
  }
  const content = editor.value.getValue()
  fetch('https://localhost:8080/api/v1/config/file?path=' + selectedPath.value.join('/'), {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ data: content })
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        alert('File saved successfully')
      } else {
        alert('Error saving file: ', data.detail)
      }
    })
    .catch((error) => {
      alert('Error saving file: ', error)
    })
}

function newFile() {
  const filename = prompt('Enter the name of the new file')
  if (!filename) {
    return
  }
  fetch('https://localhost:8080/api/v1/config/file?path=' + filename, {
    method: 'PUT',
    credentials: 'include'
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        alert('File created successfully')
        refreshTree()
      } else {
        alert('Error creating file: ', data.detail)
      }
    })
    .catch((error) => {
      alert('Error creating file: ', error)
    })
}

function newFolder() {
  const foldername = prompt('Enter the name of the new folder')
  if (!foldername) {
    return
  }
  fetch('https://localhost:8080/api/v1/config/file?isdir=true&path=' + foldername, {
    method: 'PUT',
    credentials: 'include'
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        alert('Folder created successfully')
        refreshTree()
      } else {
        alert('Error creating folder: ', data.detail)
      }
    })
    .catch((error) => {
      alert('Error creating folder: ', error)
    })
}

function deleteFileOrFolder() {
  if (selectedPath.value.length === 0) {
    return
  }
  if (!confirm('Are you sure you want to delete ' + selectedPath.value.join('/') + '?')) {
    return
  }
  fetch('https://localhost:8080/api/v1/config/file?path=' + selectedPath.value.join('/'), {
    method: 'DELETE',
    credentials: 'include'
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        alert('File or folder deleted successfully!')
        refreshTree()
        if (selectedPath.value.join('/') === currentFile.value) {
          editor.value.session.setValue('Select a file to edit its content.')
          editor.value.setReadOnly(true)
          currentFile.value = ''
          selectedPath.value = []
        }
      } else {
        alert('Error deleting file/folder: ', data.detail)
      }
    })
    .catch((error) => {
      alert('Error deleting file/folder: ', error)
    })
}

function renameFileOrFolder() {
  if (selectedPath.value.length === 0) {
    return
  }
  const newname = prompt('Enter the new name for ' + selectedPath.value.join('/'))
  if (!newname) {
    return
  }
  fetch('https://localhost:8080/api/v1/config/file?path=' + selectedPath.value.join('/'), {
    method: 'PATCH',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ path: newname })
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        alert('File or folder renamed successfully!')
        refreshTree()
        if (selectedPath.value.join('/') === currentFile.value) {
          currentFile.value = newname
          selectedPath.value = []
        }
      } else {
        alert('Error renaming file/folder: ', data.detail)
      }
    })
    .catch((error) => {
      alert('Error renaming file/folder: ', error)
    })
}
</script>

<template>
  <div id="data-editor-view" class="full-height well-padded column">
    <h1>Data Editor</h1>
    <div>
      <div class="gapped centered row">
        <button @click="refreshTree">Refresh</button>
        <button @click="newFile">+File</button>
        <button @click="newFolder">+Folder</button>
        <button
          @click="deleteFileOrFolder"
          v-show="selectedPath.length"
          style="color: var(--color-red)"
        >
          Delete
        </button>
        <button @click="renameFileOrFolder" v-show="selectedPath.length">Rename</button>
        <button
          @click="saveFile"
          v-show="isChanged && currentFile !== ''"
          style="color: var(--color-green)"
        >
          Save
        </button>
      </div>
    </div>
    <div class="full-height full-width row">
      <TreeComponent id="file-tree" :model="treeData" @item-selected="treeItemSelected" class="" />
      <div class="full-height column" id="data-editor-container">
        <span class="text-centered">{{ currentFile }}</span>
        <div id="data-editor"></div>
        <div class="gapped centered justify-centered thinly-padded row">
          <span class="hide-on-text-overflow">Language:</span>
          <select v-model="selectedLanguage" @change="changeLanguage">
            <option v-for="lang in ace_languages" :value="lang.id" :key="lang.id">
              {{ lang.name }}
            </option>
          </select>
          <span class="hide-on-text-overflow">Theme:</span>
          <select v-model="selectedTheme" @change="changeTheme">
            <option disabled>--- Light ---</option>
            <option v-for="theme in lightThemes" :value="theme.id" :key="theme.id">
              {{ theme.name }}
            </option>
            <option disabled>--- Dark ---</option>
            <option v-for="theme in darkThemes" :value="theme.id" :key="theme.id">
              {{ theme.name }}
            </option>
          </select>
          <span class="hide-on-text-overflow small-font"
            >Powered by <a href="https://ace.c9.io/" target="_blank">Ace Editor</a></span
          >
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
#file-tree {
  margin: 0.5rem 0;
  width: 25%;
  border-radius: var(--border-radius);
  background-color: var(--color-background-input);
}
#data-editor-container {
  margin: 0.5rem;
  width: 75%;
}
#data-editor {
  height: 100%;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius);
  background-color: var(--color-background-input);
  font-size: large;
}
</style>
