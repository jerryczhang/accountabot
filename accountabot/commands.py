from datetime import datetime, timedelta

from discord.ext import commands  # type: ignore

from .data import User
from .data import Commitment
from .data import Recurrence
from .data import users
from .data import user_time
from .data import supported_timezones
from .data import parse_recurrence


_timezone_parameter = commands.parameter(
    converter=str,
    description="Your timezone code (e.g. PST, PDT, EDT, etc.)",
    default="PST",
    displayed_default="PST",
)

_name_parameter = commands.parameter(
    converter=str, description="Name of the accountability commitment"
)

_description_parameter = commands.parameter(
    converter=str,
    description="A more detailed description",
)

_recurrence_parameter = commands.parameter(
    converter=str,
    description="How often your commitment repeats",
    default="daily",
    displayed_default="Daily",
)


class NotRegisteredError(commands.CommandError):
    ...


async def _is_registered(ctx: commands.Context):
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
    async def register(
        self, ctx: commands.Context, timezone: str = _timezone_parameter
    ):
        """Register yourself as a new user, or update your existing profile"""

        timezone = timezone.upper()
        if timezone not in supported_timezones:
            invalid_timezone_message = (
                f"Timezone '{timezone}' isn't valid\n"
                f"Supported timezones: {', '.join(supported_timezones)}"
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
    @commands.check(_is_registered)
    async def commit(
        self,
        ctx: commands.Context,
        name: str = _name_parameter,
        description: str = _description_parameter,
        recurrence: str = _recurrence_parameter,
    ):
        """
        Create a new commitment, or update existing commitment by name

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
            next_check_in=_first_check_in(user, recurrence_obj),
            recurrence=recurrence_obj,
            num_missed_in_a_row=0,
        )
        user.commitments.append(new_commitment)
        users.save()
        await ctx.send(f"New commitment: {new_commitment}")

    @commands.command(name="check-in")
    @commands.check(_is_registered)
    async def check_in(self, ctx: commands.Context, name: str = _name_parameter):
        """Check in your accountability commitment (mark as completed)"""

        user = users.member_id_to_user[ctx.author.id]
        for commitment in user.commitments:
            if commitment.name != name:
                continue
            time_difference = commitment.next_check_in - user_time(user, datetime.now())
            if time_difference.days >= 1:
                await ctx.send(
                    "You aren't supposed to do this commitment yet! "
                    f"Next check in is in {time_difference.days} more day(s)"
                )
                return
            commitment.num_missed_in_a_row = 0
            commitment.cycle_check_in()
            users.save()
            await ctx.send(f"Checked in! {commitment}")
            return
        await ctx.send(f'You don\'t have a commitment called "{name}"')

    @commands.command()
    @commands.check(_is_registered)
    async def delete(self, ctx: commands.Context, name: str = _name_parameter):
        """Delete an accountability commitment"""

        user = users.member_id_to_user[ctx.author.id]
        for index, commitment in enumerate(user.commitments):
            if commitment.name != name:
                continue
            user.commitments.pop(index)
            users.save()
            await ctx.send(f"Deleted commitment {commitment}")
            return
        await ctx.send(f'You don\'t have a commitment called "{name}"')


def _first_check_in(user: User, recurrence: Recurrence) -> datetime:
    now = user_time(user, datetime.now().utcnow())
    midnight = datetime(
        year=now.year, month=now.month, day=now.day, hour=23, minute=59, second=59
    )
    return recurrence.next_occurence(midnight - timedelta(days=1))
