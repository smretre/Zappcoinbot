import logging
import time
import json
import asyncio
import os
from telegram import Update, BotCommand
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Configuração do log
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = "7578757304:AAGGvhz7cSkpga36bgfy7COrUD8PRrzorKw"
DATA_FILE = 'userdata.json'
COOLDOWN_TIME = 600  # 10 minutos
ADMIN_IDS = [6063904865]  # Coloque seu user_id aqui para admin

trophy_emojis = ["🥇", "🥈", "🥉"]

# VIP planos: preço (R$), dias de ciclo, rendimento diário (R$)
VIP_PLANS = {
    0: {"price": 0, "days": 0, "daily_profit": 0.0, "multiplier": 1},
    1: {"price": 10, "days": 7, "daily_profit": 0.50, "multiplier": 1},
    2: {"price": 20, "days": 7, "daily_profit": 1.00, "multiplier": 2},
    3: {"price": 40, "days": 7, "daily_profit": 2.00, "multiplier": 4},
    4: {"price": 80, "days": 15, "daily_profit": 4.00, "multiplier": 8},
    5: {"price": 160, "days": 15, "daily_profit": 8.00, "multiplier": 16},
    6: {"price": 320, "days": 30, "daily_profit": 16.00, "multiplier": 32},
    7: {"price": 640, "days": 30, "daily_profit": 32.00, "multiplier": 64},
    8: {"price": 1280, "days": 30, "daily_profit": 64.00, "multiplier": 128},
    9: {"price": 2560, "days": 60, "daily_profit": 128.00, "multiplier": 256},
}

# Utilitários
def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        with open(DATA_FILE, 'w') as f:
            json.dump({}, f)
        return {}
    except Exception as e:
        print(f"[ERRO] Falha ao carregar dados: {e}")
        return {}

def save_data(data):
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"[ERRO] Falha ao salvar dados: {e}")

def init_player(user_id, username=None):
    data = load_data()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {
            'coins': 0,
            'last_mine': 0,
            'xp': 0,
            'level': 1,
            'invited_by': None,
            'invites': 0,
            'username': username or "",
            'vip_level': 0,
            'vip_start': 0,
            'last_alimentar': 0,
            'pending_profit': 0.0,
            'total_sacado': 0.0,
            'comissoes': 0.0,
        }
    else:
        if username:
            data[uid]['username'] = username
    save_data(data)

def is_vip_active(player):
    if player['vip_level'] == 0:
        return False
    vip = VIP_PLANS.get(player['vip_level'])
    if not vip:
        return False
    elapsed_days = (time.time() - player['vip_start']) / 86400
    return elapsed_days <= vip['days']

def vip_remaining_days(player):
    if player['vip_level'] == 0:
        return 0
    vip = VIP_PLANS.get(player['vip_level'])
    if not vip:
        return 0
    elapsed_days = (time.time() - player['vip_start']) / 86400
    remaining = vip['days'] - elapsed_days
    return max(0, int(remaining))

# Comandos

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or ""
    init_player(user_id, username)
    await update.message.reply_text(
        "👋 Bem-vindo ao Crypto Miner Bot!\n\n"
        "Use /minerar para minerar ZappCoins ⛏️\n"
        "Use /perfil para ver seu progresso 💼\n"
        "Use /comprarvip para ver planos VIP 💎\n"
        "Use /vipstatus para ver seu status VIP\n"
        "Use /alimentar para coletar rendimento diário\n"
        "Use /sacar para solicitar saque\n"
        "Use /indicar para indicar amigos e ganhar bônus\n"
        "Use /ranking para ver o ranking dos melhores mineradores"
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

    base_coins = 10 + player['level'] * 2
    vip_multiplier = VIP_PLANS.get(player['vip_level'], {}).get('multiplier', 1)
    coins_earned = base_coins * vip_multiplier

    player['coins'] += coins_earned
    player['last_mine'] = now
    player['xp'] += 5

    # Level up
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

    vip_active = is_vip_active(player)
    vip_text = "Nenhum VIP ativo" if not vip_active else (
        f"VIP {player['vip_level']} ativo, "
        f"restam {vip_remaining_days(player)} dias, "
        f"rendimento diário R${VIP_PLANS[player['vip_level']]['daily_profit']:.2f}"
    )

    msg = (
        f"👤 Perfil de {update.effective_user.first_name}:\n\n"
        f"💰 ZappCoins: {player['coins']}\n"
        f"⭐ Nível: {player['level']}\n"
        f"✨ XP: {player['xp']}/{player['level'] * 20}\n"
        f"🎮 Convites: {player['invites']}\n"
        f"💎 Status VIP: {vip_text}\n"
        f"💰 Lucro pendente: R${player['pending_profit']:.2f}\n"
        f"📤 Total sacado: R${player['total_sacado']:.2f}\n"
        f"💵 Comissões: R${player['comissoes']:.2f}"
    )
    await update.message.reply_text(msg)

async def comprarvip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "💎 *Planos VIP disponíveis:*\n\n"
    for level, plan in sorted(VIP_PLANS.items()):
        if level == 0:
            continue
        msg += (f"VIP {level} - R${plan['price']} - Ciclo {plan['days']} dias - "
                f"Rendimento diário R${plan['daily_profit']:.2f}\n")
    msg += ("\nPara ativar um VIP, envie /ativarvip <nível>\n"
            "Exemplo: /ativarvip 2\n")
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

async def ativarvip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    init_player(user_id, update.effective_user.username)
    data = load_data()
    player = data[str(user_id)]

    if not context.args:
        await update.message.reply_text("Uso: /ativarvip <nível>\nExemplo: /ativarvip 3")
        return

    try:
        level = int(context.args[0])
    except:
        await update.message.reply_text("Nível inválido.")
        return

    if level not in VIP_PLANS or level == 0:
        await update.message.reply_text("Plano VIP inválido.")
        return

    plan = VIP_PLANS[level]

    if player['coins'] < plan['price']:
        await update.message.reply_text(f"Você não tem ZappCoins suficientes para ativar VIP {level}.")
        return

    # Ativa VIP
    player['coins'] -= plan['price']
    player['vip_level'] = level
    player['vip_start'] = time.time()
    player['pending_profit'] = 0.0  # reset lucro pendente
    save_data(data)
    await update.message.reply_text(f"✅ VIP {level} ativado com sucesso! Ciclo de {plan['days']} dias.")

async def vipstatus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = load_data()
    player = data.get(str(user_id))

    if not player or player['vip_level'] == 0:
        await update.message.reply_text("Você não possui VIP ativo.")
        return

    vip_active = is_vip_active(player)
    if not vip_active:
        await update.message.reply_text("Seu VIP expirou. Ative novamente com /comprarvip")
        return

    plan = VIP_PLANS[player['vip_level']]
    remaining = vip_remaining_days(player)
    await update.message.reply_text(
        f"VIP {player['vip_level']} ativo\n"
        f"Ciclo restante: {remaining} dias\n"
        f"Rendimento diário: R${plan['daily_profit']:.2f}\n"
        f"Lucro pendente para coletar: R${player['pending_profit']:.2f}"
    )

async def alimentar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    init_player(user_id, update.effective_user.username)
    data = load_data()
    player = data[str(user_id)]

    if not is_vip_active(player):
        await update.message.reply_text("Você não possui VIP ativo para coletar rendimento.")
        return

    now = time.time()
    last = player['last_alimentar']
    if now - last < 86400:  # 24h
        wait = int((86400 - (now - last)) // 60)
        await update.message.reply_text(f"⏳ Você só pode coletar o rendimento uma vez a cada 24h. Aguarde {wait} minutos.")
        return

    plan = VIP_PLANS[player['vip_level']]
    player['pending_profit'] += plan['daily_profit']
    player['last_alimentar'] = now
    save_data(data)
    await update.message.reply_text(f"💰 Rendimento diário de R${plan['daily_profit']:.2f} adicionado ao seu lucro pendente.")

async def sacar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    init_player(user_id, update.effective_user.username)
    data = load_data()
    player = data[str(user_id)]

    min_saque = 5.0
    if player['pending_profit'] < min_saque:
        await update.message.reply_text(f"Você precisa de pelo menos R${min_saque:.2f} para solicitar saque.")
        return

    valor = player['pending_profit']
    player['pending_profit'] = 0.0
    player['total_sacado'] += valor

    # Aqui você deve implementar o sistema real de saque,
    # ex: enviar para API de pagamento ou manualmente processar

    save_data(data)
    await update.message.reply_text(f"✅ Pedido de saque de R${valor:.2f} registrado. Aguarde a confirmação.")

async def indicar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or ""
    data = load_data()

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
    data[str[user_id]]['coins'] += 20
    data[str[user_id]]['xp'] += 10
    data[str[user_id]]['invites'] += 1
    save_data(data)
    await update.message.reply_text(f"Você indicou @{indic_username}! 🎉 Você ganhou 20 ZPC e 10 XP.")

async def minhascomissoes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = load_data()
    player = data.get(str(user_id), {})

    comissoes = player.get('comissoes', 0.0)
    await update.message.reply_text(f"💰 Suas comissões acumuladas: R${comissoes:.2f}")

async def ranking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = load_data()
    sorted_players = sorted(data.items(), key=lambda x: x[1].get('coins', 0), reverse=True)
    top_10 = sorted_players[:10]

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

# Comandos admin

async def liberar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("Acesso negado.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("Uso: /liberar @usuario quantidade")
        return

    username = context.args[0].replace("@", "").lower()
    try:
        amount = int(context.args[1])
    except ValueError:
        await update.message.reply_text("Quantidade inválida.")
        return

    data = load_data()

    for uid, info in data.items():
        if info.get('username', "").lower() == username:
            data[uid]['coins'] += amount
            save_data(data)
            await update.message.reply_text(f"✅ Liberados {amount} ZPC para @{username}.")
            return

    await update.message.reply_text("Usuário não encontrado.")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("Acesso negado.")
        return

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
                'username': info.get('username', ""),
                'vip_level': 0,
                'vip_start': 0,
                'last_alimentar': 0,
                'pending_profit': 0.0,
                'total_sacado': 0.0,
                'comissoes': 0.0,
            }
            save_data(data)
            await update.message.reply_text(f"✅ Dados do @{username} foram resetados.")
            return

    await update.message.reply_text("Usuário não encontrado.")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("Acesso negado.")
        return

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

async def estatisticas(update: Update, context: ContextTypes.DEFAULT_TYPE
                       async def main():
    application = ApplicationBuilder().token(TOKEN).build()

    # Registrar handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("minerar", mine))
    application.add_handler(CommandHandler("perfil", perfil))
    application.add_handler(CommandHandler("comprarvip", comprarvip))
    application.add_handler(CommandHandler("ativarvip", ativarvip))
    application.add_handler(CommandHandler("vipstatus", vipstatus))
    application.add_handler(CommandHandler("alimentar", alimentar))
    application.add_handler(CommandHandler("sacar", sacar))
    application.add_handler(CommandHandler("indicar", indicar))
    application.add_handler(CommandHandler("minhascomissoes", minhascomissoes))
    application.add_handler(CommandHandler("ranking", ranking))

    # Admin commands
    application.add_handler(CommandHandler("liberar", liberar))
    application.add_handler(CommandHandler("reset", reset))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("estatisticas", estatisticas))

    # Atualizar menu de comandos no Telegram
    cmds = [
        BotCommand("start", "🚀 Iniciar o bot"),
        BotCommand("minerar", "⛏️ Minerar ZappCoins"),
        BotCommand("perfil", "👤 Ver seu perfil"),
        BotCommand("comprarvip", "💎 Ver planos VIP"),
        BotCommand("ativarvip", "🎯 Ativar plano VIP"),
        BotCommand("vipstatus", "📊 Ver status VIP"),
        BotCommand("alimentar", "💰 Coletar rendimento diário"),
        BotCommand("sacar", "📤 Solicitar saque"),
        BotCommand("indicar", "👥 Indicar outro jogador"),
        BotCommand("minhascomissoes", "💵 Ver comissões"),
        BotCommand("ranking", "🏆 Ver ranking global"),
        # Admin
        BotCommand("liberar", "🔓 Adicionar ZPC (admin)"),
        BotCommand("reset", "🔄 Resetar jogador (admin)"),
        BotCommand("broadcast", "📢 Mensagem global (admin)"),
        BotCommand("estatisticas", "📊 Dados do bot (admin)"),
    ]

    # Atualiza o menu no Telegram (garante que comandos estejam visíveis)
    await application.bot.set_my_commands(cmds)

    # Inicia o polling do bot (escutando mensagens)
    await application.run_polling()

if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except RuntimeError:
        # Se já existir loop rodando (ex: Replit)
        loop = asyncio.get_event_loop()
        loop.create_task(main())
        while True:
            time.sleep(1)
