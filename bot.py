import logging import time import json import asyncio import os from telegram import Update, BotCommand from telegram.constants import ParseMode from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

Configuração do log

logging.basicConfig( format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO )

TOKEN = "7578757304:AAGGvhz7cSkpga36bgfy7COrUD8PRrzorKw" DATA_FILE = 'userdata.json' COOLDOWN_TIME = 600  # 10 minutos ADMIN_IDS = [6063904865]  # seu user_id admin

VIP_PLANOS = { 0: {"multiplicador": 1, "dias": 0, "preco": 0, "saque_diario": 0}, 1: {"multiplicador": 3, "dias": 3, "preco": 2.99, "saque_diario": 0.10}, 2: {"multiplicador": 6, "dias": 7, "preco": 5.99, "saque_diario": 0.50}, 3: {"multiplicador": 12, "dias": 15, "preco": 10.99, "saque_diario": 1.20}, 4: {"multiplicador": 24, "dias": 30, "preco": 18.99, "saque_diario": 2.80}, 5: {"multiplicador": 48, "dias": 60, "preco": 29.99, "saque_diario": 5.99}, 6: {"multiplicador": 96, "dias": 90, "preco": 49.99, "saque_diario": 10.00}, 7: {"multiplicador": 192, "dias": 180, "preco": 79.99, "saque_diario": 25.00}, 8: {"multiplicador": 384, "dias": 270, "preco": 129.99, "saque_diario": 50.00}, 9: {"multiplicador": 768, "dias": 360, "preco": 199.99, "saque_diario": 100.00}, 10: {"multiplicador": 1536, "dias": 999, "preco": 349.99, "saque_diario": 200.00}, }

COMISSAO_POR_INDICACAO = 0.10  # 10%

trophy_emojis = ["\U0001F947", "\U0001F948", "\U0001F949"]

Utils

def load_data(): try: with open(DATA_FILE, 'r') as f: return json.load(f) except FileNotFoundError: with open(DATA_FILE, 'w') as f: json.dump({}, f) return {} except Exception as e: print(f"[ERRO] Falha ao carregar dados: {e}") return {}

def save_data(data): try: with open(DATA_FILE, 'w') as f: json.dump(data, f) except Exception as e: print(f"[ERRO] Falha ao salvar dados: {e}")

def init_player(user_id, username=None): data = load_data() if str(user_id) not in data: data[str(user_id)] = { 'coins': 0, 'last_mine': 0, 'xp': 0, 'level': 1, 'invited_by': None, 'invites': 0, 'username': username or "", 'vip': 0, 'vip_start': 0, 'saldo_saque': 0.0, 'total_recebido': 0.0, 'comissao': 0.0 } else: if username: data[str(user_id)]['username'] = username save_data(data)

Comandos novos de VIP e Rendimento

async def comprarvip(update: Update, context: ContextTypes.DEFAULT_TYPE): mensagem = "\n\n\U0001F4B8 Planos VIP Disponíveis:\n" for nivel, plano in VIP_PLANOS.items(): if nivel == 0: continue mensagem += ( f"\n\U0001F451 VIP {nivel} — {plano['dias']} dias\n" f"Multiplicador de mineração: x{plano['multiplicador']}\n" f"Saque diário: R$ {plano['saque_diario']:.2f}\n" f"Preço: R$ {plano['preco']:.2f}\n" ) mensagem += ("\nPara ativar, envie o valor via PIX: 5204f881-cbb8-4388-ac89-2eabeb390f58\n" "Após o pagamento, envie o comprovante aqui mesmo para ativação manual.") await update.message.reply_text(mensagem, parse_mode=ParseMode.MARKDOWN)

async def vipstatus(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = str(update.effective_user.id) data = load_data() p = data.get(user_id) if not p: await update.message.reply_text("Usuário não encontrado.") return

vip = p.get('vip', 0)
start = p.get('vip_start', 0)
dias = VIP_PLANOS[vip]['dias']
restante = max(0, int((start + dias * 86400 - time.time()) / 86400)) if vip > 0 else 0

msg = f"\U0001F451 Seu VIP atual é: VIP {vip}\n"
msg += f"⏳ Dias restantes: {restante} dia(s)\n"
msg += f"\U0001F4B0 Saque diário: R$ {VIP_PLANOS[vip]['saque_diario']:.2f}\n"
msg += f"\nSaldo disponível para saque: R$ {p.get('saldo_saque', 0.0):.2f}"
await update.message.reply_text(msg)

async def alimentar(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = str(update.effective_user.id) data = load_data() p = data.get(user_id) if not p: await update.message.reply_text("Usuário não encontrado.") return

vip = p.get('vip', 0)
if vip == 0:
    await update.message.reply_text("Você precisa ser VIP para gerar rendimento.")
    return

ultimo = p.get('last_rendimento', 0)
if time.time() - ultimo < 86400:
    await update.message.reply_text("⏳ Você já recebeu seu rendimento hoje. Tente amanhã.")
    return

p['saldo_saque'] += VIP_PLANOS[vip]['saque_diario']
p['last_rendimento'] = time.time()
save_data(data)
await update.message.reply_text(f"✅ Rendimento diário adicionado: R$ {VIP_PLANOS[vip]['saque_diario']:.2f}")

async def sacar(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = str(update.effective_user.id) data = load_data() p = data.get(user_id) saldo = p.get('saldo_saque', 0.0)

if saldo < 0.50:
    await update.message.reply_text("O saque mínimo é de R$ 0,50. Junte mais rendimento.")
    return

await update.message.reply_text(f"Para sacar R$ {saldo:.2f}, envie sua chave PIX aqui no chat. Após isso, o pagamento será feito manualmente!")

async def minhascomissoes(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = str(update.effective_user.id) data = load_data() comissao = data[user_id].get('comissao', 0.0) await update.message.reply_text(f"💼 Sua comissão acumulada por indicações: R$ {comissao:.2f}")

main()

async def main(): application = ApplicationBuilder().token(TOKEN).build()

application.add_handler(CommandHandler("comprarvip", comprarvip))
application.add_handler(CommandHandler("vipstatus", vipstatus))
application.add_handler(CommandHandler("alimentar", alimentar))
application.add_handler(CommandHandler("sacar", sacar))
application.add_handler(CommandHandler("minhascomissoes", minhascomissoes))

# (comandos anteriores continuam)

await application.bot.set_my_commands([
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
await application.run_polling()

if name == "main": try: loop = asyncio.get_event_loop() loop.run_until_complete(main()) except RuntimeError: asyncio.create_task(main()) while True: time.sleep(1) except Exception as e: print(f"Erro inesperado: {e}")

