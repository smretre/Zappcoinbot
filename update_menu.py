import asyncio
from telegram import Bot, BotCommand

# Token do bot (mesmo do bot.py)
BOT_TOKEN = '7578757304:AAGGvhz7cSkpga36bgfy7COrUD8PRrzorKw'

async def update_bot_commands():
    """Atualiza o menu de comandos do bot no Telegram"""
    bot = Bot(token=BOT_TOKEN)
    await bot.set_my_commands([
        BotCommand("start", "Iniciar o bot"),
        BotCommand("minerar", "Minerar ZappCoins"),
        BotCommand("perfil", "Ver seu perfil"),
        BotCommand("comprarvip", "Ver planos VIP"),
        BotCommand("vipstatus", "Seu VIP e rendimento"),
        BotCommand("alimentar", "Coletar rendimento diário"),
        BotCommand("sacar", "Solicitar saque"),
        BotCommand("indicar", "Indicar outro jogador"),
        BotCommand("minhascomissoes", "Ver comissões"),
        BotCommand("ranking", "Ver ranking global"),
        BotCommand("liberar", "Adicionar ZPC a jogador (admin)"),
        BotCommand("reset", "Resetar jogador (admin)"),
        BotCommand("broadcast", "Mensagem global (admin)"),
        BotCommand("estatisticas", "Dados do bot (admin)"),
    ])
    print("✅ Comandos atualizados com sucesso no menu do bot!")

def main():
    """Função principal para executar a atualização"""
    asyncio.run(update_bot_commands())

if __name__ == "__main__":
    main()
