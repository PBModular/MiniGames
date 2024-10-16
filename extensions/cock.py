from pyrogram import Client, filters
from pyrogram.types import Message
from base.module import BaseModule, command
from base.mod_ext import ModuleExtension
from ..db import Base, CockState
from ..utils import fetch_user
from ..config import CockConfig
from sqlalchemy import select, delete, func
from datetime import datetime, timedelta
import random

class CockExtension(ModuleExtension):
    @property
    def db_meta(self):
        return Base.metadata  

    async def set_participation(self, chat_id, user_id, is_participating):
        async with self.db.session_maker() as session:
            cock_state = await session.execute(
                select(CockState).where(CockState.chat_id == chat_id, CockState.user_id == user_id)
            )
            cock_state = cock_state.scalar_one_or_none()
            
            if cock_state is None:
                cock_state = CockState(chat_id=chat_id, user_id=user_id, is_participating=is_participating)
                if cock_state.cock_size is None:
                    cock_state.cock_size = CockConfig.DEFAULT_COCK_SIZE
                session.add(cock_state)
            else:
                cock_state.is_participating = is_participating
            
            await session.commit()

    async def get_participants(self, chat_id):
        async with self.db.session_maker() as session:
            participants = await session.execute(
                select(CockState.user_id).where(CockState.chat_id == chat_id, CockState.is_participating == True)
            )
            participants = [participant[0] for participant in participants]
            return participants

    async def set_cock_length(self, chat_id, user_id, change):
        async with self.db.session_maker() as session:
            cock_state = await session.scalar(
                select(CockState).where(CockState.chat_id == chat_id, CockState.user_id == user_id).with_for_update()
            )
            if cock_state.active_event == "rubber":
                cock_state.cock_size = change
            else:
                cock_state.cock_size += change

            cock_state.cock_size = round(cock_state.cock_size, 1)

            if cock_state.event_duration > 0:
                cock_state.event_duration -= 1
                if cock_state.event_duration == 0:
                    cock_state.active_event = None

            session.add(cock_state)
            await session.commit()

    async def get_cock_length(self, chat_id, user_id):
        async with self.db.session_maker() as session:
            cock_state = await session.scalar(
                select(CockState).where(CockState.chat_id == chat_id, CockState.user_id == user_id)
            )
            if cock_state.cock_size is None:
                cock_state.cock_size = CockConfig.DEFAULT_COCK_SIZE
                session.add(cock_state)
                await session.commit()
            return cock_state.cock_size

    async def get_all_participants(self, chat_id):
        async with self.db.session_maker() as session:
            participants = await session.execute(
                select(CockState.user_id, CockState.cock_size).where(CockState.chat_id == chat_id, CockState.is_participating == True)
            )
            participants = participants.all()
            return participants

    async def get_average_length(self, chat_id):
        async with self.db.session_maker() as session:
            avg_length = await session.execute(
                select(func.avg(CockState.cock_size)).where(CockState.chat_id == chat_id, CockState.is_participating == True)
            )
            avg_length = avg_length.scalar()
            return avg_length if avg_length is not None else 0

    def calculate_change(self, current_length):
        increase_probability = max(CockConfig.MIN_PROB_COCK_SIZE_INCREASE, CockConfig.MAX_PROB_COCK_SIZE_INCREASE
                                    - (current_length / CockConfig.MAX_COCK_SIZE) * CockConfig.SCALING_FACTOR)
        rand_num = random.random()

        if (rand_num <= increase_probability):
            change = random.randint(1, min(CockConfig.DEFAULT_COCK_SIZE, CockConfig.MAX_COCK_SIZE - current_length))
        else:
            max_decrease = max(1, (current_length * 0.25))
            change = -random.randint(1, int(max_decrease))

        return change

    async def check_special_events(self, bot, chat_id, user_id, current_length):
        async with self.db.session_maker() as session:
            cock_state = await session.scalar(
                select(CockState).where(CockState.chat_id == chat_id, CockState.user_id == user_id)
            )
            if cock_state.active_event:
                return None

            events = []

            events.extend([
                (self.event_micro, CockConfig.PROB_MICRO) if current_length > (CockConfig.MAX_COCK_SIZE * 0.7) else None,
                (self.event_rubber, CockConfig.PROB_RUBBER),
                (self.event_teleport, CockConfig.PROB_TELEPORT),
                (self.event_aging, CockConfig.PROB_AGING),
                (self.event_rocket, CockConfig.PROB_ROCKET),
                (self.event_magnetic, CockConfig.PROB_MAGNETIC),
                (self.event_shrink_ray, CockConfig.PROB_SHRINK_RAY),
                (self.event_growth_spurt, CockConfig.PROB_GROWTH_SPURT),
                (self.event_phantom_shrink, CockConfig.PROB_PHANTOM_SHRINK),
                (self.event_black_hole, CockConfig.PROB_BLACK_HOLE)
            ])

            events = list(filter(None, events))

            eligible_events = [(event, weight) for event, weight in events if random.random() < weight]

            if eligible_events:
                total_weight = sum(weight for _, weight in eligible_events)
                rand_choice = random.uniform(0, total_weight)
                cumulative_weight = 0

                for event, weight in eligible_events:
                    cumulative_weight += weight
                    if rand_choice <= cumulative_weight:
                        chosen_event = event
                        break

                special_event_message = await chosen_event(bot, chat_id, user_id, current_length)
                if special_event_message:
                    return special_event_message

            return None

    async def event_micro(self, bot, chat_id, user_id, current_length):
        await self.set_cock_length(chat_id, user_id, -current_length + 0.1)
        return self.S["cock"]["event"]["micro"]

    async def event_rubber(self, bot, chat_id, user_id, current_length):
        async with self.db.session_maker() as session:
            cock_state = await session.scalar(
                select(CockState).where(CockState.chat_id == chat_id, CockState.user_id == user_id)
            )
            cock_state.active_event = "rubber"
            cock_state.event_duration = CockConfig.EVENT_RUBBER_DURATION
            session.add(cock_state)
            await session.commit()

        return self.S["cock"]["event"]["rubber"]["message"]

    async def event_teleport(self, bot, chat_id, user_id, current_length):
        participants = await self.get_all_participants(chat_id)
        if len(participants) < 2:
            return None

        other_user_id, other_user_length = random.choice([p for p in participants if p[0] != user_id])
        fetch_user = await fetch_user(bot, user_id, with_link=True)

        async with self.db.session_maker() as session:
            user_cock_state = await session.scalar(
                select(CockState).where(CockState.chat_id == chat_id, CockState.user_id == user_id)
            )
            other_cock_state = await session.scalar(
                select(CockState).where(CockState.chat_id == chat_id, CockState.user_id == other_user_id)
            )

            user_cock_state.cock_size, other_cock_state.cock_size = other_cock_state.cock_size, user_cock_state.cock_size

            session.add(user_cock_state)
            session.add(other_cock_state)
            await session.commit()

        return self.S["cock"]["event"]["teleport"].format(fetch_user=fetch_user, other_user_length=other_user_length)

    async def event_aging(self, bot, chat_id, user_id, current_length):
        new_length = round(current_length * 0.8, 1)
        await self.set_cock_length(chat_id, user_id, new_length - current_length)
        return self.S["cock"]["event"]["aging"].format(new_length=new_length)

    async def event_rocket(self, bot, chat_id, user_id, current_length):
        async with self.db.session_maker() as session:
            cock_state = await session.scalar(
                select(CockState).where(CockState.chat_id == chat_id, CockState.user_id == user_id)
            )
            cock_state.active_event = "rocket"
            cock_state.event_duration = random.randint(CockConfig.EVENT_ROCKET_MIN_DURATION, CockConfig.EVENT_ROCKET_MAX_DURATION)
            session.add(cock_state)
            await session.commit()

        return self.S["cock"]["event"]["rocket"]["message"]

    async def event_magnetic(self, bot, chat_id, user_id, current_length):
        participants = await self.get_all_participants(chat_id)
        if len(participants) < 2:
            return None

        possible_targets = [p for p in participants if p[0] != user_id and p[1] > 3]
        if not possible_targets:
            return None

        target_user_id, target_length = random.choice(possible_targets)
        change = random.randint(1, (target_length * 0.6))

        async with self.db.session_maker() as session:
            user_cock_state = await session.scalar(
                select(CockState).where(CockState.chat_id == chat_id, CockState.user_id == user_id)
            )
            target_cock_state = await session.scalar(
                select(CockState).where(CockState.chat_id == chat_id, CockState.user_id == target_user_id)
            )

            user_cock_state.cock_size += change
            target_cock_state.cock_size -= change

            session.add(user_cock_state)
            session.add(target_cock_state)
            await session.commit()

        target_user = await fetch_user(bot, target_user_id, with_link=True)
        return self.S["cock"]["event"]["magnetic"].format(target_user=target_user, change=change)

    async def event_shrink_ray(self, bot, chat_id, user_id, current_length):
        change = round(current_length / 2, 1)
        await self.set_cock_length(chat_id, user_id, change - current_length)
        return self.S["cock"]["event"]["shrink_ray"].format(change=change)

    async def event_growth_spurt(self, bot, chat_id, user_id, current_length):
        change = random.randint(5, 15)
        new_length = current_length + change
        await self.set_cock_length(chat_id, user_id, change)
        return self.S["cock"]["event"]["growth_spurt"].format(change=change, new_length=new_length)

    async def event_phantom_shrink(self, bot, chat_id, user_id, current_length):
        change = random.randint(5, 15)
        await self.set_cock_length(chat_id, user_id, -change)
        new_length = current_length - change
        return self.S["cock"]["event"]["phantom_shrink"].format(change=change, new_length=new_length)

    async def event_black_hole(self, bot, chat_id, user_id, current_length):
        change = random.randint(2, 10)
        await self.set_cock_length(chat_id, user_id, -change)
        new_length = round(current_length - change, 1)
        return self.S["cock"]["event"]["black_hole"].format(change=change, new_length=new_length)

    @command("cockjoin")
    async def join_cmd(self, bot: Client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        participants = await self.get_participants(chat_id)

        if user_id in participants:
            await message.reply(self.S["cock"]["join"]["already"])
        else:
            await self.set_participation(chat_id, user_id, True)
            await message.reply(self.S["cock"]["join"]["ok"])

    @command("cockleave")
    async def leave_cmd(self, bot: Client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        participants = await self.get_participants(chat_id)

        if user_id in participants:
            async with self.db.session_maker() as session:
                await session.execute(
                    delete(CockState).where(CockState.chat_id == chat_id, CockState.user_id == user_id)
                )
                await session.commit()
            await message.reply(self.S["cock"]["leave"]["ok"])
        else:
            await message.reply(self.S["cock"]["leave"]["not_participant"])

    @command("cock")
    async def cock_cmd(self, bot: Client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        participants = await self.get_participants(chat_id)

        if user_id not in participants:
            await message.reply(self.S["cock"]["not_participant"])
            return

        async with self.db.session_maker() as session:
            cock_state = await session.scalar(
                select(CockState).where(CockState.chat_id == chat_id, CockState.user_id == user_id)
            )

            now = datetime.utcnow()
            if cock_state.cooldown and now - cock_state.cooldown < timedelta(hours=CockConfig.COOLDOWN_HOURS):
                time_remaining = timedelta(hours=CockConfig.COOLDOWN_HOURS) - (now - cock_state.cooldown)
                hours, remainder = divmod(time_remaining.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                await message.reply(self.S["cock"]["cooldown"].format(hours=hours, minutes=minutes))
                return

            current_length = await self.get_cock_length(chat_id, user_id)
            special_event_message = await self.check_special_events(bot, chat_id, user_id, current_length)

            if special_event_message:
                await message.reply(special_event_message)
            else:
                if cock_state.active_event == "rubber" and cock_state.event_duration > 0:
                    change = random.randint(CockConfig.MIN_COCK_SIZE, CockConfig.MAX_COCK_SIZE)
                    await self.set_cock_length(chat_id, user_id, change)
                    return self.S["cock"]["event"]["rubber"]["change"].format(change=change, remain=(cock_state.event_duration - 1))
                elif cock_state.active_event == "rocket" and cock_state.event_duration > 0:
                    if random.random() < 0.5:
                        cock_state.event_duration -= 1
                        change = current_length + random.randint(10, 20)
                        await self.set_cock_length(chat_id, user_id, change)
                        result_message = self.S["cock"]["event"]["rocket"]["no_change"].format(change=change)
                    else:
                        cock_state.event_duration = 0
                        change = current_length / 4
                        await self.set_cock_length(chat_id, user_id, change)
                        result_message = self.S["cock"]["event"]["rocket"]["change"].format(change=change)
                else:
                    change = self.calculate_change(current_length)
                    await self.set_cock_length(chat_id, user_id, change)
                    new_length = await self.get_cock_length(chat_id, user_id)
                    result_message = self.S["cock"]["change"].format(new_length=new_length, change=change)

                await message.reply(result_message)

            cock_state.cooldown = now
            session.add(cock_state)
            await session.commit()

    @command("cockstat")
    async def cockstat_cmd(self, bot: Client, message: Message):
        chat_id = message.chat.id
        participants = await self.get_all_participants(chat_id)
        average_length = await self.get_average_length(chat_id)

        if not participants:
            await message.reply(self.S["cock"]["stat"]["no_participants"])
            return

        sorted_participants = sorted(participants, key=lambda x: x[1], reverse=True)

        stats_message = self.S["cock"]["stat"]["list_header"]
        for place, (user_id, cock_length) in enumerate(sorted_participants, start=1):
            profile_link = await fetch_user(bot, user_id, with_link=False)
            stats_message += self.S["cock"]["stat"]["list"].format(place=place, profile_link=profile_link, cock_length=cock_length)

        stats_message += self.S["cock"]["stat"]["average"].format(average=round(average_length, 2))

        await message.reply(stats_message)
    