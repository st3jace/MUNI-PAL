/// <reference types="vite/client" />

declare module 'html2pdf.js'

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string
  readonly VITE_API_BEARER_TOKEN?: string
  readonly VITE_API_PROXY_TARGET?: string
  readonly VITE_DEV_USER_ID?: string
  readonly VITE_DEV_USER_ROLE?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
