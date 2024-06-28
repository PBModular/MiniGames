from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from base.module import BaseModule, command, allowed_for, callback_query
from base.mod_ext import ModuleExtension

class TicTacToeExtension(ModuleExtension):
    def on_init(self):
        self.games = {}

    @command("tictactoe")
    async def tictactoe_cmd(self, message: Message):
        chat_id = message.chat.id
        self.games[chat_id] = {
            'board': [' '] * 9,
            'turn': 'X'
        }
        await self.send_board(message, chat_id)

    async def send_board(self, message, chat_id):
        board = self.games[chat_id]['board']
        buttons = []
        for i in range(0, 9, 3):
            buttons.append([
                InlineKeyboardButton(board[i], callback_data=f"move:{chat_id}:{i}"),
                InlineKeyboardButton(board[i+1], callback_data=f"move:{chat_id}:{i+1}"),
                InlineKeyboardButton(board[i+2], callback_data=f"move:{chat_id}:{i+2}")
            ])
        await message.reply("Tic-Tac-Toe\nX goes first", reply_markup=InlineKeyboardMarkup(buttons))

    @callback_query(filters.regex(r"^move:(\d+):(\d+)$"))
    async def handle_move(self, bot: Client, callback_query):
        chat_id, move = map(int, callback_query.data.split(":")[1:])
        game = self.games[chat_id]

        if game['board'][move] != ' ':
            await callback_query.answer("Invalid move!", show_alert=True)
            return

        game['board'][move] = game['turn']
        game['turn'] = 'O' if game['turn'] == 'X' else 'X'
        await callback_query.message.delete()
        await self.send_board(callback_query.message, chat_id)

        winner = self.check_winner(game['board'])
        if winner:
            await bot.send_message(chat_id, f"Player {winner} wins!")
            del self.games[chat_id]
        elif ' ' not in game['board']:
            await bot.send_message(chat_id, "It's a draw!")
            del self.games[chat_id]

    def check_winner(self, board):
        winning_positions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8),  # columns
            (0, 4, 8), (2, 4, 6)              # diagonals
        ]
        for pos in winning_positions:
            if board[pos[0]] == board[pos[1]] == board[pos[2]] and board[pos[0]] != ' ':
                return board[pos[0]]
        return None
