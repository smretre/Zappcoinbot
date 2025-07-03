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
ADMIN_IDS = [6063904865]  # seu user_id admin

trophy_emojis = ["🥇", "🥈", "🥉"]

VIP_PLANS = {
    0: {"name": "VIP 0 (Grátis)", "price": 0, "days": 0, "daily_profit": 0.0, "multiplier": 1, "withdraw_min": 0},
    1: {"name": "VIP 1", "price": 10, "days": 7, "daily_profit": 0.50, "multiplier": 1, "withdraw_min": 10},
    2: {"name": "VIP 2", "price": 20, "days": 7, "daily_profit": 1.00, "multiplier": 2, "withdraw_min": 10},
    3: {"name": "VIP 3", "price": 40, "days": 7, "daily_profit": 2.00, "multiplier": 4, "withdraw_min": 10},
    4: {"name": "VIP 4", "price": 80, "days": 15, "daily_profit": 4.00, "multiplier": 8, "withdraw_min": 10},
    5: {"name": "VIP 5", "price": 160, "days": 15, "daily_profit": 8.00, "multiplier": 16, "withdraw_min": 10},
    6: {"name": "VIP 6", "price": 320, "days": 30, "daily_profit": 16.00, "multiplier": 32, "withdraw_min": 10},
    7: {"name": "VIP 7", "price": 640, "days": 30, "daily_profit": 32.00, "multiplier": 64, "withdraw_min": 10},
    8: {"name": "VIP 8", "price": 1280, "days": 30, "daily_profit": 64.00, "multiplier": 128, "withdraw_min": 10},
    9: {"name": "VIP 9", "price": 40, "days": 7, "daily_profit": 4.00, "multiplier": 4, "withdraw_min": 10},
}

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
    if str(user_id) not in data:
        data[str(user_id)] = {
            'coins': 0,
            'last_mine': 0,
            'xp': 0,
            'level': 1,
            'invited_by': None,
            'invites': 0,
            'username': username or "",
            'vip_plan': 0,
            'vip_start': 0,
            'vip_collected': False,
            'last_feed': 0,
            'balance_to_withdraw': 0.0,
        }
        save_data(data)
    else:
        if username:
            data[str(user_id)]['username'] = username
            save_data(data)

# Funções principais existentes...

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or ""
    init_player(user_id, username)

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
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            else:
                await update.message.reply_text("Código inválido ou você já foi indicado antes.")
                return
        else:
            await update.message.reply_text("Você não pode se indicar.")
            return

    await update.message.reply_text(
        """👋 Bem-vindo ao *Crypto Miner Bot*!

Use /minerar para minerar ZappCoins ⛏️
Use /perfil para ver seu progresso 💼
Use /comprar para adquirir mais moedas 💰
Use /comprarvip para ver planos VIP
Use /vipstatus para ver seu VIP
Use /alimentar para coletar rendimento diário do VIP
Use /sacar para sacar saldo disponível""",
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

    vip_plan = player.get('vip_plan', 0)
    multiplier = VIP_PLANS.get(vip_plan, {}).get('multiplier', 1)
    coins_earned = int((10 + player['level'] * 2) * multiplier)
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

    vip_plan = player.get('vip_plan', 0)
    vip_info = VIP_PLANS.get(vip_plan, {})
    vip_start = player.get('vip_start', 0)
    vip_days = vip_info.get('days', 0)
    vip_end = vip_start + vip_days * 86400
    now = time.time()
    vip_left = max(0, int((vip_end - now) / 86400))

    msg = (
        f"👤 Perfil de {update.effective_user.first_name}:\n\n"
        f"💰 ZappCoins: {player['coins']}\n"
        f"⭐ Nível: {player['level']}\n"
        f"✨ XP: {player['xp']}/{player['level'] * 20}\n"
        f"🎮 Convites: {player['invites']}\n"
        f"💎 VIP: {vip_info.get('name', 'Nenhum')} ({vip_left} dias restantes)\n"
        f"📤 Saldo para saque: R$ {player.get('balance_to_withdraw', 0):.2f}"
    )
    await update.message.reply_text(msg)

async def comprar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "💰 Comprar ZappCoins\n"
        "Escolha um dos pacotes abaixo e envie o valor para a chave PIX:\n"
        "🔹 500 ZPC – R$2,99\n"
        "🔸 1000 ZPC – R$4,99\n"
        "💎 2500 ZPC – R$9,99\n"
        "🔑 Chave PIX (aleatória): 5204f881-cbb8-4388-ac89-2eabeb390f58\n"
        "📤 Após o pagamento, envie o comprovante aqui mesmo no chat.\n"
        "⚠️ Assim que confirmado, você receberá as moedas manualmente!"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# VIP Functions

async def comprarvip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "💎 Planos VIP disponíveis:\n\n"
    for k, v in VIP_PLANS.items():
        if k == 0:
            continue
        msg += (f"{k} - {v['name']} - {v['days']} dias - R$ {v['price']:.2f} - Rendimento diário: R$ {v['daily_profit']:.2f} - "
                f"Multiplicador: x{v['multiplier']}\n")
    msg += "\nUse /ativarvip <número do plano> para ativar seu VIP."
    await update.message.reply_text(msg)

async def ativarvip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Use: /ativarvip <número do plano>")
        return
    try:
        plan_id = int(context.args[0])
    except:
        await update.message.reply_text("Número inválido.")
        return
    if plan_id not in VIP_PLANS or plan_id == 0:
        await update.message.reply_text("Plano inválido.")
        return

    data = load_data()
    player = data.get(str(user_id))
    if not player:
        await update.message.reply_text("Usuário não encontrado.")
        return

    vip_start = time.time()
    player['vip_plan'] = plan_id
    player['vip_start'] = vip_start
    player['vip_collected'] = False
    player['last_feed'] = 0
    save_data(data)

    await update.message.reply_text(f"VIP {VIP_PLANS[plan_id]['name']} ativado com sucesso!")

async def vipstatus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = load_data()
    player = data.get(str(user_id))
    if not player:
        await update.message.reply_text("Usuário não encontrado.")
        return

    vip_plan = player.get('vip_plan', 0)
    if vip_plan == 0:
        await update.message.reply_text("Você não possui VIP ativo.")
        return

    vip_info = VIP_PLANS.get(vip_plan)
    vip_start = player.get('vip_start', 0)
    vip_end = vip_start + vip_info['days'] * 86400
    now = time.time()

    if now > vip_end:
        await update.message.reply_text("Seu VIP expirou.")
        return

    days_left = int((vip_end - now) / 86400)
    await update.message.reply_text(
        f"VIP ativo: {vip_info['name']}\n"
        f"Dias restantes: {days_left}\n"
        f"Rendimento diário: R$ {vip_info['daily_profit']:.2f}\n"
        f"Multiplicador: x{vip_info['multiplier']}"
    )

async def alimentar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = load_data()
    player = data.get(str(user_id))
    if not player:
        await update.message.reply_text("Usuário não encontrado.")
        return

    vip_plan = player.get('vip_plan', 0)
    vip_info = VIP_PLANS.get(vip_plan, {})
    if vip_plan == 0:
        await update.message.reply_text("Você não possui VIP ativo para coletar rendimento.")
        return

    vip_start = player.get('vip_start', 0)
    vip_end = vip_start + vip_info.get('days', 0) * 86400
    now = time.time()

    if now > vip_end:
        await update.message.reply_text("Seu VIP expirou, compre um novo para continuar recebendo rendimento.")
        return

    last_feed = player.get('last_feed', 0)
    if now - last_feed < 86400:
        await update.message.reply_text("Você já coletou seu rendimento diário. Tente novamente amanhã.")
        return

    # Adiciona rendimento ao saldo de saque
    player['balance_to_withdraw'] = player.get('balance_to_withdraw', 0.0) + vip_info['daily_profit']
    player['last_feed'] = now
    save_data(data)

    await update.message.reply_text(
        f"💰 Você coletou R$ {vip_info['daily_profit']:.2f} de rendimento diário do seu VIP."
    )

async def sacar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = load_data()
    player = data.get(str(user_id))
    if not player:
        await update.message.reply_text("Usuário não encontrado.")
        return

    vip_plan = player.get('vip_plan', 0)
    vip_info = VIP_PLANS.get(vip_plan, {})
    balance = player.get('balance_to_withdraw', 0.0)
    min_withdraw = vip_info.get('withdraw_min', 10)

    if balance < min_withdraw:
        await update.message.reply_text(
            f"Saldo insuficiente para saque. O mínimo para saque é R$ {min_withdraw:.2f}. Seu saldo: R$ {balance:.2f}"
        )
        return

    # Aqui você pode adicionar integração com sistema de pagamento real

    player['balance_to_withdraw'] = 0.0
    save_data(data)

    await update.message.reply_text(
        f"✅ Pedido de saque de R$ {balance:.2f} recebido! Aguarde o processamento."
    )

# Comandos Admin

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
ADMIN_IDS = [6063904865]  # seu user_id admin

trophy_emojis = ["🥇", "🥈", "🥉"]

VIP_PLANS = {
    0: {"name": "VIP 0 (Grátis)", "price": 0, "days": 0, "daily_profit": 0.0, "multiplier": 1, "withdraw_min": 0},
    1: {"name": "VIP 1", "price": 10, "days": 7, "daily_profit": 0.50, "multiplier": 1, "withdraw_min": 10},
    2: {"name": "VIP 2", "price": 20, "days": 7, "daily_profit": 1.00, "multiplier": 2, "withdraw_min": 10},
    3: {"name": "VIP 3", "price": 40, "days": 7, "daily_profit": 2.00, "multiplier": 4, "withdraw_min": 10},
    4: {"name": "VIP 4", "price": 80, "days": 15, "daily_profit": 4.00, "multiplier": 8, "withdraw_min": 10},
    5: {"name": "VIP 5", "price": 160, "days": 15, "daily_profit": 8.00, "multiplier": 16, "withdraw_min": 10},
    6: {"name": "VIP 6", "price": 320, "days": 30, "daily_profit": 16.00, "multiplier": 32, "withdraw_min": 10},
    7: {"name": "VIP 7", "price": 640, "days": 30, "daily_profit": 32.00, "multiplier": 64, "withdraw_min": 10},
    8: {"name": "VIP 8", "price": 1280, "days": 30, "daily_profit": 64.00, "multiplier": 128, "withdraw_min": 10},
    9: {"name": "VIP 9", "price": 40, "days": 7, "daily_profit": 4.00, "multiplier": 4, "withdraw_min": 10},
}

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
    if str(user_id) not in data:
        data[str(user_id)] = {
            'coins': 0,
            'last_mine': 0,
            'xp': 0,
            'level': 1,
            'invited_by': None,
            'invites': 0,
            'username': username or "",
            'vip_plan': 0,
            'vip_start': 0,
            'vip_collected': False,
            'last_feed': 0,
            'balance_to_withdraw': 0.0,
        }
        save_data(data)
    else:
        if username:
            data[str(user_id)]['username'] = username
            save_data(data)

# Funções principais existentes...

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or ""
    init_player(user_id, username)

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
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            else:
                await update.message.reply_text("Código inválido ou você já foi indicado antes.")
                return
        else:
            await update.message.reply_text("Você não pode se indicar.")
            return

    await update.message.reply_text(
        """👋 Bem-vindo ao *Crypto Miner Bot*!

Use /minerar para minerar ZappCoins ⛏️
Use /perfil para ver seu progresso 💼
Use /comprar para adquirir mais moedas 💰
Use /comprarvip para ver planos VIP
Use /vipstatus para ver seu VIP
Use /alimentar para coletar rendimento diário do VIP
Use /sacar para sacar saldo disponível""",
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

    vip_plan = player.get('vip_plan', 0)
    multiplier = VIP_PLANS.get(vip_plan, {}).get('multiplier', 1)
    coins_earned = int((10 + player['level'] * 2) * multiplier)
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

    vip_plan = player.get('vip_plan', 0)
    vip_info = VIP_PLANS.get(vip_plan, {})
    vip_start = player.get('vip_start', 0)
    vip_days = vip_info.get('days', 0)
    vip_end = vip_start + vip_days * 86400
    now = time.time()
    vip_left = max(0, int((vip_end - now) / 86400))

    msg = (
        f"👤 Perfil de {update.effective_user.first_name}:\n\n"
        f"💰 ZappCoins: {player['coins']}\n"
        f"⭐ Nível: {player['level']}\n"
        f"✨ XP: {player['xp']}/{player['level'] * 20}\n"
        f"🎮 Convites: {player['invites']}\n"
        f"💎 VIP: {vip_info.get('name', 'Nenhum')} ({vip_left} dias restantes)\n"
        f"📤 Saldo para saque: R$ {player.get('balance_to_withdraw', 0):.2f}"
    )
    await update.message.reply_text(msg)

async def comprar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "💰 Comprar ZappCoins\n"
        "Escolha um dos pacotes abaixo e envie o valor para a chave PIX:\n"
        "🔹 500 ZPC – R$2,99\n"
        "🔸 1000 ZPC – R$4,99\n"
        "💎 2500 ZPC – R$9,99\n"
        "🔑 Chave PIX (aleatória): 5204f881-cbb8-4388-ac89-2eabeb390f58\n"
        "📤 Após o pagamento, envie o comprovante aqui mesmo no chat.\n"
        "⚠️ Assim que confirmado, você receberá as moedas manualmente!"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# VIP Functions

async def comprarvip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "💎 Planos VIP disponíveis:\n\n"
    for k, v in VIP_PLANS.items():
        if k == 0:
            continue
        msg += (f"{k} - {v['name']} - {v['days']} dias - R$ {v['price']:.2f} - Rendimento diário: R$ {v['daily_profit']:.2f} - "
                f"Multiplicador: x{v['multiplier']}\n")
    msg += "\nUse /ativarvip <número do plano> para ativar seu VIP."
    await update.message.reply_text(msg)

async def ativarvip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Use: /ativarvip <número do plano>")
        return
    try:
        plan_id = int(context.args[0])
    except:
        await update.message.reply_text("Número inválido.")
        return
    if plan_id not in VIP_PLANS or plan_id == 0:
        await update.message.reply_text("Plano inválido.")
        return

    data = load_data()
    player = data.get(str(user_id))
    if not player:
        await update.message.reply_text("Usuário não encontrado.")
        return

    vip_start = time.time()
    player['vip_plan'] = plan_id
    player['vip_start'] = vip_start
    player['vip_collected'] = False
    player['last_feed'] = 0
    save_data(data)

    await update.message.reply_text(f"VIP {VIP_PLANS[plan_id]['name']} ativado com sucesso!")

async def vipstatus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = load_data()
    player = data.get(str(user_id))
    if not player:
        await update.message.reply_text("Usuário não encontrado.")
        return

    vip_plan = player.get('vip_plan', 0)
    if vip_plan == 0:
        await update.message.reply_text("Você não possui VIP ativo.")
        return

    vip_info = VIP_PLANS.get(vip_plan)
    vip_start = player.get('vip_start', 0)
    vip_end = vip_start + vip_info['days'] * 86400
    now = time.time()

    if now > vip_end:
        await update.message.reply_text("Seu VIP expirou.")
        return

    days_left = int((vip_end - now) / 86400)
    await update.message.reply_text(
        f"VIP ativo: {vip_info['name']}\n"
        f"Dias restantes: {days_left}\n"
        f"Rendimento diário: R$ {vip_info['daily_profit']:.2f}\n"
        f"Multiplicador: x{vip_info['multiplier']}"
    )

async def alimentar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = load_data()
    player = data.get(str(user_id))
    if not player:
        await update.message.reply_text("Usuário não encontrado.")
        return

    vip_plan = player.get('vip_plan', 0)
    vip_info = VIP_PLANS.get(vip_plan, {})
    if vip_plan == 0:
        await update.message.reply_text("Você não possui VIP ativo para coletar rendimento.")
        return

    vip_start = player.get('vip_start', 0)
    vip_end = vip_start + vip_info.get('days', 0) * 86400
    now = time.time()

    if now > vip_end:
        await update.message.reply_text("Seu VIP expirou, compre um novo para continuar recebendo rendimento.")
        return

    last_feed = player.get('last_feed', 0)
    if now - last_feed < 86400:
        await update.message.reply_text("Você já coletou seu rendimento diário. Tente novamente amanhã.")
        return

    # Adiciona rendimento ao saldo de saque
    player['balance_to_withdraw'] = player.get('balance_to_withdraw', 0.0) + vip_info['daily_profit']
    player['last_feed'] = now
    save_data(data)

    await update.message.reply_text(
        f"💰 Você coletou R$ {vip_info['daily_profit']:.2f} de rendimento diário do seu VIP."
    )

async def sacar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = load_data()
    player = data.get(str(user_id))
    if not player:
        await update.message.reply_text("Usuário não encontrado.")
        return

    vip_plan = player.get('vip_plan', 0)
    vip_info = VIP_PLANS.get(vip_plan, {})
    balance = player.get('balance_to_withdraw', 0.0)
    min_withdraw = vip_info.get('withdraw_min', 10)

    if balance < min_withdraw:
        await update.message.reply_text(
            f"Saldo insuficiente para saque. O mínimo para saque é R$ {min_withdraw:.2f}. Seu saldo: R$ {balance:.2f}"
        )
        return

    # Aqui você pode adicionar integração com sistema de pagamento real

    player['balance_to_withdraw'] = 0.0
    save_data(data)

    await update.message.reply_text(
        f"✅ Pedido de saque de R$ {balance:.2f} recebido! Aguarde o processamento."
    )

# Comandos Admin

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
                'vip_plan': 0,
                'vip_start': 0,
                'vip_collected': False,
                'last_feed': 0,
                'balance_to_withdraw': 0.0,
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

async def estatisticas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("Acesso negado.")
        return

    data = load_data()
    total_users = len(data)
    total_coins = sum(info.get('coins', 0) for info in data.values())
    total_xp = sum(info.get('xp', 0) for info in data.values())

    msg = (
        f"*Estatísticas do Bot*\n\n"
        f"👥 Total de usuários: {total_users}\n"
        f"💰 Total de ZappCoins em circulação: {total_coins}\n"
        f"⭐ Total de XP acumulado: {total_xp}\n"
    )
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

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

    if data.get(str(user_id), {}).get('invited_by') is not None:
        await update.message.reply_text("Você já foi indicado por alguém.")
        return

    data[str(user_id)]['invited_by'] = indic_id
    data[str(indic_id)]['coins'] += 20
    data[str(indic_id)]['xp'] += 10
    data[str(indic_id)]['invites'] += 1
    save_data(data)
    await update.message.reply_text(f"Você foi indicado por @{indic_username}! 🎉 Eles ganharam 20 ZPC e 10 XP.")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Comandos principais
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("minerar", mine))
    app.add_handler(CommandHandler("perfil", perfil))
    app.add_handler(CommandHandler("comprar", comprar))

    # VIP
    app.add_handler(CommandHandler("comprarvip", comprarvip))
    app.add_handler(CommandHandler("ativarvip", ativarvip))
    app.add_handler(CommandHandler("vipstatus", vipstatus))
    app.add_handler(CommandHandler("alimentar", alimentar))
    app.add_handler(CommandHandler("sacar", sacar))

    # Administração
    app.add_handler(CommandHandler("liberar", liberar))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("estatisticas", estatisticas))

    # Ranking e indicação
    app.add_handler(CommandHandler("ranking", ranking))
    app.add_handler(CommandHandler("indicar", indicar))

    print("Bot iniciado...")
    app.run_polling()

if __name__ == "__main__":
    main()
