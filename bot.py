import logging import time import json import asyncio import os from telegram import Update from telegram.constants import ParseMode from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

Configuração do log

logging.basicConfig( format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO )

Token do bot (direto no código por enquanto)

TOKEN = "7578757304:AAGGvhz7cSkpga36bgfy7COrUD8PRrzorKw"

DATA_FILE = 'userdata.json' COOLDOWN_TIME = 600  # 10 minutos

ADMIN_IDS = [6063904865]  # seu user_id

trophy_emojis = ["🥇", "🥈", "🥉"]

Utilitários

def load_data(): try: with open(DATA_FILE, 'r') as f: return json.load(f) except FileNotFoundError: with open(DATA_FILE, 'w') as f: json.dump({}, f) return {} except Exception as e: print(f"[ERRO] Falha ao carregar dados: {e}") return {}

def save_data(data): try: with open(DATA_FILE, 'w') as f: json.dump(data, f) except Exception as e: print(f"[ERRO] Falha ao salvar dados: {e}")

def init_player(user_id, username=None): data = load_data() if str(user_id) not in data: data[str(user_id)] = { 'coins': 0, 'last_mine': 0, 'xp': 0, 'level': 1, 'invited_by': None, 'invites': 0, 'username': username or "" } else: if username: data[str(user_id)]['username'] = username save_data(data)

Comandos principais

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = update.effective_user.id username = update.effective_user.username or "" init_player(user_id, username)

data = load_data()
args = context.args
if args:
    indic_code = args[0].replace("@", "").lower()
    if indic_code != username.lower():
        indicante_id = None
        for uid, info in data.items():
            if info.get('username', "").lower() == indic_code:
                indicante_id = int(uid)
                break
        if indicante_id and data[str(user_id)].get('invited_by') is None:
            data[str(user_id)]['invited_by'] = indicante_id
            data[str(indicante_id)]['coins'] += 20
            data[str(indicante_id)]['xp'] += 10
            data[str(indicante_id)]['invites'] += 1
            save_data(data)
            await update.message.reply_text(
                f"🎉 Você foi indicado por @{data[str(indicante_id)]['username']}! Eles ganharam 20 ZPC e 10 XP.\n\n"
                "👋 Bem-vindo ao *Crypto Miner Bot*!\nUse /minerar para minerar ZappCoins ⛏️",
                parse_mode=ParseMode.MARKDOWN)
            return
        else:
            await update.message.reply_text("Código inválido ou você já foi indicado antes.")
            return
    else:
        await update.message.reply_text("Você não pode se indicar.")
        return

await update.message.reply_text(
    """👋 Bem-vindo ao *Crypto Miner Bot*!

Use /minerar para minerar ZappCoins ⛏️ Use /perfil para ver seu progresso 💼 Use /comprar para adquirir mais moedas 💰""", parse_mode=ParseMode.MARKDOWN )

async def mine(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = update.effective_user.id init_player(user_id, update.effective_user.username) data = load_data() player = data[str(user_id)]

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

async def perfil(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = update.effective_user.id init_player(user_id, update.effective_user.username) data = load_data() player = data[str(user_id)]

msg = (
    f"👤 Perfil de {update.effective_user.first_name}:

" f"💰 ZappCoins: {player['coins']} " f"⭐ Nível: {player['level']} " f"✨ XP: {player['xp']}/{player['level'] * 20} " f"🎮 Convites: {player['invites']}" ) await update.message.reply_text(msg)

async def comprar(update: Update, context: ContextTypes.DEFAULT_TYPE): text = ( "💰 Comprar ZappCoins \n" "Escolha um dos pacotes abaixo e envie o valor para a chave PIX: \n" "🔹 500 ZPC – R$2,99 " "🔸 1000 ZPC – R$4,99 " "💎 2500 ZPC – R$9,99 \n" "🔑 Chave PIX (aleatória): " "5204f881-cbb8-4388-ac89-2eabeb390f58 \n" "📤 Após o pagamento, envie o comprovante aqui mesmo no chat. " "⚠️ Assim que confirmado, você receberá as moedas manualmente!" ) await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

Comandos novos (Ranking, Indicar, Admin)

async def ranking(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = update.effective_user.id data = load_data() sorted_players = sorted(data.items(), key=lambda x: x[1].get('coins', 0), reverse=True) top_10 = sorted_players[:10]

position = None
for idx, (uid, _) in enumerate(sorted_players, start=1):
    if int(uid) == user_id:
        position = idx
        break

msg = "🏆 *Ranking Global ZappCoins* 🏆\n\n"
for idx, (uid, info) in enumerate(top_10, start=1):
    emoji = trophy_emojis[idx - 1] if idx <= 3 else f"{idx}."
    username = info.get('username', f"User{uid}")
    coins = info.get('coins', 0)
    msg += f"{emoji} @{username} — {coins} ZPC\n"

if position and position > 10:
    user_info = data.get(str(user_id), {})
    msg += f"\nSua posição: {position} — @{user_info.get('username', '')} — {user_info.get('coins', 0)} ZPC"

await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

async def indicar(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = update.effective_user.id username = update.effective_user.username or "" data = load_data()

if not context.args:
    await update.message.reply_text("Use: /indicar @username")
    return

indic_username = context.args[0].replace("@", "").lower()
if indic_username == username.lower():
    await update.message.reply_text("Você não pode se indicar.")
    return

indic_id = None
for uid, info in data.items():
    if info.get('username', "").lower() == indic_username:
        indic_id = int(uid)
        break

if indic_id is None:
    await update.message.reply_text("Usuário não encontrado.")
    return

if data.get(str(indic_id), {}).get('invited_by') is not None:
    await update.message.reply_text("Esse usuário já foi indicado.")
    return

data[str(indic_id)]['invited_by'] = user_id
data[str(user_id)]['coins'] += 20
data[str(user_id)]['xp'] += 10
data[str(user_id)]['invites'] += 1
save_data(data)
await update.message.reply_text(f"Você indicou @{indic_username}! 🎉 Você ganhou 20 ZPC e 10 XP.")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE): if update.effective_user.id not in ADMIN_IDS: await update.message.reply_text("Acesso negado.") return

if not context.args:
    await update.message.reply_text("Uso: /reset @usuario")
    return

username = context.args[0].replace("@", "").lower()
data = load_data()

for uid, info in data.items():
    if info.get('username', "").lower() == username:
        data[uid] = {
            'coins': 0,
            'last_mine': 0,
            'xp': 0,
            'level': 1,
            'invited_by': None,
            'invites': 0,
            'username': info.get('username', "")
        }
        save_data(data)
        await update.message.reply_text(f"✅ Dados do @{username} foram resetados.")
        return

await update.message.reply_text("Usuário não encontrado.")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE): if update.effective_user.id not in ADMIN_IDS: await update.message.reply_text("Acesso negado.") return

if not context.args:
    await update.message.reply_text("Uso: /broadcast mensagem")
    return

mensagem = " ".join(context.args)
data = load_data()

count = 0
for uid in data.keys():
    try:
        await context.bot.send_message(chat_id=int(uid), text=mensagem)
        count += 1
    except:
        continue

await update.message.reply_text(f"✅ Broadcast enviado para {count} usuários.")

async def estatisticas(update: Update, context: ContextTypes.DEFAULT_TYPE): if update.effective_user.id not in ADMIN_IDS: await update.message.reply_text("Acesso negado.") return

data = load_data()
total_users = len(data)
total_coins = sum(info.get('coins', 0) for info in data.values())
total_xp = sum(info.get('xp', 0) for info in data.values())

msg = (
    f"*Estatísticas do Bot*

\n" f"Usuários: {total_users}\n" f"Total de ZappCoins: {total_coins}\n" f"Total de XP: {total_xp}" ) await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

Inicialização
from telegram import BotCommand

async def main():
    application = ApplicationBuilder().token(TOKEN).build()

    # Registra todos os handlers de comando
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("minerar", mine))
    application.add_handler(CommandHandler("perfil", perfil))
    application.add_handler(CommandHandler("comprar", comprar))
    application.add_handler(CommandHandler("ranking", ranking))
    application.add_handler(CommandHandler("indicar", indicar))
    application.add_handler(CommandHandler("reset", reset))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("estatisticas", estatisticas))
    application.add_handler(CommandHandler("liberar", liberar))  # admin libera moedas

    # Define os comandos visíveis no menu do Telegram
    await application.bot.set_my_commands([
        BotCommand("start", "Iniciar o bot"),
        BotCommand("minerar", "Minerar ZappCoins"),
        BotCommand("perfil", "Ver seu perfil"),
        BotCommand("comprar", "Comprar ZappCoins"),
        BotCommand("ranking", "Ver ranking dos jogadores"),
        BotCommand("indicar", "Indicar outro jogador"),
        BotCommand("reset", "Resetar jogador (admin)"),
        BotCommand("broadcast", "Mensagem global (admin)"),
        BotCommand("estatisticas", "Dados gerais do bot"),
        BotCommand("liberar", "Adicionar ZPC a um jogador (admin)"),
    ])

    # Inicia o bot com polling
await application.run_polling()

# Executa o main() se estiver rodando direto
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
