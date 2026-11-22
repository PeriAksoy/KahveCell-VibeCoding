import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Backend yalnızca 5173 adresinden gelen isteklere izin veriyor (CORS).
  // Port doluysa sessizce başka porta geçmek yerine hata versin.
  server: { port: 5173, strictPort: true },
})
