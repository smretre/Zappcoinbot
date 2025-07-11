import os
import pathlib

for pycache in pathlib.Path('.').rglob('__pycache__'):
    for file in pycache.glob('*.pyc'):
        try:
            file.unlink()
        except Exception as e:
            print(f"Erro ao deletar {file}: {e}")
import logging
import time
import json
import asyncio
import nest_asyncio
nest_asyncio.apply()
from telegram import Update, BotCommand
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Configuração do log
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

TOKEN = "7578757304:AAGGvhz7cSkpga36bgfy7COrUD8PRrzorKw"
DATA_FILE = "userdata.json"
COOLDOWN_TIME = 600  # 10 minutos
ADMIN_IDS = [6063904865]

VIP_TIERS = {
    0: {"name": "VIP 0 (Grátis)", "multiplier": 1, "days": 0, "price": 0, "withdraw": 0},
    1: {"name": "VIP 1", "multiplier": 3, "days": 7, "price": 10, "withdraw": 0.50},
    2: {"name": "VIP 2", "multiplier": 6, "days": 15, "price": 20, "withdraw": 1.00},
    3: {"name": "VIP 3", "multiplier": 12, "days": 15, "price": 40, "withdraw": 2.00},
    4: {"name": "VIP 4", "multiplier": 24, "days": 15, "price": 80, "withdraw": 4.00},
    5: {"name": "VIP 5", "multiplier": 48, "days": 30, "price": 160, "withdraw": 8.00},
    6: {"name": "VIP 6", "multiplier": 96, "days": 30, "price": 320, "withdraw": 16.00},
    7: {"name": "VIP 7", "multiplier": 192, "days": 30, "price": 640, "withdraw": 32.00},
    8: {"name": "VIP 8", "multiplier": 384, "days": 30, "price": 1280, "withdraw": 64.00},
    9: {"name": "VIP 9", "multiplier": 768, "days": 60, "price": 2560, "withdraw": 128.00},
    10: {"name": "VIP 10", "multiplier": 1536, "days": 60, "price": 5120, "withdraw": 256.00}
}

COMMISSION_PERCENT = 10
trophy_emojis = ["🥇", "🥈", "🥉"]

# Utilitários
def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

def init_player(user_id, username=""):
    data = load_data()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {
            "coins": 0,
            "xp": 0,
            "level": 1,
            "username": username,
            "vip": 0,
            "vip_start": 0,
            "profit": 0.0,
            "last_mine": 0,
            "last_alimentar": 0,
            "invited_by": None,
            "invites": 0,
            "comissoes": 0.0,
            "total_sacado": 0.0
        }
    elif username:
        data[uid]["username"] = username
    save_data(data)

def is_vip_active(player):
    if player["vip"] == 0:
        return False
    return (time.time() - player["vip_start"]) < VIP_TIERS[player["vip"]]["days"] * 86400

def vip_remaining_days(player):
    if not is_vip_active(player):
        return 0
    restante = VIP_TIERS[player["vip"]]["days"] * 86400 - (time.time() - player["vip_start"])
    return int(restante // 86400)

# Comandos principais
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    username = update.effective_user.username or ""
    init_player(uid, username)
    await update.message.reply_text("""👋 Bem-vindo ao Crypto Miner Bot!
Use /minerar para começar.""")

async def mine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    init_player(uid)
    data = load_data()
    player = data[uid]

    if time.time() - player["last_mine"] < COOLDOWN_TIME:
        wait = int(COOLDOWN_TIME - (time.time() - player["last_mine"]))
        await update.message.reply_text(f"⏳ Aguarde {wait}s para minerar novamente.")
        return

    base = 10 + player["level"] * 2
    mult = VIP_TIERS[player["vip"]]["multiplier"]
    ganho = base * mult

    player["coins"] += ganho
    player["last_mine"] = time.time()
    player["xp"] += 5
    if player["xp"] >= player["level"] * 20:
        player["xp"] = 0
        player["level"] += 1
        await update.message.reply_text(f"🏆 Você subiu para o nível {player['level']}!")
    save_data(data)
    await update.message.reply_text(f"⛏️ Você minerou {ganho} ZPC!")

async def perfil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    data = load_data()
    player = data.get(uid, {})
    vip = VIP_TIERS.get(player.get("vip", 0), {})
    dias = vip_remaining_days(player)

    msg = (
        f"👤 *Perfil!*\n"
        f"ZPC: {player.get('coins', 0)}\n"
        f"Nível: {player.get('level', 1)}\n"
        f"XP: {player.get('xp', 0)}\n"
        f"VIP: {vip.get('name')} ({dias} dias restantes)\n"
        f"Lucro: R${player.get('profit', 0.0):.2f}\n"
        f"🆔 ID: `{uid}`"
    )

    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

# Novos comandos VIP
async def comprarvip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "💎 *Planos VIP:*\n"
    for i in VIP_TIERS:
        if i == 0:
            continue
        tier = VIP_TIERS[i]
        msg += f"{tier['name']} - R${tier['price']} - {tier['days']} dias - R${tier['withdraw']}/dia\n"
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

async def ativarvipadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return await update.message.reply_text("Acesso negado.")

    if len(context.args) != 2:
        return await update.message.reply_text("Uso: /ativarvipadmin <user_id> <nível>")

    uid = str(context.args[0])
    nivel = int(context.args[1])

    if nivel not in VIP_TIERS:
        return await update.message.reply_text("Nível VIP inválido.")

    data = load_data()
    if uid not in data:
        return await update.message.reply_text("Usuário não encontrado.")

    player = data[uid]
    player["vip"] = nivel
    player["vip_start"] = time.time()
    save_data(data)

    await update.message.reply_text(f"✅ VIP {nivel} ativado para ID {uid}.")
    
async def alimentar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    data = load_data()
    player = data[uid]
    if not is_vip_active(player):
        return await update.message.reply_text("Nenhum VIP ativo.")
    if time.time() - player["last_alimentar"] < 86400:
        return await update.message.reply_text("Espere 24h para coletar novamente.")
    lucro = VIP_TIERS[player["vip"]]["withdraw"]
    player["profit"] += lucro
    player["last_alimentar"] = time.time()
    save_data(data)
    await update.message.reply_text(f"💰 R${lucro:.2f} coletado!")

async def sacar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    init_player(uid)
    data = load_data()
    player = data[uid]
    if player["profit"] < 10:
        return await update.message.reply_text("Valor mínimo para saque: R$10")
    valor = player["profit"]
    player["profit"] = 0
    player["total_sacado"] += valor
    save_data(data)
    await update.message.reply_text(f"✅ Pedido de saque de R${valor:.2f} registrado.")

async def minhascomissoes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    data = load_data()
    player = data[uid]
    com = player.get("comissoes", 0.0)
    await update.message.reply_text(f"💸 Comissões acumuladas: R${com:.2f}")


# Funções adicionais: ranking, indicação e admin

async def ranking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    data = load_data()
    top = sorted(data.items(), key=lambda x: x[1].get("coins", 0), reverse=True)[:10]
    msg = "🏆 *Top 10 ZappCoin Miners* 🏆\n\n"
    for idx, (uid, p) in enumerate(top, start=1):
        name = p.get("username", f"User{uid}")
        coins = p.get("coins", 0)
        emoji = trophy_emojis[idx - 1] if idx <= 3 else f"{idx}."
        msg += f"{emoji} @{name} — {coins} ZPC\n"
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

async def indicar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    username = update.effective_user.username or ""
    data = load_data()
    if not context.args:
        return await update.message.reply_text("Uso: /indicar @usuario")

    indic = context.args[0].replace("@", "").lower()
    for other_uid, player in data.items():
        if player.get("username", "").lower() == indic:
            if data[other_uid].get("invited_by") is not None:
                return await update.message.reply_text("Este usuário já foi indicado.")
            data[other_uid]["invited_by"] = uid
            comissao = VIP_TIERS[data[other_uid]["vip"]]["price"] * COMMISSION_PERCENT / 100
            data[uid]["comissoes"] += comissao
            save_data(data)
            return await update.message.reply_text(f"🎉 Você indicou @{indic} e ganhou R${comissao:.2f} de comissão!")
    await update.message.reply_text("Usuário não encontrado.")

async def liberar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return await update.message.reply_text("Acesso negado.")
    if len(context.args) != 2:
        return await update.message.reply_text("Uso: /liberar @usuario quantidade")
    nome = context.args[0].replace("@", "").lower()
    valor = int(context.args[1])
    data = load_data()
    for uid, p in data.items():
        if p.get("username", "").lower() == nome:
            p["coins"] += valor
            save_data(data)
            return await update.message.reply_text(f"✅ {valor} ZPC enviados para @{nome}")
    await update.message.reply_text("Usuário não encontrado.")


# Inicialização
async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("minerar", mine))
    app.add_handler(CommandHandler("perfil", perfil))
    app.add_handler(CommandHandler("comprarvip", comprarvip))
    app.add_handler(CommandHandler("ativarvipadmin", ativarvipadmin))
    app.add_handler(CommandHandler("vipstatus", perfil))
    app.add_handler(CommandHandler("alimentar", alimentar))
    app.add_handler(CommandHandler("sacar", sacar))
    app.add_handler(CommandHandler("minhascomissoes", minhascomissoes))
    app.add_handler(CommandHandler("ranking", ranking))
    app.add_handler(CommandHandler("indicar", indicar))
    app.add_handler(CommandHandler("liberar", liberar))
    app.add_handler(CommandHandler("comprarvipnivel", comprarvipnivel))

    comandos = [
        BotCommand("start", "Iniciar"),
        BotCommand("minerar", "Minerar ZPC"),
        BotCommand("perfil", "Seu perfil"),
        BotCommand("comprarvip", "Ver planos VIP"),
        BotCommand("ativarvipadmin", "Ativar VIP"),
        BotCommand("vipstatus", "Status VIP"),
        BotCommand("alimentar", "Coletar rendimento diário"),
        BotCommand("sacar", "Solicitar saque"),
        BotCommand("minhascomissoes", "Ver comissões"),
        BotCommand("ranking", "Ranking global"),
        BotCommand("indicar", "Indicar amigo"),
        BotCommand("liberar", "Liberar ZPC (admin)"),
        BotCommand("comprarvipnivel", "Comprar VIP com pagamento PIX")
    ]
import logging
import time
import json
import asyncio
from telegram import Update, BotCommand
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Configuração do log
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

TOKEN = "7578757304:AAGGvhz7cSkpga36bgfy7COrUD8PRrzorKw"
DATA_FILE = "userdata.json"
COOLDOWN_TIME = 600  # 10 minutos
ADMIN_IDS = [6063904865]

VIP_TIERS = {
    0: {"name": "VIP 0 (Grátis)", "multiplier": 1, "days": 0, "price": 0, "withdraw": 0},
    1: {"name": "VIP 1", "multiplier": 3, "days": 7, "price": 10, "withdraw": 0.50},
    2: {"name": "VIP 2", "multiplier": 6, "days": 15, "price": 20, "withdraw": 1.00},
    3: {"name": "VIP 3", "multiplier": 12, "days": 15, "price": 40, "withdraw": 2.00},
    4: {"name": "VIP 4", "multiplier": 24, "days": 15, "price": 80, "withdraw": 4.00},
    5: {"name": "VIP 5", "multiplier": 48, "days": 30, "price": 160, "withdraw": 8.00},
    6: {"name": "VIP 6", "multiplier": 96, "days": 30, "price": 320, "withdraw": 16.00},
    7: {"name": "VIP 7", "multiplier": 192, "days": 30, "price": 640, "withdraw": 32.00},
    8: {"name": "VIP 8", "multiplier": 384, "days": 30, "price": 1280, "withdraw": 64.00},
    9: {"name": "VIP 9", "multiplier": 768, "days": 60, "price": 2560, "withdraw": 128.00},
    10: {"name": "VIP 10", "multiplier": 1536, "days": 60, "price": 5120, "withdraw": 256.00}
}

COMMISSION_PERCENT = 10
trophy_emojis = ["🥇", "🥈", "🥉"]

# Utilitários
def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

def init_player(user_id, username=""):
    data = load_data()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {
            "coins": 0,
            "xp": 0,
            "level": 1,
            "username": username,
            "vip": 0,
            "vip_start": 0,
            "profit": 0.0,
            "last_mine": 0,
            "last_alimentar": 0,
            "invited_by": None,
            "invites": 0,
            "comissoes": 0.0,
            "total_sacado": 0.0
        }
    elif username:
        data[uid]["username"] = username
    save_data(data)

def is_vip_active(player):
    if player["vip"] == 0:
        return False
    return (time.time() - player["vip_start"]) < VIP_TIERS[player["vip"]]["days"] * 86400

def vip_remaining_days(player):
    if not is_vip_active(player):
        return 0
    restante = VIP_TIERS[player["vip"]]["days"] * 86400 - (time.time() - player["vip_start"])
    return int(restante // 86400)

# Comandos principais
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    username = update.effective_user.username or ""
    init_player(uid, username)
    await update.message.reply_text("""👋 Bem-vindo ao Crypto Miner Bot!
Use /minerar para começar.""")

async def mine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    init_player(uid)
    data = load_data()
    player = data[uid]

    if time.time() - player["last_mine"] < COOLDOWN_TIME:
        wait = int(COOLDOWN_TIME - (time.time() - player["last_mine"]))
        await update.message.reply_text(f"⏳ Aguarde {wait}s para minerar novamente.")
        return

    base = 10 + player["level"] * 2
    mult = VIP_TIERS[player["vip"]]["multiplier"]
    ganho = base * mult

    player["coins"] += ganho
    player["last_mine"] = time.time()
    player["xp"] += 5
    if player["xp"] >= player["level"] * 20:
        player["xp"] = 0
        player["level"] += 1
        await update.message.reply_text(f"🏆 Você subiu para o nível {player['level']}!")
    save_data(data)
    await update.message.reply_text(f"⛏️ Você minerou {ganho} ZPC!")

async def perfil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    data = load_data()
    player = data.get(uid, {})
    vip = VIP_TIERS.get(player.get("vip", 0), {})
    dias = vip_remaining_days(player)

    msg = (
        f"👤 *Perfil*\n"
        f"ZPC: {player.get('coins', 0)}\n"
        f"Nível: {player.get('level', 1)}\n"
        f"XP: {player.get('xp', 0)}\n"
        f"VIP: {vip.get('name')} ({dias} dias restantes)\n"
        f"Lucro: R${player.get('profit', 0.0):.2f}\n"
        f"🆔 ID: `{uid}`"
    )

    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

# Novos comandos VIP
async def comprarvipnivel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("Uso: /comprarvipnivel <nível>")
    nivel = int(context.args[0])
    if nivel not in VIP_TIERS:
        return await update.message.reply_text("Plano inválido.")

    tier = VIP_TIERS[nivel]
    msg = (
    f"💎 *Compra do {tier['name']}*\n"
    f"🔹 Preço: R${tier['price']}\n"
    f"🔑 Chave PIX para pagamento:\n`{{5204f881-cbb8-4388-ac89-2eabeb390f58}}`\n\n"
    "Após o pagamento, envie o comprovante ao administrador.\n"
    "Quando confirmado, use /ativarvip <nível> para ativar seu plano."
)
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
    
async def ativarvipadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return await update.message.reply_text("Acesso negado.")

    if len(context.args) != 2:
        return await update.message.reply_text("Uso: /ativarvipadmin <user_id> <nível>")

    uid = str(context.args[0])
    nivel = int(context.args[1])

    if nivel not in VIP_TIERS:
        return await update.message.reply_text("Nível VIP inválido.")

    data = load_data()
    if uid not in data:
        return await update.message.reply_text("Usuário não encontrado.")

    player = data[uid]
    player["vip"] = nivel
    player["vip_start"] = time.time()
    save_data(data)

    await update.message.reply_text(f"✅ VIP {nivel} ativado para ID {uid}.")   

async def alimentar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    data = load_data()
    player = data[uid]
    if not is_vip_active(player):
        return await update.message.reply_text("Nenhum VIP ativo.")
    if time.time() - player["last_alimentar"] < 86400:
        return await update.message.reply_text("Espere 24h para coletar novamente.")
    lucro = VIP_TIERS[player["vip"]]["withdraw"]
    player["profit"] += lucro
    player["last_alimentar"] = time.time()
    save_data(data)
    await update.message.reply_text(f"💰 R${lucro:.2f} coletado!")

async def sacar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    init_player(uid)
    data = load_data()
    player = data[uid]

    if player["profit"] < 10:
        return await update.message.reply_text("Valor mínimo para saque: R$10")

    if not context.args:
        return await update.message.reply_text("Por favor, envie sua chave PIX junto. Exemplo:\n/sacar SUA_CHAVE_PIX")

    chave_pix_usuario = " ".join(context.args)

    valor = player["profit"]
    player["profit"] = 0
    player["total_sacado"] += valor
    save_data(data)

    await update.message.reply_text(
        f"✅ Pedido de saque registrado.\n"
        f"💰 Valor: R${valor:.2f}\n"
        f"🔑 Chave PIX: {chave_pix_usuario}\n"
        f"Seu pagamento será processado em breve."
    )

async def minhascomissoes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    data = load_data()
    player = data[uid]
    com = player.get("comissoes", 0.0)
    await update.message.reply_text(f"💸 Comissões acumuladas: R${com:.2f}")


# Funções adicionais: ranking, indicação e admin

async def ranking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    data = load_data()
    top = sorted(data.items(), key=lambda x: x[1].get("coins", 0), reverse=True)[:10]
    msg = "🏆 *Top 10 ZappCoin Miners* 🏆\n\n"
    for idx, (uid, p) in enumerate(top, start=1):
        name = p.get("username", f"User{uid}")
        coins = p.get("coins", 0)
        emoji = trophy_emojis[idx - 1] if idx <= 3 else f"{idx}."
        msg += f"{emoji} @{name} — {coins} ZPC\n"
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

async def indicar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    username = update.effective_user.username or ""
    data = load_data()
    if not context.args:
        return await update.message.reply_text("Uso: /indicar @usuario")

    indic = context.args[0].replace("@", "").lower()
    for other_uid, player in data.items():
        if player.get("username", "").lower() == indic:
            if data[other_uid].get("invited_by") is not None:
                return await update.message.reply_text("Este usuário já foi indicado.")
            data[other_uid]["invited_by"] = uid
            comissao = VIP_TIERS[data[other_uid]["vip"]]["price"] * COMMISSION_PERCENT / 100
            data[uid]["comissoes"] += comissao
            save_data(data)
            return await update.message.reply_text(f"🎉 Você indicou @{indic} e ganhou R${comissao:.2f} de comissão!")
    await update.message.reply_text("Usuário não encontrado.")

async def liberar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return await update.message.reply_text("Acesso negado.")
    if len(context.args) != 2:
        return await update.message.reply_text("Uso: /liberar @usuario quantidade")
    nome = context.args[0].replace("@", "").lower()
    valor = int(context.args[1])
    data = load_data()
    for uid, p in data.items():
        if p.get("username", "").lower() == nome:
            p["coins"] += valor
            save_data(data)
            return await update.message.reply_text(f"✅ {valor} ZPC enviados para @{nome}")
    await update.message.reply_text("Usuário não encontrado.")


# Inicialização
async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("minerar", mine))
    app.add_handler(CommandHandler("perfil", perfil))
    app.add_handler(CommandHandler("comprarvip", comprarvip))
    app.add_handler(CommandHandler("ativarvipadmin", ativarvipadmin))
    app.add_handler(CommandHandler("vipstatus", perfil))
    app.add_handler(CommandHandler("alimentar", alimentar))
    app.add_handler(CommandHandler("sacar", sacar))
    app.add_handler(CommandHandler("minhascomissoes", minhascomissoes))
    app.add_handler(CommandHandler("ranking", ranking))
    app.add_handler(CommandHandler("indicar", indicar))
    app.add_handler(CommandHandler("liberar", liberar))
    app.add_handler(CommandHandler("comprarvipnivel", comprarvipnivel))

    comandos = [
        BotCommand("start", "Iniciar"),
        BotCommand("minerar", "Minerar ZPC"),
        BotCommand("perfil", "Seu perfil"),
        BotCommand("comprarvip", "Ver planos VIP"),
        BotCommand("ativarvipadmin", "Ativar VIP"),
        BotCommand("vipstatus", "Status VIP"),
        BotCommand("alimentar", "Coletar rendimento diário"),
        BotCommand("sacar", "Solicitar saque"),
        BotCommand("minhascomissoes", "Ver comissões"),
        BotCommand("ranking", "Ranking global"),
        BotCommand("indicar", "Indicar amigo"),
        BotCommand("liberar", "Liberar ZPC (admin)"),
        BotCommand("comprarvipnivel", "Comprar VIP com pagamento PIX")
    ]
    await app.bot.set_my_commands(comandos)
    await app.run_polling()
if __name__ == "__main__":
    asyncio.run(main())
