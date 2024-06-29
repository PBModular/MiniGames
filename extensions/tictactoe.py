from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from base.module import BaseModule, command, allowed_for, callback_query
from base.mod_ext import ModuleExtension
import random

class TicTacToeExtension(ModuleExtension):
    def on_init(self):
        self.games = {}
        self.waiting = {}

    @command("tictactoe")
    async def tictactoe_cmd(self, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        if chat_id in self.games:
            await message.reply(self.S["tictactoe"]["already_game"])
            return
        
        if chat_id in self.waiting:
            await message.reply(self.S["tictactoe"]["already_waiting"])
            return

        join_button = InlineKeyboardMarkup([
            [InlineKeyboardButton(self.S["tictactoe"]["join_button"], callback_data="join")]
        ])
        waiting_message = await message.reply(self.S["tictactoe"]["waiting"], reply_markup=join_button)
        self.waiting[chat_id] = {"user_id": user_id, "message": waiting_message}

    @callback_query(filters.regex(r"^join$"))
    async def join_game(self, callback_query):
        chat_id = callback_query.message.chat.id
        user_id = callback_query.from_user.id

        if chat_id not in self.waiting:
            await callback_query.answer(self.S["tictactoe"]["not_waiting"], show_alert=True)
            return

        if self.waiting[chat_id]["user_id"] == user_id:
            await callback_query.answer(self.S["tictactoe"]["your_game"], show_alert=True)
            return

        players = [self.waiting[chat_id]["user_id"], user_id]
        random.shuffle(players)
        self.games[chat_id] = {
            'board': [' '] * 9,
            'turn': 'X',
            'players': {
                'X': players[0],
                'O': players[1]
            }
        }
        waiting_message = self.waiting[chat_id]["message"]
        del self.waiting[chat_id]
        await self.send_board(waiting_message, chat_id, edit=True)

    async def send_board(self, message, chat_id, edit=False):
        game = self.games[chat_id]
        board = game['board']
        turn = game['turn']
        current_player = await message.chat.get_member(game['players'][turn])
        buttons = []
        for i in range(0, 9, 3):
            buttons.append([
                InlineKeyboardButton(board[i], callback_data=f"move:{chat_id}:{i}"),
                InlineKeyboardButton(board[i+1], callback_data=f"move:{chat_id}:{i+1}"),
                InlineKeyboardButton(board[i+2], callback_data=f"move:{chat_id}:{i+2}")
            ])
        text = self.S["tictactoe"]["current_turn"].format(user_name=current_player.user.first_name, turn=turn)
        if edit:
            await message.edit(text, reply_markup=InlineKeyboardMarkup(buttons))
        else:
            await message.reply(text, reply_markup=InlineKeyboardMarkup(buttons))

    @callback_query(filters.regex(r"^move:"))
    async def handle_move(self, callback_query):
        chat_id, move = map(int, callback_query.data.split(":")[1:])
        game = self.games[chat_id]
        user_id = callback_query.from_user.id
        if user_id != game['players'][game['turn']]:
            await callback_query.answer(self.S["tictactoe"]["not_your_turn"], show_alert=True)
            return

        if game['board'][move] != ' ':
            await callback_query.answer(self.S["tictactoe"]["invalid_move"], show_alert=True)
            return

        game['board'][move] = game['turn']
        game['turn'] = 'O' if game['turn'] == 'X' else 'X'
        await callback_query.message.delete()
        await self.send_board(callback_query.message, chat_id)

        winner = self.check_winner(game['board'])
        if winner:
            winner_name = (await callback_query.message.chat.get_member(game['players'][winner]))
            await callback_query.message.reply(self.S["tictactoe"]["player_win"].format(winner_name=winner_name, winner=winner))
            del self.games[chat_id]
        elif ' ' not in game['board']:
            await callback_query.message.reply(self.S["tictactoe"]["draw"])
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