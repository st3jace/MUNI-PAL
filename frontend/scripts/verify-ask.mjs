// Uses the same Vite config without esbuild's config bundling, which traverses
// inaccessible ancestor directories in the managed Windows service shell.
import { startVitest } from 'vitest/node'
import { build } from 'vite'
import config from '../vite.config.js'

const options = { ...config({ mode: 'test', command: 'serve' }), configFile: false }
if (process.argv.includes('--build')) {
  await build({ ...config({ mode: 'production', command: 'build' }), configFile: false })
} else {
  await startVitest('test', process.argv.includes('--all') ? [] : [
    'src/pages/__tests__/Ask.test.tsx', 'src/components/__tests__/AskNavigation.test.tsx',
    'src/components/__tests__/Layout.test.tsx',
  ], { run: true, config: false }, options)
}
