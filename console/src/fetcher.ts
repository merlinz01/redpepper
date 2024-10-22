class _Fetch {
  url: URL
  onerror: ((error: unknown) => unknown) | null
  onsuccess: ((data: unknown) => unknown) | null
  onstatuses: Record<number, (response: Response) => unknown>
  fetchparams: RequestInit

  constructor(url: string) {
    this.url = new URL(url)
    this.onerror = null
    this.onsuccess = null
    this.onstatuses = {}
    this.fetchparams = {
      method: 'GET',
      headers: {},
      credentials: 'omit'
    }
  }

  onStatus(status: number, callback: (response: Response) => unknown) {
    this.onstatuses[status] = callback
    return this
  }

  onError(callback: (error: unknown) => unknown) {
    this.onerror = callback
    return this
  }

  onSuccess(callback: (data: unknown) => unknown) {
    this.onsuccess = callback
    return this
  }

  get() {
    this.fetchparams.method = 'GET'
    return this.fetch()
  }

  post(data?: unknown) {
    this.fetchparams.method = 'POST'
    if (data !== undefined) {
      this.body('application/json', JSON.stringify(data))
    }
    return this.fetch()
  }

  put(data?: unknown) {
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

  patch(data: unknown) {
    this.fetchparams.method = 'PATCH'
    if (data !== undefined) {
      this.body('application/json', JSON.stringify(data))
    }
    return this.fetch()
  }

  header(key: string, value: string) {
    if (this.fetchparams.headers === undefined) {
      this.fetchparams.headers = {}
    }
    ;(this.fetchparams.headers as Record<string, string>)[key] = value
    return this
  }

  query(key: string, value: unknown) {
    this.url.searchParams.append(key, String(value))
    return this
  }

  body(contentType: string, data: string) {
    this.header('Content-Type', contentType)
    this.fetchparams.body = data
    return this
  }

  credentials(mode: RequestCredentials) {
    this.fetchparams.credentials = mode
    return this
  }

  async fetch() {
    let data = undefined
    try {
      const response = await fetch(this.url, this.fetchparams)
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
      console.log(error)
      if (this.onerror) {
        return this.onerror(error)
      } else {
        throw error
      }
    }
  }
}

function Fetch(url: string) {
  if (url.startsWith('/')) {
    url = window.location.origin + url
  }
  return new _Fetch(url)
}

export default Fetch
