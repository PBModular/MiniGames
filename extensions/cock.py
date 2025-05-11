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
import json

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
                    cock_state.cock_size = float(CockConfig.DEFAULT_COCK_SIZE)
                session.add(cock_state)
            else:
                cock_state.is_participating = is_participating
            
            await session.commit()

    async def get_participants(self, chat_id):
        async with self.db.session_maker() as session:
            participants_result = await session.execute(
                select(CockState.user_id).where(CockState.chat_id == chat_id, CockState.is_participating == True)
            )
            participants = [participant[0] for participant in participants_result]
            return participants

    async def set_cock_length(self, chat_id, user_id, change, absolute=False, skip_event_duration_decrement=False):
        async with self.db.session_maker() as session:
            cock_state = await session.scalar(
                select(CockState).where(CockState.chat_id == chat_id, CockState.user_id == user_id).with_for_update()
            )
            if not cock_state:
                return

            if absolute:
                cock_state.cock_size = float(change)
            elif cock_state.active_event == "rubber" and not absolute:
                cock_state.cock_size = float(change)
            else:
                cock_state.cock_size += float(change)

            cock_state.cock_size = round(cock_state.cock_size, 1)
            cock_state.cock_size = max(float(CockConfig.MIN_COCK_SIZE), cock_state.cock_size)

            if not skip_event_duration_decrement and cock_state.active_event:
                if cock_state.event_duration > 0:
                    cock_state.event_duration -= 1
                    if cock_state.event_duration == 0:
                        cock_state.active_event = None
                        cock_state.event_data = None

            session.add(cock_state)
            await session.commit()

    async def get_cock_length(self, chat_id, user_id):
        async with self.db.session_maker() as session:
            cock_state = await session.scalar(
                select(CockState).where(CockState.chat_id == chat_id, CockState.user_id == user_id)
            )
            if not cock_state:
                return float(CockConfig.DEFAULT_COCK_SIZE) 
            if cock_state.cock_size is None:
                cock_state.cock_size = float(CockConfig.DEFAULT_COCK_SIZE)
                session.add(cock_state)
                await session.commit()
            return float(cock_state.cock_size)

    async def get_all_participants(self, chat_id):
        async with self.db.session_maker() as session:
            participants_result = await session.execute(
                select(CockState.user_id, CockState.cock_size).where(CockState.chat_id == chat_id, CockState.is_participating == True)
            )
            participants = [(p[0], float(p[1]) if p[1] is not None else float(CockConfig.DEFAULT_COCK_SIZE)) for p in participants_result.all()]
            return participants

    async def get_average_length(self, chat_id):
        async with self.db.session_maker() as session:
            avg_length_result = await session.execute(
                select(func.avg(CockState.cock_size)).where(CockState.chat_id == chat_id, CockState.is_participating == True)
            )
            avg_length = avg_length_result.scalar()
            return float(avg_length) if avg_length is not None else 0.0

    def calculate_change(self, current_length):
        increase_probability = max(CockConfig.MIN_PROB_COCK_SIZE_INCREASE, CockConfig.MAX_PROB_COCK_SIZE_INCREASE
                                    - (current_length / CockConfig.MAX_COCK_SIZE) * CockConfig.SCALING_FACTOR)
        rand_num = random.random()

        if (rand_num <= increase_probability):
            change = random.uniform(1.0, float(CockConfig.DEFAULT_COCK_SIZE))
        else:
            max_decrease = max(1.0, current_length * 0.25)
            change = -random.uniform(1.0, max_decrease)

        return round(change, 1)

    async def check_special_events(self, bot, chat_id, user_id, current_length):
        async with self.db.session_maker() as session:
            cock_state = await session.scalar(
                select(CockState).where(CockState.chat_id == chat_id, CockState.user_id == user_id)
            )
            if not cock_state or cock_state.active_event:
                return None

            events_config = []
            events_config.extend([
                (self.event_micro, CockConfig.PROB_MICRO) if current_length > (CockConfig.MAX_COCK_SIZE * 0.7) else None,
                (self.event_rubber, CockConfig.PROB_RUBBER),
                (self.event_teleport, CockConfig.PROB_TELEPORT),
                (self.event_aging, CockConfig.PROB_AGING),
                (self.event_rocket, CockConfig.PROB_ROCKET),
                (self.event_magnetic, CockConfig.PROB_MAGNETIC),
                (self.event_shrink_ray, CockConfig.PROB_SHRINK_RAY),
                (self.event_growth_spurt, CockConfig.PROB_GROWTH_SPURT),
                (self.event_phantom_shrink, CockConfig.PROB_PHANTOM_SHRINK),
                (self.event_black_hole, CockConfig.PROB_BLACK_HOLE),
                (self.event_average_recalibration, CockConfig.PROB_AVERAGE_RECALIBRATION),
                (self.event_phantom_limb_syndrome, CockConfig.PROB_PHANTOM_LIMB_SYNDROME),
                (self.event_the_borrower, CockConfig.PROB_BORROWER),
                (self.event_existential_crisis, CockConfig.PROB_EXISTENTIAL_CRISIS),
                (self.event_humblebrag_tax, CockConfig.PROB_HUMBLEBRAG_TAX),
            ])

            events_config = list(filter(None, events_config))

            total_prob_sum = sum(prob for _, prob in events_config)
            if total_prob_sum == 0:
                return None

            eligible_events = [(event_func, weight) for event_func, weight in events_config if random.random() < weight]

            if not eligible_events:
                return None

            total_weight = sum(weight for _, weight in eligible_events)
            if total_weight == 0: return None

            rand_choice = random.uniform(0, total_weight)
            cumulative_weight = 0.0
            chosen_event_func = None

            for event_func, weight in eligible_events:
                cumulative_weight += weight
                if rand_choice <= cumulative_weight:
                    chosen_event_func = event_func
                    break
            
            if chosen_event_func:
                return await chosen_event_func(bot, chat_id, user_id, current_length, session, cock_state)
            
            return None

    async def event_micro(self, bot, chat_id, user_id, current_length, session, cock_state):
        user_mention = await fetch_user(bot, user_id, with_link=True)
        await self.set_cock_length(chat_id, user_id, 0.1, absolute=True)
        return self.S["cock"]["event"]["micro"].format(user=user_mention)

    async def event_rubber(self, bot, chat_id, user_id, current_length, session, cock_state):
        user_mention = await fetch_user(bot, user_id, with_link=True)
        cock_state.active_event = "rubber"
        cock_state.event_duration = CockConfig.EVENT_RUBBER_DURATION
        session.add(cock_state)
        await session.commit()
        return self.S["cock"]["event"]["rubber"]["message"].format(user=user_mention, duration=cock_state.event_duration)

    async def event_teleport(self, bot, chat_id, user_id, current_length, session, cock_state_self):
        participants = await self.get_all_participants(chat_id)
        possible_targets = [p for p in participants if p[0] != user_id]
        if not possible_targets:
            return None

        other_user_id, other_user_original_length = random.choice(possible_targets)

        other_cock_state = await session.scalar(
            select(CockState).where(CockState.chat_id == chat_id, CockState.user_id == other_user_id).with_for_update()
        )

        if not other_cock_state: return None

        original_self_length = cock_state_self.cock_size
        cock_state_self.cock_size = other_cock_state.cock_size
        other_cock_state.cock_size = original_self_length

        cock_state_self.cock_size = max(float(CockConfig.MIN_COCK_SIZE), round(float(cock_state_self.cock_size),1))
        other_cock_state.cock_size = max(float(CockConfig.MIN_COCK_SIZE), round(float(other_cock_state.cock_size),1))

        session.add(cock_state_self)
        session.add(other_cock_state)
        await session.commit()

        current_user_display_name = await fetch_user(bot, user_id, with_link=True)
        other_user_display_name = await fetch_user(bot, other_user_id, with_link=True)
        return self.S["cock"]["event"]["teleport"].format(
            user1=current_user_display_name,
            user2=other_user_display_name,
            user1_new_length=round(float(cock_state_self.cock_size), 1),
            user2_new_length=round(float(other_cock_state.cock_size), 1)
        )

    async def event_aging(self, bot, chat_id, user_id, current_length, session, cock_state):
        user_mention = await fetch_user(bot, user_id, with_link=True)
        new_length = round(current_length * 0.8, 1)
        await self.set_cock_length(chat_id, user_id, new_length, absolute=True)
        return self.S["cock"]["event"]["aging"].format(user=user_mention, new_length=new_length)

    async def event_rocket(self, bot, chat_id, user_id, current_length, session, cock_state):
        user_mention = await fetch_user(bot, user_id, with_link=True)
        cock_state.active_event = "rocket"
        cock_state.event_duration = random.randint(CockConfig.EVENT_ROCKET_MIN_DURATION, CockConfig.EVENT_ROCKET_MAX_DURATION)
        initial_boost = 20.0
        await self.set_cock_length(chat_id, user_id, initial_boost)
        new_length_after_boost = await self.get_cock_length(chat_id, user_id)
        session.add(cock_state)
        await session.commit()
        return self.S["cock"]["event"]["rocket"]["message"].format(user=user_mention, initial_boost=initial_boost, new_length=new_length_after_boost, duration=cock_state.event_duration)

    async def event_magnetic(self, bot, chat_id, user_id, current_length, session, cock_state_self):
        user_mention = await fetch_user(bot, user_id, with_link=True)
        participants = await self.get_all_participants(chat_id)
        if len(participants) < 2: return None

        possible_targets = [p for p in participants if p[0] != user_id and p[1] > 3.0]
        if not possible_targets: return None

        target_user_id, target_length = random.choice(possible_targets)

        max_steal_amount = target_length * 0.6
        if max_steal_amount < 1.0: return None

        steal_amount = random.uniform(1.0, max_steal_amount)
        steal_amount = round(steal_amount, 1)

        target_cock_state = await session.scalar(
            select(CockState).where(CockState.chat_id == chat_id, CockState.user_id == target_user_id).with_for_update()
        )
        if not target_cock_state: return None

        actual_lost_by_target = min(steal_amount, target_cock_state.cock_size - float(CockConfig.MIN_COCK_SIZE))
        actual_lost_by_target = round(max(0.0, actual_lost_by_target), 1)

        if actual_lost_by_target > 0:
            cock_state_self.cock_size += actual_lost_by_target
            target_cock_state.cock_size -= actual_lost_by_target

            cock_state_self.cock_size = max(float(CockConfig.MIN_COCK_SIZE), round(cock_state_self.cock_size, 1))
            target_cock_state.cock_size = max(float(CockConfig.MIN_COCK_SIZE), round(target_cock_state.cock_size, 1))

            session.add(cock_state_self)
            session.add(target_cock_state)
            await session.commit()

            target_user_mention = await fetch_user(bot, target_user_id, with_link=True)
            return self.S["cock"]["event"]["magnetic"].format(user=user_mention, target_user=target_user_mention, change=actual_lost_by_target, new_length=cock_state_self.cock_size)
        return None

    async def event_shrink_ray(self, bot, chat_id, user_id, current_length, session, cock_state):
        user_mention = await fetch_user(bot, user_id, with_link=True)
        new_length = round(max(float(CockConfig.MIN_COCK_SIZE), current_length / 2), 1)
        await self.set_cock_length(chat_id, user_id, new_length, absolute=True)
        return self.S["cock"]["event"]["shrink_ray"].format(user=user_mention, new_length=new_length)

    async def event_growth_spurt(self, bot, chat_id, user_id, current_length, session, cock_state):
        user_mention = await fetch_user(bot, user_id, with_link=True)
        change = random.randint(5, 15)
        await self.set_cock_length(chat_id, user_id, float(change))
        new_length = await self.get_cock_length(chat_id, user_id)
        return self.S["cock"]["event"]["growth_spurt"].format(user=user_mention, change=change, new_length=new_length)

    async def event_phantom_shrink(self, bot, chat_id, user_id, current_length, session, cock_state):
        user_mention = await fetch_user(bot, user_id, with_link=True)
        change = random.randint(5, 15)
        await self.set_cock_length(chat_id, user_id, -float(change))
        new_length = await self.get_cock_length(chat_id, user_id)
        return self.S["cock"]["event"]["phantom_shrink"].format(user=user_mention, change=change, new_length=new_length)

    async def event_black_hole(self, bot, chat_id, user_id, current_length, session, cock_state):
        user_mention = await fetch_user(bot, user_id, with_link=True)
        change = random.randint(2, 10)
        await self.set_cock_length(chat_id, user_id, -float(change))
        new_length = await self.get_cock_length(chat_id, user_id)
        return self.S["cock"]["event"]["black_hole"].format(user=user_mention, change=change, new_length=new_length)

    async def event_average_recalibration(self, bot, chat_id, user_id, current_length, session, cock_state):
        user_mention = await fetch_user(bot, user_id, with_link=True)
        avg_length = await self.get_average_length(chat_id)
        if avg_length > 0 and abs(current_length - avg_length) > 0.1:
            await self.set_cock_length(chat_id, user_id, avg_length, absolute=True)
            return self.S["cock"]["event"]["average_recalibration"].format(user=user_mention, avg_length=round(avg_length, 1))
        return None

    async def event_phantom_limb_syndrome(self, bot, chat_id, user_id, current_length, session, cock_state):
        user_mention = await fetch_user(bot, user_id, with_link=True)
        fake_delta = round(random.uniform(8.0, 15.0) * random.choice([-1, 1]), 1)
        tiny_real_delta = round(random.uniform(0.1, 0.3) * random.choice([-1, 1]), 1)

        fake_new_length = round(current_length + fake_delta, 1)

        await self.set_cock_length(chat_id, user_id, tiny_real_delta, skip_event_duration_decrement=True)
        final_real_length = await self.get_cock_length(chat_id, user_id)

        cock_state.active_event = "phantom_limb_active"
        cock_state.event_duration = CockConfig.EVENT_PHANTOM_LIMB_DURATION
        cock_state.event_data = json.dumps({
            "tiny_real_change_applied": tiny_real_delta,
            "final_real_length": final_real_length
        })
        session.add(cock_state)
        await session.commit()
        return self.S["cock"]["event"]["phantom_limb"]["initial"].format(user=user_mention, fake_new_length=fake_new_length)

    async def event_the_borrower(self, bot, chat_id, user_id, current_length, session, cock_state_borrower):
        user_mention = await fetch_user(bot, user_id, with_link=True)
        participants = await self.get_all_participants(chat_id)
        possible_lenders = [p for p in participants if p[0] != user_id and p[1] > (float(CockConfig.MIN_COCK_SIZE) + 1.0)]
        if not possible_lenders: return None

        lender_id, lender_length = random.choice(possible_lenders)
        borrow_percentage = random.uniform(0.10, 0.30)
        borrowed_amount = round(lender_length * borrow_percentage, 1)

        if borrowed_amount < 0.5: return None

        cock_state_lender = await session.scalar(
            select(CockState).where(CockState.chat_id == chat_id, CockState.user_id == lender_id).with_for_update()
        )
        if not cock_state_lender: return None

        actual_borrowed = min(borrowed_amount, cock_state_lender.cock_size - float(CockConfig.MIN_COCK_SIZE))
        actual_borrowed = round(max(0.1, actual_borrowed), 1)
        if actual_borrowed < 0.1: return None

        duration = random.randint(CockConfig.EVENT_BORROWER_MIN_DURATION, CockConfig.EVENT_BORROWER_MAX_DURATION)

        cock_state_borrower.cock_size += actual_borrowed
        cock_state_lender.cock_size -= actual_borrowed
        cock_state_borrower.cock_size = round(max(float(CockConfig.MIN_COCK_SIZE), cock_state_borrower.cock_size),1)
        cock_state_lender.cock_size = round(max(float(CockConfig.MIN_COCK_SIZE), cock_state_lender.cock_size),1)

        cock_state_borrower.active_event = "borrower_active"
        cock_state_borrower.event_duration = duration
        cock_state_borrower.event_data = json.dumps({
            "lender_id": lender_id,
            "borrowed_amount": actual_borrowed
        })

        session.add(cock_state_borrower)
        session.add(cock_state_lender)
        await session.commit()

        lender_user_mention = await fetch_user(bot, lender_id, with_link=True)
        return self.S["cock"]["event"]["borrower"]["initial"].format(
            user=user_mention, 
            lender_user=lender_user_mention, 
            borrowed_amount=actual_borrowed, 
            duration=duration
        )

    async def event_existential_crisis(self, bot, chat_id, user_id, current_length, session, cock_state):
        user_mention = await fetch_user(bot, user_id, with_link=True)
        quotes = self.S["cock"]["event"]["existential_crisis"]["quotes"]
        chosen_quote = random.choice(quotes)

        cock_state.active_event = "existential_crisis_active"
        cock_state.event_duration = CockConfig.EVENT_EXISTENTIAL_CRISIS_DURATION
        cock_state.event_data = json.dumps({
            "original_length": current_length,
            "quote": chosen_quote 
        })
        session.add(cock_state)
        await session.commit()
        return self.S["cock"]["event"]["existential_crisis"]["initial"].format(user=user_mention, philosophical_quote=chosen_quote)

    async def event_humblebrag_tax(self, bot, chat_id, user_id, current_length, session, cock_state_payer):
        user_mention = await fetch_user(bot, user_id, with_link=True)
        all_participants_data = await self.get_all_participants(chat_id)
        if len(all_participants_data) < 3: return None

        sorted_participants = sorted(all_participants_data, key=lambda x: x[1], reverse=True)

        top_20_percent_cutoff = int(len(sorted_participants) * 0.2)
        if top_20_percent_cutoff == 0 and len(sorted_participants) > 0 : top_20_percent_cutoff = 1

        is_top_player = False
        for i, (p_id, p_size) in enumerate(sorted_participants):
            if p_id == user_id:
                if i < top_20_percent_cutoff:
                    is_top_player = True
                break
        if not is_top_player: return None

        tax_percentage = random.uniform(0.10, 0.25)
        tax_amount = round(current_length * tax_percentage, 1)
        tax_amount = min(tax_amount, current_length - float(CockConfig.MIN_COCK_SIZE))
        tax_amount = round(max(0.1, tax_amount),1)
        if tax_amount < 0.5: return None

        await self.set_cock_length(chat_id, user_id, -tax_amount, skip_event_duration_decrement=True)

        bottom_50_percent_start_index = len(sorted_participants) - int(len(sorted_participants) * 0.5)
        eligible_recipients_data = [p for i, p in enumerate(sorted_participants) if i >= bottom_50_percent_start_index and p[0] != user_id]

        if not eligible_recipients_data:
            return self.S["cock"]["event"]["humblebrag_tax"]["tax_vanished_no_recipients"].format(user=user_mention, tax_amount=tax_amount)

        num_recipients_to_get = random.randint(1, min(3, len(eligible_recipients_data)))
        chosen_recipients_info = random.sample(eligible_recipients_data, num_recipients_to_get)

        amount_per_recipient = round(tax_amount / num_recipients_to_get, 1)
        if amount_per_recipient < 0.1:
             return self.S["cock"]["event"]["humblebrag_tax"]["tax_vanished_too_small_split"].format(user=user_mention, tax_amount=tax_amount)

        recipient_mentions = []
        for recipient_id, _ in chosen_recipients_info:
            await self.set_cock_length(chat_id, recipient_id, amount_per_recipient, skip_event_duration_decrement=True)
            recipient_mentions.append(await fetch_user(bot, recipient_id, with_link=True))

        payer_message = self.S["cock"]["event"]["humblebrag_tax"]["payer_msg"].format(user=user_mention, tax_amount=tax_amount)
        recipients_str = ", ".join(recipient_mentions)

        if len(recipient_mentions) == 1:
            distribution_message = self.S["cock"]["event"]["humblebrag_tax"]["recipient_single_msg"].format(
                recipient_user=recipients_str,
                amount=amount_per_recipient)
        else:
            distribution_message = self.S["cock"]["event"]["humblebrag_tax"]["recipient_multi_msg"].format(
                recipient_list_str=recipients_str,
                amount_each=amount_per_recipient)

        return f"{payer_message} {distribution_message}"

    @command("cockjoin")
    async def join_cmd(self, bot: Client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        user_mention = await fetch_user(bot, user_id, with_link=True)
        participants = await self.get_participants(chat_id)

        if user_id in participants:
            await message.reply(self.S["cock"]["join"]["already"])
        else:
            await self.set_participation(chat_id, user_id, True)
            await message.reply(self.S["cock"]["join"]["ok"].format(user=user_mention, default_size=CockConfig.DEFAULT_COCK_SIZE))

    @command("cockleave")
    async def leave_cmd(self, bot: Client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        user_mention = await fetch_user(bot, user_id, with_link=True)

        async with self.db.session_maker() as session:
            cock_state = await session.get(CockState, (chat_id, user_id))
            if cock_state and cock_state.is_participating:
                await session.delete(cock_state)
                await session.commit()
                await message.reply(self.S["cock"]["leave"]["ok"].format(user=user_mention))
            else:
                await message.reply(self.S["cock"]["leave"]["not_participant"].format(user=user_mention))
    
    @command("cock")
    async def cock_cmd(self, bot: Client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        user_mention = await fetch_user(bot, user_id, with_link=True)

        async with self.db.session_maker() as session:
            cock_state = await session.scalar(
                select(CockState).where(CockState.chat_id == chat_id, CockState.user_id == user_id).with_for_update()
            )

            if not cock_state or not cock_state.is_participating:
                await message.reply(self.S["cock"]["not_participant"].format(user=user_mention, default_size=CockConfig.DEFAULT_COCK_SIZE))
                return

            now = datetime.utcnow()
            if not CockConfig.DEBUG_MODE:
                if cock_state.cooldown and now - cock_state.cooldown < timedelta(hours=CockConfig.COOLDOWN_HOURS):
                    time_remaining = timedelta(hours=CockConfig.COOLDOWN_HOURS) - (now - cock_state.cooldown)
                    hours, remainder = divmod(int(time_remaining.total_seconds()), 3600)
                    minutes, _ = divmod(remainder, 60)
                    await message.reply(self.S["cock"]["cooldown"].format(user=user_mention, hours=hours, minutes=minutes))
                    return

            current_length = float(cock_state.cock_size)

            resolution_message_parts = []
            previous_active_event_for_resolution = cock_state.active_event
            previous_event_data_for_resolution = cock_state.event_data
            previous_event_duration_for_resolution = cock_state.event_duration

            if previous_active_event_for_resolution == "phantom_limb_active" and previous_event_duration_for_resolution == 0 :
                if previous_event_data_for_resolution:
                    data = json.loads(previous_event_data_for_resolution)
                    resolution_message_parts.append(self.S["cock"]["event"]["phantom_limb"]["reveal"].format(
                        user=user_mention, 
                        tiny_real_change=data["tiny_real_change_applied"], 
                        final_real_length=data["final_real_length"]
                    ))
                cock_state.active_event = None
                cock_state.event_data = None

            elif previous_active_event_for_resolution == "borrower_active" and previous_event_duration_for_resolution == 0:
                if previous_event_data_for_resolution:
                    data = json.loads(previous_event_data_for_resolution)
                    lender_id = data["lender_id"]
                    returned_amount = float(data["borrowed_amount"])

                    cock_state.cock_size -= returned_amount
                    cock_state.cock_size = round(max(float(CockConfig.MIN_COCK_SIZE), cock_state.cock_size), 1)

                    lender_mention_str = await fetch_user(bot, lender_id, with_link=True)
                    lender_cock_state = await session.get(CockState, (chat_id, lender_id))
                    if lender_cock_state and lender_cock_state.is_participating:
                        lender_cock_state.cock_size += returned_amount
                        lender_cock_state.cock_size = round(max(float(CockConfig.MIN_COCK_SIZE), lender_cock_state.cock_size),1)
                        session.add(lender_cock_state)
                        resolution_message_parts.append(self.S["cock"]["event"]["borrower"]["return_success"].format(user=user_mention, amount=returned_amount, lender=lender_mention_str))
                    else:
                        resolution_message_parts.append(self.S["cock"]["event"]["borrower"]["return_fail_lender_gone"].format(user=user_mention, amount=returned_amount, lender=lender_mention_str))
                cock_state.active_event = None
                cock_state.event_data = None

            elif previous_active_event_for_resolution == "existential_crisis_active" and previous_event_duration_for_resolution == 0:
                if previous_event_data_for_resolution:
                    data = json.loads(previous_event_data_for_resolution)
                    original_length = float(data["original_length"])
                    small_random_change = round(random.uniform(-1.0, 1.0), 1)
                    resolved_length = max(float(CockConfig.MIN_COCK_SIZE), round(original_length + small_random_change, 1))
                    cock_state.cock_size = resolved_length
                    resolution_message_parts.append(self.S["cock"]["event"]["existential_crisis"]["resolve"].format(user=user_mention, new_length=resolved_length))
                cock_state.active_event = None
                cock_state.event_data = None

            if resolution_message_parts:
                await message.reply("\n".join(resolution_message_parts))

            current_length = float(cock_state.cock_size)

            special_event_message = await self.check_special_events(bot, chat_id, user_id, current_length)
            if special_event_message:
                await message.reply(special_event_message)

            elif cock_state.active_event == "rubber":
                new_random_size = round(random.uniform(float(CockConfig.MIN_COCK_SIZE), float(CockConfig.MAX_COCK_SIZE)),1)
                await self.set_cock_length(chat_id, user_id, new_random_size) 
                result_message = self.S["cock"]["event"]["rubber"]["change"].format(
                    change=new_random_size, 
                    remain=cock_state.event_duration
                )
                await message.reply(result_message)

            elif cock_state.active_event == "rocket":
                rocket_exploded = random.random() < 0.3

                if not rocket_exploded:
                    delta = random.uniform(5.0, 15.0)
                    await self.set_cock_length(chat_id, user_id, delta)
                    new_length_after_growth = await self.get_cock_length(chat_id, user_id)
                    result_message = self.S["cock"]["event"]["rocket"]["no_change"].format(
                        user=user_mention,
                        new_length=new_length_after_growth, 
                        remain=cock_state.event_duration
                    )
                else:
                    new_total_length_after_explosion = round(max(CockConfig.MIN_COCK_SIZE, current_length / 3.0),1)
                    await self.set_cock_length(chat_id, user_id, new_total_length_after_explosion, absolute=True, skip_event_duration_decrement=True)
                    
                    result_message = self.S["cock"]["event"]["rocket"]["change"].format(
                        user=user_mention,
                        new_length=new_total_length_after_explosion
                    )
                    cock_state.active_event = None
                    cock_state.event_duration = 0
                    cock_state.event_data = None
                await message.reply(result_message)
            else:
                change_delta = self.calculate_change(current_length)
                await self.set_cock_length(chat_id, user_id, change_delta)
                new_length = await self.get_cock_length(chat_id, user_id)
                result_message = self.S["cock"]["change"].format(
                    user=user_mention,
                    new_length=round(new_length, 1), 
                    change_sign="+" if change_delta >=0 else "",
                    change=round(change_delta, 1)
                )
                await message.reply(result_message)

            cock_state.cooldown = now
            session.add(cock_state)
            await session.commit()

    @command("cockstat")
    async def cockstat_cmd(self, bot: Client, message: Message):
        chat_id = message.chat.id
        participants_data = await self.get_all_participants(chat_id)
        average_length = await self.get_average_length(chat_id)

        if not participants_data:
            await message.reply(self.S["cock"]["stat"]["no_participants"])
            return

        sorted_participants = sorted(participants_data, key=lambda x: x[1], reverse=True)

        stats_message_parts = [self.S["cock"]["stat"]["list_header"]]
        for place, (user_id, cock_length) in enumerate(sorted_participants, start=1):
            async with self.db.session_maker() as s:
                p_state = await s.get(CockState, (chat_id, user_id))

            display_length_str = f"{round(cock_length, 1)} cm"
            if p_state and p_state.active_event == "existential_crisis_active" and p_state.event_data:
                try:
                    crisis_data = json.loads(p_state.event_data)
                    display_length_str = f"({crisis_data.get('quote', 'In Crisis')})"
                except json.JSONDecodeError:
                    display_length_str = "(Deep Thoughts)"

            profile_link = await fetch_user(bot, user_id, with_link=False)
            stats_message_parts.append(
                self.S["cock"]["stat"]["list_entry"].format(
                    place=place, 
                    profile_link=profile_link, 
                    cock_length_display=display_length_str
                )
            )

        stats_message_parts.append(self.S["cock"]["stat"]["average"].format(average=round(average_length, 2)))
        await message.reply("\n".join(stats_message_parts))
