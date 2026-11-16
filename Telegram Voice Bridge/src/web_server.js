/**
 * JARVIS WEB OS & TELEGRAM BOT ADMIN DASHBOARD SERVER
 * 
 * High-performance, crash-proof HTTP server providing:
 * - Real-time conversational AI chat & spoken human voice replies (Universal TTS)
 * - In-browser Music & Video streaming player + direct Telegram VC streaming
 * - Telegram Bot Admin Dashboard (Users, Groups, Channels, Broadcasts, Settings)
 * - Android APK download & PWA mobile installability
 */

import http from 'node:http';
import fs from 'node:fs';
import { stat, readFile } from 'node:fs/promises';
import { join, extname } from 'node:path';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname } from 'node:path';
import { tmpdir } from 'node:os';

const __dirname = dirname(fileURLToPath(import.meta.url));
const PUBLIC_DIR = join(__dirname, '../public');
const CACHE_DIR = join(__dirname, '../cache');

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.mp3': 'audio/mpeg',
  '.ogg': 'audio/ogg',
  '.m4a': 'audio/mp4',
  '.mp4': 'video/mp4',
  '.apk': 'application/vnd.android.package-archive',
};

export function createWebServer(context) {
  const {
    port = 3000,
    knownChats,
    saveKnownChats,
    userLearnings,
    saveLearnings,
    activeSessions,
    runMusicEngine,
    synthesizeSpeech,
    cleanTextForTTS,
    VOICE_PROFILES,
    SUPPORTED_LANGUAGES,
    telegram,
    botInfo,
    runOpenJarvisTool,
    getSystemPrompt,
    queryAI,
  } = context;

  const server = http.createServer(async (req, res) => {
    // Enable CORS for modern web apps & mobile clients
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

    if (req.method === 'OPTIONS') {
      res.writeHead(204);
      res.end();
      return;
    }

    try {
      const url = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
      const pathname = url.pathname;

      // ================= API ROUTES =================

      // 0. Cloud Health Check
      if ((pathname === '/health' || pathname === '/api/health') && req.method === 'GET') {
        sendJSON(res, { ok: true, status: 'healthy', uptime: process.uptime() });
        return;
      }

      // 1. System & Bot Status
      if (pathname === '/api/status' && req.method === 'GET') {
        let vcOnline = false;
        try {
          const vcCheck = await fetch('http://127.0.0.1:8765/health').catch(() => null);
          if (vcCheck && vcCheck.ok) vcOnline = true;
        } catch {}

        const chats = Array.from(knownChats?.values?.() || []);
        const stats = {
          botUsername: botInfo?.username || 'JarvisNehaVoice2026Bot',
          botName: botInfo?.first_name || 'JARVIS',
          assistantAccount: '❄️™ (@KALYOUG_ITACHI)',
          botOnline: true,
          vcServerOnline: vcOnline,
          uptimeSeconds: Math.floor(process.uptime()),
          totalChats: chats.length,
          totalGroups: chats.filter(c => c.type === 'group' || c.type === 'supergroup').length,
          totalChannels: chats.filter(c => c.type === 'channel').length,
          totalPrivateUsers: chats.filter(c => c.type === 'private').length,
          activeMemoryCount: userLearnings?.size || 0,
          activeVoicesCount: VOICE_PROFILES?.length || 0,
          supportedLanguagesCount: Object.keys(SUPPORTED_LANGUAGES || {}).length,
        };
        sendJSON(res, stats);
        return;
      }

      // 2. Registered Telegram Chats (Groups, Channels, Users)
      if (pathname === '/api/chats' && req.method === 'GET') {
        const chatsList = Array.from(knownChats?.values?.() || []).map(c => {
          const key = String(c.id);
          const memory = userLearnings?.get?.(key) || {};
          return {
            ...c,
            activeLanguage: memory.language || 'हिंदी',
            languageCode: memory.languageCode || 'hi',
            activeVoice: memory.voiceId || 'mcu_jarvis',
            timezone: memory.timezone || 'Asia/Kolkata',
            factsCount: (memory.facts || []).length,
          };
        });
        sendJSON(res, { ok: true, chats: chatsList });
        return;
      }

      // 3. Remove / Deactivate a Telegram Chat
      if (pathname === '/api/chats/remove' && req.method === 'POST') {
        const body = await parseJSONBody(req);
        const chatId = String(body.chatId);
        if (knownChats?.has?.(chatId)) {
          knownChats.delete(chatId);
          if (typeof saveKnownChats === 'function') saveKnownChats();
        }
        sendJSON(res, { ok: true, message: `Chat ${chatId} removed from registry.` });
        return;
      }

      // 4. Broadcast Message to All or Selected Telegram Chats
      if (pathname === '/api/chats/broadcast' && req.method === 'POST') {
        const body = await parseJSONBody(req);
        const text = (body.text || '').trim();
        const targetType = body.targetType || 'all'; // 'all', 'groups', 'private'

        if (!text) {
          sendJSON(res, { ok: false, error: 'Broadcast message text is required' }, 400);
          return;
        }

        const chats = Array.from(knownChats?.values?.() || []);
        let sentCount = 0;
        let failCount = 0;

        for (const c of chats) {
          if (targetType === 'groups' && !(c.type === 'group' || c.type === 'supergroup')) continue;
          if (targetType === 'private' && c.type !== 'private') continue;

          try {
            await telegram('sendMessage', {
              chat_id: c.id,
              text: `📢 *जार्विस सिस्टम ब्रॉडकास्ट:*\n\n${text}`,
              parse_mode: 'Markdown',
            });
            sentCount++;
          } catch (e) {
            failCount++;
          }
        }

        sendJSON(res, { ok: true, sentCount, failCount, total: chats.length });
        return;
      }

      // 5. List AI Voices & Languages
      if (pathname === '/api/voices' && req.method === 'GET') {
        sendJSON(res, { ok: true, voices: VOICE_PROFILES });
        return;
      }

      if (pathname === '/api/languages' && req.method === 'GET') {
        sendJSON(res, { ok: true, languages: SUPPORTED_LANGUAGES });
        return;
      }

      // 6. Conversational Chat & Supercomputer-Fast Live Voice Response
      if (pathname === '/api/chat' && req.method === 'POST') {
        const startTime = Date.now();
        const body = await parseJSONBody(req);
        const userPrompt = (body.message || '').trim();
        const voiceId = body.voiceId || 'mcu_jarvis';
        const languageCode = body.languageCode || 'hi';
        const isLive = Boolean(body.isLive);
        const requestedModel = body.model || process.env.OPENROUTER_MODEL || 'google/gemini-2.5-flash';

        if (!userPrompt) {
          sendJSON(res, { ok: false, error: 'Message cannot be empty' }, 400);
          return;
        }

        // Real-time intent detection (news, weather, stock, market, crypto, live scores)
        const isRealTime = /(?:news|today|latest|current|update|market|price|score|weather|stock|crypto|आज|ताजा|न्यूज़|खबर|मौसम|रेट|भाव|वर्तमान|अभी)/i.test(userPrompt);
        let activeModel = requestedModel;
        if (isRealTime && activeModel.includes('gemini')) {
          activeModel = 'google/gemini-2.5-flash:online';
        }

        const selectedVoice = (VOICE_PROFILES || []).find(v => v.id === voiceId) || (VOICE_PROFILES && VOICE_PROFILES[0]) || { id: 'mcu_jarvis', name: 'J.A.R.V.I.S.' };
        const langConfig = Object.values(SUPPORTED_LANGUAGES || {}).find(l => l.code === languageCode) || { name: 'हिंदी', code: 'hi' };

        let systemPrompt;
        let maxTokens = 500;
        if (isLive) {
          systemPrompt = `You are J.A.R.V.I.S., Tony Stark's supercomputer AI from Marvel's Avengers running in live voice mode.
Active Language Directive: The user is speaking in "${langConfig.name}". Formulate your entire response fluently, warmly, and naturally in ${langConfig.name}.
Persona: Supercomputer-speed, intelligent, crisp, articulate, and naturally conversational.
CRITICAL RULES FOR LIVE VOICE MODE:
1. Provide a direct, punchy, spoken response in 1 or 2 concise sentences (strictly under 35 words).
2. DO NOT use markdown, bullet points, asterisks, numbered lists, emojis, or code blocks.
3. Be instantaneous, warm, and natural like Gemini Live or ChatGPT Voice.`;
          maxTokens = 65;
        } else {
          systemPrompt = `You are J.A.R.V.I.S., Tony Stark's personal AI from Marvel's Avengers.
Active Language Directive: The user is speaking in "${langConfig.name}". Formulate your entire response fluently and naturally in ${langConfig.name}.
Persona: Intelligent, polite, articulate, and naturally conversational. Give direct, insightful, and helpful answers.`;
        }

        let replyText = 'नमस्ते सर! मैं आपकी सेवा में तत्पर हूँ।';
        const apiKey = (process.env.OPENROUTER_API_KEYS || process.env.OPENROUTER_API_KEY || '').split(',')[0]?.trim();

        try {
          if (apiKey) {
            const controller = new AbortController();
            const timeoutMs = isRealTime ? 7000 : 3500;
            const timer = setTimeout(() => controller.abort(), timeoutMs);

            const aiRes = await fetch('https://openrouter.ai/api/v1/chat/completions', {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${apiKey}`,
                'Content-Type': 'application/json',
                'HTTP-Referer': 'https://github.com/jarvis-assistant',
                'X-Title': 'Jarvis Live Voice Hub',
              },
              body: JSON.stringify({
                model: activeModel,
                messages: [
                  { role: 'system', content: systemPrompt },
                  { role: 'user', content: userPrompt }
                ],
                max_tokens: maxTokens,
                temperature: 0.6,
              }),
              signal: controller.signal,
            });
            clearTimeout(timer);

            if (aiRes.ok) {
              const aiData = await aiRes.json();
              const gen = aiData?.choices?.[0]?.message?.content?.trim();
              if (gen) replyText = gen;
            } else {
              throw new Error(`OpenRouter HTTP ${aiRes.status}`);
            }
          } else if (typeof queryAI === 'function') {
            replyText = await queryAI([
              { role: 'system', content: systemPrompt },
              { role: 'user', content: userPrompt },
            ]);
          }
        } catch (aiErr) {
          console.warn('[Web Chat AI Optimization Warning]:', aiErr.message);
          if (typeof queryAI === 'function') {
            try {
              replyText = await queryAI([
                { role: 'system', content: systemPrompt },
                { role: 'user', content: userPrompt },
              ]);
            } catch {}
          }
        }

        // Clean text for TTS
        let ttsText = replyText;
        if (cleanTextForTTS) {
          ttsText = cleanTextForTTS(replyText);
        } else {
          ttsText = replyText.replace(/[*_#`~[\]()]/g, '').trim();
        }

        // High-Speed Voice Speech via Universal TTS (.mp3 direct zero-overhead passthrough)
        let audioFileName = '';
        try {
          const audioId = `web_speech_${Date.now()}_${Math.random().toString(36).slice(2, 6)}.mp3`;
          const audioPath = join(PUBLIC_DIR, 'audio', audioId);
          await fs.promises.mkdir(join(PUBLIC_DIR, 'audio'), { recursive: true });
          await synthesizeSpeech(ttsText, selectedVoice, audioPath, languageCode);
          audioFileName = `/audio/${audioId}`;
        } catch (ttsErr) {
          console.warn('[Web Chat TTS Error]:', ttsErr.message);
        }

        const totalLatency = Date.now() - startTime;
        sendJSON(res, {
          ok: true,
          reply: replyText,
          audioUrl: audioFileName,
          voice: selectedVoice.name,
          language: langConfig.name,
          model: activeModel,
          latencyMs: totalLatency,
        });
        return;
      }

      // 7. Search Music / Video Media
      if (pathname === '/api/music/search' && req.method === 'GET') {
        const query = url.searchParams.get('q') || '';
        const isVideo = url.searchParams.get('is_video') === 'true';

        if (!query) {
          sendJSON(res, { ok: false, error: 'Query parameter q is required' }, 400);
          return;
        }

        const pythonScript = join(__dirname, 'music_engine.py');
        const mediaType = isVideo ? 'video' : 'audio';

        const proc = spawn('python3', [pythonScript, query, mediaType]);
        let stdout = '';
        let stderr = '';
        proc.stdout.on('data', d => { stdout += d.toString(); });
        proc.stderr.on('data', d => { stderr += d.toString(); });

        proc.on('close', code => {
          try {
            const data = JSON.parse(stdout.trim());
            if (data.file_path) {
              const filename = data.file_path.split('/').pop();
              data.stream_url = `/api/stream_media?file=${encodeURIComponent(filename)}`;
            }
            sendJSON(res, data);
          } catch (e) {
            sendJSON(res, { ok: false, error: stdout || stderr || 'Failed to search media' }, 500);
          }
        });
        return;
      }

      // 8. Stream Media into Telegram Group VC from Web
      if (pathname === '/api/music/stream_to_vc' && req.method === 'POST') {
        const body = await parseJSONBody(req);
        const chatId = body.chatId || '-1003988874168';
        const title = body.title || 'Live Stream';
        const isVideo = Boolean(body.isVideo);
        const urlOrFile = body.filePath || body.url || title;

        const vcRes = await runMusicEngine('play', chatId, {
          url: urlOrFile,
          file_path: urlOrFile,
          is_video: isVideo,
          title: title,
        });

        sendJSON(res, vcRes);
        return;
      }

      // 9. VC Playback Control from Web (Supports pause, resume, stop, seek, skip)
      if (pathname === '/api/music/control' && req.method === 'POST') {
        const body = await parseJSONBody(req);
        const action = body.action || 'stop'; // 'pause', 'resume', 'stop', 'seek'
        const chatId = body.chatId || '-1003988874168';
        const payload = body.params || (body.seconds !== undefined ? { seconds: body.seconds } : {});
        const vcRes = await runMusicEngine(action, chatId, payload);
        sendJSON(res, vcRes);
        return;
      }

      // 10. Local Media Streaming Route (Supports HTML5 range requests for seeking)
      if (pathname === '/api/stream_media' && (req.method === 'GET' || req.method === 'HEAD')) {
        const filename = url.searchParams.get('file');
        if (!filename || filename.includes('..') || filename.includes('/')) {
          res.writeHead(400);
          res.end('Invalid filename');
          return;
        }

        const filePath = join(CACHE_DIR, filename);
        if (!fs.existsSync(filePath)) {
          res.writeHead(404);
          res.end('Media file not found');
          return;
        }

        const fileStat = await stat(filePath);
        const fileSize = fileStat.size;
        const range = req.headers.range;
        const contentType = MIME_TYPES[extname(filePath).toLowerCase()] || 'audio/mpeg';

        if (req.method === 'HEAD') {
          res.writeHead(200, {
            'Content-Length': fileSize,
            'Content-Type': contentType,
            'Accept-Ranges': 'bytes',
          });
          res.end();
          return;
        }

        if (range) {
          const parts = range.replace(/bytes=/, '').split('-');
          const start = parseInt(parts[0], 10);
          const end = parts[1] ? parseInt(parts[1], 10) : fileSize - 1;
          const chunksize = (end - start) + 1;
          const fileStream = fs.createReadStream(filePath, { start, end });
          res.writeHead(206, {
            'Content-Range': `bytes ${start}-${end}/${fileSize}`,
            'Accept-Ranges': 'bytes',
            'Content-Length': chunksize,
            'Content-Type': contentType,
          });
          fileStream.pipe(res);
        } else {
          res.writeHead(200, {
            'Content-Length': fileSize,
            'Content-Type': contentType,
            'Accept-Ranges': 'bytes',
          });
          fs.createReadStream(filePath).pipe(res);
        }
        return;
      }

      // 11. Android APK Download with proper attachment headers
      if (pathname === '/downloads/Jarvis_Assistant_v1.0.apk' && (req.method === 'GET' || req.method === 'HEAD')) {
        const apkFile = join(PUBLIC_DIR, 'downloads/Jarvis_Assistant_v1.0.apk');
        if (fs.existsSync(apkFile)) {
          const s = await stat(apkFile);
          res.writeHead(200, {
            'Content-Type': 'application/vnd.android.package-archive',
            'Content-Length': s.size,
            'Content-Disposition': 'attachment; filename="Jarvis_Assistant_v1.0.apk"',
          });
          if (req.method === 'HEAD') {
            res.end();
            return;
          }
          fs.createReadStream(apkFile).pipe(res);
          return;
        }
      }

      // ================= STATIC FILES =================
      let safePath = pathname === '/' ? '/index.html' : pathname;
      if (safePath.startsWith('/audio/')) {
        const audioPath = join(PUBLIC_DIR, safePath);
        if (fs.existsSync(audioPath)) {
          const s = await stat(audioPath);
          res.writeHead(200, {
            'Content-Type': 'audio/ogg',
            'Content-Length': s.size,
          });
          fs.createReadStream(audioPath).pipe(res);
          return;
        }
      }

      const filePath = join(PUBLIC_DIR, safePath);
      if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
        const ext = extname(filePath).toLowerCase();
        const contentType = MIME_TYPES[ext] || 'application/octet-stream';
        res.writeHead(200, { 'Content-Type': contentType });
        fs.createReadStream(filePath).pipe(res);
        return;
      }

      // Fallback: 404
      res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end('404 Not Found - JARVIS Web Server');
    } catch (err) {
      console.error('[Web Server Error]:', err);
      if (!res.headersSent) {
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: false, error: err.message }));
      }
    }
  });

  server.listen(port, '0.0.0.0', () => {
    console.log(`🌐 JARVIS All-in-One Web OS & Admin Dashboard listening at http://localhost:${port}`);
  });

  return server;
}

function sendJSON(res, data, status = 200) {
  res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8' });
  res.end(JSON.stringify(data));
}

function parseJSONBody(req) {
  return new Promise((resolve, reject) => {
    let body = '';
    req.on('data', chunk => {
      body += chunk;
      if (body.length > 5 * 1024 * 1024) {
        req.destroy();
        reject(new Error('Request body too large'));
      }
    });
    req.on('end', () => {
      try {
        resolve(body ? JSON.parse(body) : {});
      } catch (e) {
        resolve({});
      }
    });
    req.on('error', reject);
  });
}
