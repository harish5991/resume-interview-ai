import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5174,
    host: '0.0.0.0', // Accessible locally and over LAN
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
        configure: (proxy, options) => {
          proxy.on('error', (err, req, res) => {
            console.warn('[Vite Proxy Warning] Backend on port 8000 is not reachable:', err.message);
            if (res && !res.headersSent && typeof res.writeHead === 'function') {
              res.writeHead(502, {
                'Content-Type': 'application/json',
              });
              res.end(JSON.stringify({
                detail: 'Backend server is not running on http://127.0.0.1:8000. Please start the backend using "python run.py" or "run.bat".',
                error_type: 'BACKEND_OFFLINE'
              }));
            }
          });
        }
      }
    }
  }
})
