/**
 * JARVIS ALL-IN-ONE CLOUD ROOT ENTRYPOINT
 * Auto-bridges Render / Cloud execution to Telegram Voice Bridge
 */
import { main } from './Telegram Voice Bridge/src/index.js';

console.log('[Jarvis Cloud Bootstrap] Starting J.A.R.V.I.S. Multi-Platform AI Engine...');
main().catch(error => {
  console.error('[Fatal Jarvis Cloud Error]:', error);
  process.exit(1);
});
