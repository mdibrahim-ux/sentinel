# Frontend runtime and TypeScript fix

This patch addresses the blank page and the seven frontend build errors reported during local Windows development.

## Changes

- The Cognito SDK is dynamically imported only when Cognito is configured and cloud auth methods are used. Local demonstration mode no longer evaluates the Cognito browser SDK during initial app startup.
- Vite maps the Node-style `global` reference used by the Cognito SDK to browser `globalThis`.
- Adds `src/vite-env.d.ts` so TypeScript knows `import.meta.env` is provided by Vite.
- Adds explicit Cognito session callback types.
- Handles a possibly undefined `Array.pop()` result in the architecture map.
- Removes two unused declarations/props that fail the strict `noUnusedLocals`/`noUnusedParameters` build.

## Apply on Windows

Extract `sentinal-frontend-runtime-fix.zip` into the existing project directory (the folder that contains `frontend`) and allow the four frontend files to be overwritten. This patch does not replace `package.json`, `package-lock.json`, `.env` files, the backend, or local data.

Then run from PowerShell:

```powershell
cd "$HOME\OneDrive\Desktop\sentinal-project\frontend"
npm run build
```

If the build succeeds, stop the running Vite process with `Ctrl+C`, then run:

```powershell
npm run dev
```

Reload `http://localhost:5173` with `Ctrl+Shift+R`.

## Verification note

The user's reported compiler messages are directly addressed in the patch. A fresh build could not be run in the packaging container because npm registry access timed out; successful installation and a passing build on the user's Windows environment are not claimed until verified there.
