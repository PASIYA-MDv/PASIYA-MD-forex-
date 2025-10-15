// Minimal Baileys-based sender (Node.js)
// Usage: node send_whatsapp.js "<groupJid>" "<message>"
//
// NOTE: This file is a placeholder. To use, install baileys and run once to scan QR.
//
// npm install @adiwajshing/baileys qrcode-terminal
const { default: makeWASocket, useSingleFileAuthState, delay } = require('@adiwajshing/baileys');
const qrcode = require('qrcode-terminal');
const fs = require('fs');

const args = process.argv.slice(2);
if (args.length < 2) {
  console.log('Usage: node send_whatsapp.js <groupJid> <message>');
  process.exit(1);
}
const [groupJid, message] = args;

async function main() {
  const { state, saveCreds } = useSingleFileAuthState('./auth_info.json');
  const sock = makeWASocket({ auth: state });
  sock.ev.on('creds.update', saveCreds);
  sock.ev.on('connection.update', (update) => {
    if (update.connection === 'open') {
      console.log('Connected to WhatsApp');
    }
    if (update.qr) {
      qrcode.generate(update.qr, { small: true });
    }
  });
  // Wait a bit for connection
  await delay(3000);
  await sock.sendMessage(groupJid, { text: message });
  console.log('Message sent');
  process.exit(0);
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
