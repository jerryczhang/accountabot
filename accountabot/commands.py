from datetime import datetime, timedelta

from discord.ext import commands  # type: ignore

from .data import User
from .data import Commitment
from .data import Recurrence
from .data import timezone_to_utc_offset
from .data import users
from .data import parse_recurrence


timezone_parameter = commands.parameter(
    converter=str,
    description="Your timezone code (e.g. PST, PDT, EDT, etc.)",
    default="PST",
    displayed_default="PST",
)

name_parameter = commands.parameter(
    converter=str, description="What you want to commit to"
)

description_parameter = commands.parameter(
    converter=str,
    description="A more detailed description",
)

recurrence_parameter = commands.parameter(
    converter=str,
    description="How often your commitment repeats",
    default="daily",
    displayed_default="Daily",
)


class NotRegisteredError(commands.CommandError):
    ...


async def is_registered(ctx: commands.Context):
    is_registered = ctx.author.id in users.member_id_to_user
    if not is_registered:
        raise NotRegisteredError(
            f"You must register yourself as a user first!\n"
            'Type "&register <your_timezone>"'
        )
    return True


class Accountability(commands.Cog):
    """Commands to manage your accountability commitments"""

    @commands.command()
    async def register(self, ctx: commands.Context, timezone: str = timezone_parameter):
        """Register yourself as a new user, or update your existing profile"""

        timezone = timezone.upper()
        if timezone not in timezone_to_utc_offset:
            invalid_timezone_message = (
                f"Timezone '{timezone}' isn't valid\n"
                f"Supported timezones: {', '.join(list(timezone_to_utc_offset.keys()))}"
            )
            await ctx.send(invalid_timezone_message)
            return

        member_id = ctx.author.id
        if member_id in users.member_id_to_user:
            user = users.member_id_to_user[member_id]
            user.timezone = timezone
            await ctx.send(f"User updated:\n{user}")
        else:
            new_user = User(
                member_id=member_id, commitments=[], is_active=True, timezone=timezone
            )
            users.member_id_to_user[member_id] = new_user
            users.save()
            await ctx.send(f"Registered!\n{new_user}")

    @commands.command()
    @commands.check(is_registered)
    async def commit(
        self,
        ctx: commands.Context,
        name: str = name_parameter,
        description: str = description_parameter,
        recurrence: str = recurrence_parameter,
    ):
        """
        Create a new accountability commitment, or update an existing commitment with the same name

        Examples:
            &commit "Read" "Read for 30 min. before bed" "daily"
            &commit "Workout" "PPL program + flexibility routine" "Weekly Mon,Wed,Fri"
            &commit "Golden hour" "Do a golden hour at work" "weekly mon tue wed thu fri"

        Enclose each argument in quotes

        For the recurrence, either indicate "weekly" and specify the days of the week as a three-letter
        abbreviation (e.g. Sun, Mon, Tue, etc.), or indicate "daily"
        """
        try:
            recurrence_obj = parse_recurrence(recurrence)
        except ValueError as ex:
            await ctx.send(str(ex))

        user = users.member_id_to_user[ctx.author.id]
        for commitment in user.commitments:
            if name == commitment.name:
                commitment.description = description
                commitment.recurrence = recurrence_obj
                users.save()
                await ctx.send(f"Commitment updated: {commitment}")
                return
        new_commitment = Commitment(
            owner_id=user.member_id,
            name=name,
            description=description,
            next_check_in=first_check_in(user, recurrence_obj),
            recurrence=recurrence_obj,
            num_missed_in_a_row=0,
        )
        user.commitments.append(new_commitment)
        users.save()
        await ctx.send(f"New commitment: {new_commitment}")


def first_check_in(user: User, recurrence: Recurrence) -> datetime:
    now = datetime.now()
    midnight = datetime(
        year=now.year, month=now.month, day=now.day, hour=23, minute=59, second=59
    )
    user_midnight = midnight + timedelta(hours=timezone_to_utc_offset[user.timezone])
    return recurrence.next_occurence(user_midnight - timedelta(days=1))
