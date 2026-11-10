import express from 'express';
import cors from 'cors';
import qrcode from 'qrcode-terminal';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';
import makeWASocket, {
    DisconnectReason,
    useMultiFileAuthState,
    fetchLatestBaileysVersion,
    makeCacheableSignalKeyStore
} from '@whiskeysockets/baileys';
import pino from 'pino';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const PORT = process.env.GATEWAY_PORT || 3001;
const PYTHON_WEBHOOK_URL = process.env.PYTHON_WEBHOOK_URL || 'http://127.0.0.1:8000/api/webhook/whatsapp';
const AUTH_METHOD = (process.env.WA_AUTH_METHOD || 'qr').toLowerCase(); // 'qr' or 'pairing'
const PHONE_NUMBER = process.env.WA_PHONE_NUMBER ? process.env.WA_PHONE_NUMBER.replace(/[^0-9]/g, '') : '';
const SESSION_DIR = process.env.WA_SESSION_DIR || path.resolve(__dirname, '../../auth/whatsapp_session');

// Ensure session directory exists
if (!fs.existsSync(SESSION_DIR)) {
    fs.mkdirSync(SESSION_DIR, { recursive: true });
}

const logger = pino({ level: 'silent' }); // Keep terminal clean for QR / Pairing code
let sock = null;
let connectionStatus = 'logged_out'; // 'connected' | 'reconnecting' | 'logged_out'
let reconnectAttempts = 0;
let qrRefreshCount = 0;

const app = express();
app.use(cors());
app.use(express.json());

// Forward incoming message to Python backend
async function forwardToPython(payload) {
    try {
        const response = await fetch(PYTHON_WEBHOOK_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (!response.ok) {
            console.error(`[Gateway] Python webhook responded with status ${response.status}`);
        }
    } catch (err) {
        console.error(`[Gateway] Failed to forward to Python webhook: ${err.message}`);
    }
}

// Connect to WhatsApp
async function startWhatsApp() {
    const { state, saveCreds } = await useMultiFileAuthState(SESSION_DIR);
    const { version } = await fetchLatestBaileysVersion();

    sock = makeWASocket({
        version,
        logger,
        printQRInTerminal: false, // We control terminal printing manually
        auth: {
            creds: state.creds,
            keys: makeCacheableSignalKeyStore(state.keys, logger)
        },
        generateHighQualityLinkPreview: true,
        syncFullHistory: true
    });

    sock.ev.on('creds.update', saveCreds);

    // Pairing code logic if not registered and method is pairing
    if (AUTH_METHOD === 'pairing' && !sock.authState.creds.registered) {
        if (!PHONE_NUMBER) {
            console.error('\n❌ [Gateway Error] WA_AUTH_METHOD=pairing dipilih tetapi WA_PHONE_NUMBER kosong!');
            console.error('Silakan isi nomor di config.yaml atau .env dengan format internasional (contoh: 6281234567890).\n');
        } else {
            // Request pairing code with slight delay to ensure socket readiness
            setTimeout(async () => {
                try {
                    const code = await sock.requestPairingCode(PHONE_NUMBER);
                    console.log('\n======================================================');
                    console.log('🔗 [WHATSAPP PAIRING CODE]');
                    console.log(`📱 Nomor Target : +${PHONE_NUMBER}`);
                    console.log(`🔑 KODE PAIRING : ${code?.match(/.{1,4}/g)?.join('-') || code}`);
                    console.log('📌 Langkah di WhatsApp HP Kedua:');
                    console.log('   Setelan → Perangkat tertaut → Tautkan perangkat');
                    console.log('   Pilih "Tautkan dengan nomor telepon" lalu masukkan kode di atas.');
                    console.log('======================================================\n');
                } catch (err) {
                    console.error('[Gateway] Gagal meminta Pairing Code:', err.message);
                }
            }, 3000);
        }
    }

    sock.ev.on('connection.update', async (update) => {
        const { connection, lastDisconnect, qr } = update;

        if (qr && AUTH_METHOD === 'qr' && !sock.authState.creds.registered) {
            qrRefreshCount++;
            console.clear();
            console.log('\n======================================================');
            console.log(`📲 [WHATSAPP QR CODE] (Refresh #${qrRefreshCount})`);
            console.log('📌 Langkah di WhatsApp HP Kedua:');
            console.log('   Setelan → Perangkat tertaut → Tautkan perangkat → Scan QR ini');
            console.log('======================================================\n');
            qrcode.generate(qr, { small: true });
        }

        if (connection === 'close') {
            const statusCode = lastDisconnect?.error?.output?.statusCode;
            const isLoggedOut = statusCode === DisconnectReason.loggedOut;

            if (isLoggedOut) {
                connectionStatus = 'logged_out';
                console.warn('\n⚠️ [Gateway] Sesi WhatsApp telah KEDALUWARSA / LOGGED OUT dari HP.');
                console.warn('[Gateway] Menghapus sesi lama di auth/whatsapp_session...');
                try {
                    fs.rmSync(SESSION_DIR, { recursive: true, force: true });
                    fs.mkdirSync(SESSION_DIR, { recursive: true });
                } catch (e) {
                    console.error('[Gateway] Gagal menghapus direktori sesi:', e.message);
                }
                console.warn('[Gateway] Silakan jalankan ulang atau scan QR / masukkan pairing code baru.\n');
                // Re-initialize for fresh linking
                reconnectAttempts = 0;
                startWhatsApp();
            } else {
                connectionStatus = 'reconnecting';
                reconnectAttempts++;
                const delayMs = Math.min(1000 * Math.pow(2, Math.min(reconnectAttempts, 5)), 30000); // Exponential backoff max 30s
                console.log(`[Gateway] Koneksi terputus sementara (Status: ${statusCode || 'unknown'}). Reconnect dalam ${delayMs / 1000}s (Percobaan #${reconnectAttempts})...`);
                setTimeout(() => {
                    startWhatsApp();
                }, delayMs);
            }
        } else if (connection === 'open') {
            connectionStatus = 'connected';
            reconnectAttempts = 0;
            qrRefreshCount = 0;
            const userJid = sock.user?.id || 'unknown';
            console.log('\n======================================================');
            console.log('✅ [WHATSAPP GATEWAY TERHUBUNG]');
            console.log(`👤 ID Akun Terhubung : ${userJid}`);
            console.log('🚀 Siap menerima dan meneruskan pesan ke Python Core.');
            console.log('======================================================\n');
        }
    });

    // Track recent message IDs to prevent duplicate processing
    const processedMessageIds = new Set();

    // Listen for incoming messages
    sock.ev.on('messages.upsert', async (m) => {
        // ONLY process live real-time notifications, skip historical catch-up/sync
        if (m.type !== 'notify') return;
        if (!m.messages || m.messages.length === 0) return;

        for (const msg of m.messages) {
            // CRITICAL: NEVER process messages sent by the bot itself! (prevents infinite echo loops)
            if (msg.key?.fromMe) continue;

            const msgId = msg.key?.id;
            if (msgId) {
                if (processedMessageIds.has(msgId)) continue;
                processedMessageIds.add(msgId);
                if (processedMessageIds.size > 2000) {
                    const oldest = processedMessageIds.values().next().value;
                    processedMessageIds.delete(oldest);
                }
            }

            const fromMe = msg.key?.fromMe;
            const jid = msg.key?.remoteJid;
            const participant = msg.key?.participant; // For groups
            const isGroup = jid?.endsWith('@g.us');
            const sender = isGroup ? (participant || jid) : jid;

            // Extract text message content
            const messageContent = msg.message;
            if (!messageContent) continue;

            const text = messageContent.conversation ||
                messageContent.extendedTextMessage?.text ||
                messageContent.imageMessage?.caption ||
                messageContent.videoMessage?.caption ||
                '';

            const payload = {
                message_id: msg.key.id,
                from_me: fromMe,
                jid: jid,
                sender: sender,
                is_group: isGroup,
                timestamp: msg.messageTimestamp,
                text: text,
                key: msg.key,
                raw: msg
            };

            await forwardToPython(payload);
        }
    });
}

// REST Endpoints for Python Core Adapter
app.get('/status', (req, res) => {
    res.json({
        status: connectionStatus,
        user: sock?.user || null,
        reconnect_attempts: reconnectAttempts
    });
});

app.post('/send', async (req, res) => {
    try {
        const { to, text } = req.body;
        if (!to || !text) {
            return res.status(400).json({ error: 'Missing "to" or "text"' });
        }
        if (connectionStatus !== 'connected' || !sock) {
            return res.status(503).json({ error: 'WhatsApp not connected', status: connectionStatus });
        }

        const formattedTo = to.includes('@') ? to : `${to}@s.whatsapp.net`;
        const sent = await sock.sendMessage(formattedTo, { text });
        res.json({ success: true, message_id: sent?.key?.id });
    } catch (err) {
        console.error('[Gateway] Error sending message:', err.message);
        res.status(500).json({ error: err.message });
    }
});

app.post('/react', async (req, res) => {
    try {
        const { to, key, emoji } = req.body;
        if (!key || !emoji) {
            return res.status(400).json({ error: 'Missing "key" or "emoji"' });
        }
        if (connectionStatus !== 'connected' || !sock) {
            return res.status(503).json({ error: 'WhatsApp not connected', status: connectionStatus });
        }

        const reactionMessage = {
            react: {
                text: emoji,
                key: key
            }
        };
        const target = to ? (to.includes('@') ? to : `${to}@s.whatsapp.net`) : key.remoteJid;
        await sock.sendMessage(target, reactionMessage);
        res.json({ success: true });
    } catch (err) {
        console.error('[Gateway] Error sending reaction:', err.message);
        res.status(500).json({ error: err.message });
    }
});

app.listen(PORT, () => {
    console.log(`[Gateway] Server berjalan di http://127.0.0.1:${PORT}`);
    startWhatsApp();
});
