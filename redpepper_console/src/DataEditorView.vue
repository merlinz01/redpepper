<script setup>
import { ref, onMounted } from 'vue'
import TreeComponent from './tree/TreeComponent.vue'
import { useRouter } from 'vue-router'
import Fetch from './fetcher'
import CommandView from './CommandView.vue'
import { Alert, Prompt, Confirm } from './dialogs'

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
      Alert(error).title('Failed to fetch file tree').showModal()
    })
    .onSuccess((data) => {
      if (data === undefined) {
        return
      }
      treeData.value = data.tree
    })
    .credentials('same-origin')
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
      Alert(error).title('Failed to open file').showModal()
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
    .credentials('same-origin')
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
      Alert(error).title('Failed to save file').showModal()
    })
    .onSuccess((data) => {
      if (data.success) {
        Alert('File saved successfully').title('Success').showModal()
        editor.value.session.getUndoManager().markClean()
        isChanged.value = false
      } else {
        throw new Error(data.detail)
      }
    })
    .credentials('same-origin')
    .post({ data: content })
}

function newFile() {
  Prompt('Enter the name of the new file')
    .title('New file')
    .onSubmit((filename) => {
      Fetch('/api/v1/config/file')
        .query('path', filename)
        .query('isdir', false)
        .onStatus(401, () => {
          console.log('Unauthorized. Redirecting to login page.')
          router.push('/login')
        })
        .onError((error) => {
          Alert(error).title('Failed to create file').showModal()
        })
        .onSuccess((data) => {
          if (data.success) {
            refreshTree()
            Alert('File created successfully').title('Success').showModal()
          } else {
            throw new Error(data.detail)
          }
        })
        .credentials('same-origin')
        .put()
    })
    .showModal()
}

function newFolder() {
  Prompt('Enter the name of the new folder')
    .title('New folder')
    .onSubmit((foldername) => {
      Fetch('/api/v1/config/file')
        .query('path', foldername)
        .query('isdir', true)
        .onStatus(401, () => {
          console.log('Unauthorized. Redirecting to login page.')
          router.push('/login')
        })
        .onError((error) => {
          Alert(error).title('Failed to create folder').showModal()
        })
        .onSuccess((data) => {
          if (data.success) {
            refreshTree()
            Alert('Folder created successfully').title('Success').showModal()
          } else {
            throw new Error(data.detail)
          }
        })
        .credentials('same-origin')
        .put()
    })
    .showModal()
}

function deleteFileOrFolder() {
  if (selectedPath.value.length === 0) {
    return
  }
  Confirm('Are you sure you want to delete ' + selectedPath.value.join('/') + '?')
    .onConfirm(() => {
      Fetch('/api/v1/config/file')
        .query('path', selectedPath.value.join('/'))
        .onStatus(401, () => {
          console.log('Unauthorized. Redirecting to login page.')
          router.push('/login')
        })
        .onError((error) => {
          Alert(error).title('Failed to delete file or folder').showModal()
        })
        .onSuccess((data) => {
          if (data.success) {
            refreshTree()
            Alert('File or folder deleted successfully').title('Success').showModal()
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
        .credentials('same-origin')
        .delete()
    })
    .showModal()
}

function renameFileOrFolder() {
  if (selectedPath.value.length === 0) {
    return
  }
  Prompt('Enter the new name for ' + selectedPath.value.join('/'))
    .title('Rename file or folder')
    .onSubmit((newname) => {
      Fetch('/api/v1/config/file')
        .query('path', selectedPath.value.join('/'))
        .onStatus(401, () => {
          console.log('Unauthorized. Redirecting to login page.')
          router.push('/login')
        })
        .onError((error) => {
          Alert(error).title('Failed to rename file or folder').showModal()
        })
        .onSuccess((data) => {
          if (data.success) {
            refreshTree()
            Alert('File or folder renamed successfully').title('Success').showModal()
            if (selectedPath.value.join('/') === currentFile.value) {
              currentFile.value = newname
              selectedPath.value = []
            }
          } else {
            throw new Error(data.detail)
          }
        })
        .credentials('same-origin')
        .patch({ path: newname })
    })
    .showModal()
}
</script>

<template>
  <CommandView />
  <div id="data-editor-view" class="full-height column">
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
        <div id="data-editor" class="full-height bordered rounded large-font"></div>
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
}
#data-editor-container {
  margin: 0.5rem;
  width: 75%;
}
</style>
