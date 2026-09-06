import { cp, mkdir, rm } from 'node:fs/promises';

await rm('dist', { recursive: true, force: true });
await mkdir('dist', { recursive: true });
await cp('index.html', 'dist/index.html');
await cp('public', 'dist', { recursive: true });
await cp('src/app.js', 'dist/app.js');
await cp('src/styles.css', 'dist/styles.css');
await cp('src/service-worker.js', 'dist/service-worker.js');
console.log('ContinuityOS minimal PWA built');
