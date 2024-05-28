<script setup>
import { ref, onMounted } from 'vue'
import TreeComponent from './tree/TreeComponent.vue'
import { useRouter } from 'vue-router'
import Fetch from './fetcher'

import ace from 'ace-builds'
ace.config.set('basePath', '/assets/ace_modules')
import ace_languages from './languages'
import { lightThemes, darkThemes } from './themes'

const editor = ref(null)
const treeData = ref([])
const selectedPath = ref([])
const currentFile = ref('')
const isChanged = ref(true)
const selectedLanguage = ref('plain_text')
const selectedTheme = ref('chrome')

const router = useRouter()

onMounted(() => {
  refreshTree()
  editor.value = ace.edit('data-editor', {
    theme: 'ace/theme/' + selectedTheme.value,
    mode: 'ace/mode/' + selectedLanguage.value,
    readOnly: true
  })
  editor.value.on('input', () => {
    isChanged.value = !editor.value.session.getUndoManager().isClean()
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
  Fetch('/api/v1/config/tree')
    .onStatus(401, () => {
      console.log('Unauthorized. Redirecting to login page.')
      router.push('/login')
    })
    .onError((error) => {
      alert('Error retrieving file tree:\n' + error)
    })
    .onSuccess((data) => {
      if (data === undefined) {
        return
      }
      treeData.value = data.tree
    })
    .credentials('include')
    .get()
}

function openFile(path) {
  if (!path || path.length === 0) {
    return
  }
  Fetch('/api/v1/config/file')
    .query('path', path.join('/'))
    .onStatus(401, () => {
      console.log('Unauthorized. Redirecting to login page.')
      router.push('/login')
    })
    .onError((error) => {
      alert('Error retrieving file content:\n' + error)
    })
    .onSuccess((data) => {
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
      editor.value.session.setValue(data.content)
      editor.value.setReadOnly(false)
      currentFile.value = path.join('/')
      return data.data
    })
    .credentials('include')
    .get()
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
  Fetch('/api/v1/config/file')
    .query('path', selectedPath.value.join('/'))
    .onStatus(401, () => {
      console.log('Unauthorized. Redirecting to login page.')
      router.push('/login')
    })
    .onError((error) => {
      alert('Error saving file:\n' + error)
    })
    .onSuccess((data) => {
      if (data.success) {
        alert('File saved successfully')
        editor.value.session.getUndoManager().markClean()
        isChanged.value = false
      } else {
        throw new Error(data.detail)
      }
    })
    .credentials('include')
    .post({ data: content })
}

function newFile() {
  const filename = prompt('Enter the name of the new file')
  if (!filename) {
    return
  }
  Fetch('/api/v1/config/file')
    .query('path', filename)
    .query('isdir', false)
    .onStatus(401, () => {
      console.log('Unauthorized. Redirecting to login page.')
      router.push('/login')
    })
    .onError((error) => {
      alert('Error creating file:\n' + error)
    })
    .onSuccess((data) => {
      if (data.success) {
        refreshTree()
        alert('File created successfully')
      } else {
        throw new Error(data.detail)
      }
    })
    .credentials('include')
    .put()
}

function newFolder() {
  const foldername = prompt('Enter the name of the new folder')
  if (!foldername) {
    return
  }
  Fetch('/api/v1/config/file')
    .query('path', foldername)
    .query('isdir', true)
    .onStatus(401, () => {
      console.log('Unauthorized. Redirecting to login page.')
      router.push('/login')
    })
    .onError((error) => {
      alert('Error creating folder:\n' + error)
    })
    .onSuccess((data) => {
      if (data.success) {
        refreshTree()
        alert('Folder created successfully')
      } else {
        throw new Error(data.detail)
      }
    })
    .credentials('include')
    .put()
}

function deleteFileOrFolder() {
  if (selectedPath.value.length === 0) {
    return
  }
  if (!confirm('Are you sure you want to delete ' + selectedPath.value.join('/') + '?')) {
    return
  }
  Fetch('/api/v1/config/file')
    .query('path', selectedPath.value.join('/'))
    .onStatus(401, () => {
      console.log('Unauthorized. Redirecting to login page.')
      router.push('/login')
    })
    .onError((error) => {
      alert('Error deleting file or folder:\n' + error)
    })
    .onSuccess((data) => {
      if (data.success) {
        refreshTree()
        alert('File or folder deleted successfully!')
        if (selectedPath.value.join('/') === currentFile.value) {
          editor.value.session.setValue('Select a file to edit its content.')
          editor.value.setReadOnly(true)
          currentFile.value = ''
          selectedPath.value = []
        }
      } else {
        throw new Error(data.detail)
      }
    })
    .credentials('include')
    .delete()
}

function renameFileOrFolder() {
  if (selectedPath.value.length === 0) {
    return
  }
  const newname = prompt('Enter the new name for ' + selectedPath.value.join('/'))
  if (!newname) {
    return
  }
  Fetch('/api/v1/config/file')
    .query('path', selectedPath.value.join('/'))
    .onStatus(401, () => {
      console.log('Unauthorized. Redirecting to login page.')
      router.push('/login')
    })
    .onError((error) => {
      alert('Error renaming file or folder:\n' + error)
    })
    .onSuccess((data) => {
      if (data.success) {
        refreshTree()
        alert('File or folder renamed successfully!')
        if (selectedPath.value.join('/') === currentFile.value) {
          currentFile.value = newname
          selectedPath.value = []
        }
      } else {
        throw new Error(data.detail)
      }
    })
    .credentials('include')
    .patch({ path: newname })
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
        <span v-show="currentFile !== '' && !isChanged">&#10004; No changes</span>
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
