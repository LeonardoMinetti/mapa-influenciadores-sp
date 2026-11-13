import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// base relativo: funciona em https://<usuario>.github.io/mapa-influenciadores-sp/
export default defineConfig({
  plugins: [react()],
  base: './',
})
