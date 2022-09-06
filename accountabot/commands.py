from datetime import datetime, time, timedelta

from discord.ext import commands  # type: ignore

from .data import User
from .data import Commitment
from .data import Recurrence
from .data import Timezone
from .data import users
from .data import user_time


_timezone_parameter = commands.parameter(
    description="Your timezone code (e.g. PST, PDT, EDT, etc.)",
)

_commitment_parameter = commands.parameter(
    description="The name of your commitment",
)

_optional_commitment_parameter = commands.parameter(
    description="The name of your commitment",
    default=None,
    displayed_default=None,
)

_commitment_name_parameter = commands.parameter(
    description="What do you want to commit to?",
)

_description_parameter = commands.parameter(
    description="A detailed description",
)

_recurrence_parameter = commands.parameter(
    description="How often your commitment repeats"
)

_optional_reminder_parameter = commands.parameter(
    description='When to be reminded in format "H:MM AM/PM"',
    default=None,
)


async def _is_registered(ctx: commands.Context):
    is_registered = ctx.author.id in users.member_id_to_user
    if not is_registered:
        raise commands.errors.UserInputError(
            f"You must register yourself as a user first!\n"
            'Type "&register <your_timezone>"'
        )
    return True


class _Time(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> time:
        try:
            return datetime.strptime(argument.upper(), "%I:%M %p").time()
        except ValueError:
            raise commands.errors.UserInputError(
                f'Cannot parse time "{argument}", make sure to use format "H:MM AM/PM"'
            )


class Accountability(commands.Cog):
    """Commands to manage your accountability commitments"""

    @commands.command()
    async def register(
        self, ctx: commands.Context, timezone: Timezone = _timezone_parameter
    ):
        """Register yourself as a new user, or update your existing profile"""

        member_id = ctx.author.id
        if member_id in users.member_id_to_user:
            user = users.member_id_to_user[member_id]
            user.timezone = timezone
            await _save_and_message(ctx, f"User updated:\n{user}")
        else:
            new_user = User(
                member_id=member_id, commitments=[], is_active=True, timezone=timezone
            )
            users.member_id_to_user[member_id] = new_user
            await _save_and_message(ctx, f"Registered!\n{new_user}")

    @commands.command()
    @commands.check(_is_registered)
    async def commit(
        self,
        ctx: commands.Context,
        name: str = _commitment_name_parameter,
        description: str = _description_parameter,
        recurrence: Recurrence = _recurrence_parameter,
        reminder: _Time = _optional_reminder_parameter,
    ):
        """
        Create a new commitment, or update existing commitment by name

        Examples:
            &commit "Read" "Read for 30 min. before bed" "daily"
            &commit "Workout" "PPL program + flexibility routine" "Weekly Mon,Wed,Fri" "9:00 AM"
            &commit "Golden hour" "Do a golden hour at work" "weekly mon tue wed thu fri"

        Enclose each argument in quotes

        For the recurrence, either indicate "weekly" and specify the days of the week as a three-letter
        abbreviation (e.g. Sun, Mon, Tue, etc.), or indicate "daily"

        For the reminder, indicate the time in format "H:MM AM/PM", or leave blank for no reminder
        """
        user = users.member_id_to_user[ctx.author.id]
        commitment = _find_commitment(user, name)
        if commitment:
            commitment.description = description
            commitment.recurrence = recurrence
            commitment.reminder = reminder
            await _save_and_message(ctx, f"Commitment updated: {commitment}")
        else:
            new_commitment = Commitment(
                owner_id=user.member_id,
                name=name,
                description=description,
                next_check_in=_first_check_in(user, recurrence),
                recurrence=recurrence,
                num_missed_in_a_row=0,
                reminder=reminder,
            )
            user.commitments.append(new_commitment)
            await _save_and_message(ctx, f"New commitment: {new_commitment}")

    @commands.command(name="check-in")
    @commands.check(_is_registered)
    async def check_in(
        self, ctx: commands.Context, commitment: Commitment = _commitment_parameter
    ):
        """Check in your accountability commitment (mark as completed)"""

        user = users.member_id_to_user[ctx.author.id]
        time_until_commitment = commitment.next_check_in - user_time(
            user, datetime.now()
        )
        if time_until_commitment.days >= 1:
            raise commands.errors.UserInputError(
                "You aren't supposed to do this commitment yet! "
                f"Next check in is in {time_until_commitment.days} more day(s)"
            )

        commitment.num_missed_in_a_row = 0
        commitment.cycle_check_in()
        await _save_and_message(ctx, f"Checked in! {commitment}")

    @commands.command()
    @commands.check(_is_registered)
    async def delete(
        self, ctx: commands.Context, commitment: Commitment = _commitment_parameter
    ):
        """Delete an accountability commitment"""

        user = users.member_id_to_user[ctx.author.id]
        user.commitments.remove(commitment)
        await _save_and_message(ctx, f"Deleted commitment {commitment}")

    @commands.command()
    @commands.check(_is_registered)
    async def remind(
        self,
        ctx: commands.Context,
        commitment: Commitment = _commitment_parameter,
        reminder: _Time = _optional_reminder_parameter,
    ):
        """Set up or remove a reminder"""

        commitment.reminder = reminder
        await _save_and_message(ctx, f"Commitment updated: {commitment}")

    @commands.command()
    @commands.check(_is_registered)
    async def info(
        self,
        ctx: commands.Context,
        commitment: Commitment = _optional_commitment_parameter,
    ):
        """
        Display info about your commitment or profile

        Specify the name of your commitment to see its info, or leave blank to get
        your profile info
        """
        user = users.member_id_to_user[ctx.author.id]
        if commitment is None:
            await ctx.send(str(user))
            return
        await ctx.send(str(commitment))

    @commands.command(name="to-do")
    @commands.check(_is_registered)
    async def to_do(self, ctx: commands.Context):
        """Get a list of commitments to do today"""

        user = users.member_id_to_user[ctx.author.id]
        user_now = user_time(user, datetime.now())
        for commitment in user.commitments:
            if commitment.next_check_in.date() == user_now.date():
                await ctx.send(str(commitment))
                break

    @commands.command(name="toggle-active")
    @commands.check(_is_registered)
    async def toggle_active(self, ctx: commands.Context):
        """Toggles your profile between active and inactive"""
        user = users.member_id_to_user[ctx.author.id]
        user.is_active = not user.is_active
        await ctx.send(f"User activity updated:\n{user}")


def _find_commitment(user: User, commitment_name: str) -> Commitment | None:
    for commitment in user.commitments:
        if commitment.name == commitment_name:
            return commitment
    return None


def _first_check_in(user: User, recurrence: Recurrence) -> datetime:
    now = user_time(user, datetime.now().utcnow())
    midnight = datetime(
        year=now.year, month=now.month, day=now.day, hour=23, minute=59, second=59
    )
    return recurrence.next_occurence(midnight - timedelta(days=1))


async def _save_and_message(ctx: commands.Context, message: str) -> None:
    users.save()
    await ctx.send(message)
