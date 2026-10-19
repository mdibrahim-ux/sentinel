import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig({
    plugins: [react()],
    // The Cognito browser SDK references Node's `global` name. Mapping it to the
    // browser's globalThis keeps optional Cognito sign-in functional in Vite.
    define: { global: 'globalThis' },
    server: { port: 5173 },
    preview: { port: 4173 },
});
