
import logging
import time
import json
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = '7578757304:AAGGvhz7cSkpga36bgfy7COrUD8PRrzorKw'  # Substitua pelo seu token do BotFather

DATA_FILE = 'userdata.json'
COOLDOWN_TIME = 600  # 10 minutos

# ----- Utilitários -----
def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

def init_player(user_id, username=None):
    data = load_data()
    if str(user_id) not in data:
        data[str(user_id)] = {
            'coins': 0,
            'last_mine': 0,
            'xp': 0,
            'level': 1,
            'invited_by': None,
            'invites': 0,
            'username': username or ""
        }
    else:
        if username:
            data[str(user_id)]['username'] = username
    save_data(data)

# ----- Comandos -----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    init_player(user_id, update.effective_user.username)
    await update.message.reply_text(
        """👋 Bem-vindo ao *Crypto Miner Bot*!

"
        "Use /minerar para minerar ZappCoins ⛏️
"
        "Use /perfil para ver seu progresso 💼
"
        "Use /comprar para adquirir mais moedas 💰""",
        parse_mode=ParseMode.MARKDOWN
    )

async def mine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    init_player(user_id, update.effective_user.username)
    data = load_data()
    player = data[str(user_id)]

    now = time.time()
    elapsed = now - player['last_mine']

    if elapsed < COOLDOWN_TIME:
        wait = int(COOLDOWN_TIME - elapsed)
        await update.message.reply_text(f"⏳ Aguarde {wait} segundos para minerar novamente.")
        return

    coins_earned = 10 + player['level'] * 2
    player['coins'] += coins_earned
    player['last_mine'] = now
    player['xp'] += 5

    if player['xp'] >= player['level'] * 20:
        player['level'] += 1
        player['xp'] = 0
        await update.message.reply_text(f"🚀 Parabéns! Você subiu para o nível {player['level']}!")

    save_data(data)
    await update.message.reply_text(f"⛏️ Você minerou {coins_earned} ZappCoins!")

async def perfil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    init_player(user_id, update.effective_user.username)
    data = load_data()
    player = data[str(user_id)]
    msg = (
        f"👤 Perfil de {update.effective_user.first_name}:\n"
"
        f"💰 ZappCoins: {player['coins']}\n"
"
        f"⭐ Nível: {player['level']}\n"
"
        f"✨ XP: {player['xp']}/{player['level']*20}\n"
"
        f"🎮 Convites: {player['invites']}\n"
    )
    await update.message.reply_text(msg)

async def comprar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "💰 *Comprar ZappCoins*

"
        "Escolha um dos pacotes abaixo e envie o valor para a chave PIX:

"
        "🔹 500 ZPC – *R$2,99*
"
        "🔸 1000 ZPC – *R$4,99*
"
        "💎 2500 ZPC – *R$9,99*

"
        "🔑 *Chave PIX (aleatória):*
"
        "`5204f881-cbb8-4388-ac89-2eabeb390f58`

"
        "📤 Após o pagamento, envie o comprovante aqui mesmo no chat.
"
        "⚠️ Assim que confirmado, você receberá as moedas manualmente!"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def liberar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("Uso: /liberar @usuario quantidade")
        return

    username = context.args[0].replace("@", "")
    quantidade = int(context.args[1])

    data = load_data()
    for uid, info in data.items():
        if 'username' in info and info['username'] == username:
            info['coins'] += quantidade
            save_data(data)
            await update.message.reply_text(f"✅ {quantidade} ZPC adicionados para @{username}.")
            return

    await update.message.reply_text(f"❌ Usuário @{username} não encontrado no banco de dados.")

# ----- Main -----
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("minerar", mine))
    app.add_handler(CommandHandler("perfil", perfil))
    app.add_handler(CommandHandler("comprar", comprar))
    app.add_handler(CommandHandler("liberar", liberar))

    print("🤖 Bot rodando...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
