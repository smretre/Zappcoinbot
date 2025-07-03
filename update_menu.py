import asyncio
from telegram import Bot, BotCommand
from telegram.error import TelegramError

TOKEN = "7578757304:AAGGvhz7cSkpga36bgfy7COrUD8PRrzorKw"  # Seu token aqui

# Lista de comandos desejados
COMMANDS = [
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
]

async def update_bot_commands():
    try:
        bot = Bot(token=TOKEN)

        # Atualiza o menu de comandos
        await bot.set_my_commands(COMMANDS)
        print("✅ Comandos atualizados com sucesso no menu do bot!")

        # Confirma os comandos aplicados
        current = await bot.get_my_commands()
        print("📋 Lista de comandos configurados:")
        for cmd in current:
            print(f"➤ /{cmd.command} – {cmd.description}")

    except TelegramError as e:
        print(f"❌ Erro ao atualizar menu: {e}")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

if __name__ == "__main__":
    asyncio.run(update_bot_commands())
