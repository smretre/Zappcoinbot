import logging
import time
import json
import asyncio
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
ADMIN_IDS = [6063904865]  # Substitua pelo seu ID de admin

trophy_emojis = ["🥇", "🥈", "🥉"]

# Planos VIP
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

# IMPORTANTE: aqui devem entrar todas as suas funções definidas antes: load_data(), save_data(), start(), minerar(), etc.

# Exemplo da função estatísticas (só para fechar o código com lógica)
async def estatisticas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    total_users = len(data)
    total_coins = sum(player.get('coins', 0) for player in data.values())
    await update.message.reply_text(
        f"📊 Estatísticas:\n\n👥 Usuários: {total_users}\n💰 Total de ZappCoins: {total_coins}"
    )

# Função principal do bot
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

    # Comandos Admin
    application.add_handler(CommandHandler("liberar", liberar))
    application.add_handler(CommandHandler("reset", reset))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("estatisticas", estatisticas))

    # Atualizar menu do bot
    cmds = [
        BotCommand("start", "🚀 Iniciar o bot"),
        BotCommand("minerar", "⛏️ Minerar ZappCoins"),
        BotCommand("perfil", "👤 Ver seu perfil"),
        BotCommand("comprarvip", "💎 Ver planos VIP"),
        BotCommand("ativarvip", "🎯 Ativar plano VIP"),
        BotCommand("vipstatus", "📊 Ver status VIP"),
        BotCommand("alimentar", "💰 Coletar rendimento diário"),
        BotCommand("sacar", "📄 Solicitar saque"),
        BotCommand("indicar", "👥 Indicar outro jogador"),
        BotCommand("minhascomissoes", "💵 Ver comissões"),
        BotCommand("ranking", "🏆 Ver ranking global"),
        BotCommand("liberar", "🔓 Adicionar ZPC (admin)"),
        BotCommand("reset", "🔄 Resetar jogador (admin)"),
        BotCommand("broadcast", "📢 Mensagem global (admin)"),
        BotCommand("estatisticas", "📊 Dados do bot (admin)"),
    ]
    await application.bot.set_my_commands(cmds)

    # Iniciar polling do bot
    await application.run_polling()

# Executar
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError:
        loop = asyncio.get_event_loop()
        loop.create_task(main())
        while True:
            time.sleep(1)
