class _Fetch {
  constructor(url) {
    this.url = new URL(url)
    this.onerror = null
    this.onsuccess = null
    this.onstatuses = {}
    this.fetchparams = {
      method: 'GET',
      headers: {},
      credentials: 'none'
    }
  }

  onStatus(status, callback) {
    this.onstatuses[status] = callback
    return this
  }

  onError(callback) {
    this.onerror = callback
    return this
  }

  onSuccess(callback) {
    this.onsuccess = callback
    return this
  }

  get() {
    this.fetchparams.method = 'GET'
    return this.fetch()
  }

  post(data) {
    this.fetchparams.method = 'POST'
    if (data !== undefined) {
      this.body('application/json', JSON.stringify(data))
    }
    return this.fetch()
  }

  put(data) {
    this.fetchparams.method = 'PUT'
    if (data !== undefined) {
      this.body('application/json', JSON.stringify(data))
    }
    return this.fetch()
  }

  delete() {
    this.fetchparams.method = 'DELETE'
    return this.fetch()
  }

  patch(data) {
    this.fetchparams.method = 'PATCH'
    if (data !== undefined) {
      this.body('application/json', JSON.stringify(data))
    }
    return this.fetch()
  }

  header(key, value) {
    this.fetchparams.headers[key] = value
    return this
  }

  query(key, value) {
    this.url.searchParams.append(key, value)
    return this
  }

  body(contentType, data) {
    this.fetchparams.headers['Content-Type'] = contentType
    this.fetchparams.body = data
    return this
  }

  credentials(mode) {
    this.fetchparams.credentials = mode
    return this
  }

  async fetch() {
    let data = undefined
    try {
      let response = await fetch(this.url, this.fetchparams)
      if (this.onstatuses[response.status]) {
        return this.onstatuses[response.status](response)
      }
      if (!response.ok) {
        throw new Error('Status code: ' + response.status + ' ' + response.statusText)
      }
      data = await response.json()
      if (this.onsuccess) {
        data = this.onsuccess(data) || data
      }
      return data
    } catch (error) {
      if (this.onerror) {
        return this.onerror(error)
      } else {
        throw error
      }
    }
  }
}

function Fetch(url) {
  if (url.startsWith('/')) {
    url = window.location.origin + url
  }
  return new _Fetch(url)
}

export default Fetch
