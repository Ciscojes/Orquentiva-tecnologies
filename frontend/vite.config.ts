import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

const apiTarget = process.env.ORQENTIVA_API_TARGET || 'http://127.0.0.1:8001'
// La demostración aislada puede usar otro backend sin alterar el desarrollo habitual.
export default defineConfig({
  plugins: [react()],
  server: { proxy: { '/book': apiTarget, '/leads': apiTarget, '/auth': apiTarget, '/admin': apiTarget, '/client': apiTarget } },
})
