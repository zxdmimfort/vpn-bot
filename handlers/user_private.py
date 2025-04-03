from asyncio.log import logger
from aiogram import F, Router, types
from aiogram.filters import Command, CommandStart, or_f
from sqlalchemy.ext.asyncio import AsyncSession


from db.repository import UserRepository
from kbds.menu_markups import Action, UserAction, get_user_actions_markup
from db.models import User

router = Router()
admins: tuple[str, ...] = ("aoi_dev", "mimfort")


# def register_callback(
#     action: str, handler: Callable[[types.CallbackQuery], Awaitable[None]]
# ) -> None:
#     async def wrapper(query: types.CallbackQuery) -> None:
#         print(f"Handling action: {action}")
#         await handler(query)

#     router.callback_query.register(wrapper, F.data == action)


# register_callback("settingup", lambda q: send_setting_up_vpn_connection(q.message))
# register_callback("adminmarkup", lambda q: send_admin_actions(q.message))
# register_callback("addcon", lambda q: add_connection(q.message))
# register_callback("conlist", lambda q: get_connections(q.message))


# @router.message(CommandStart())
# async def start_cmd(message: types.Message) -> None:
#     await message.answer(
#         "Hello! I'm a bot!",
#         reply_markup=reply.start_kb,
#     )


# @router.message()
# async def unknown_cmd(message: types.Message) -> None:
#     await message.answer("Unknown command!")


@router.message(or_f(Command("help"), CommandStart()))
async def send_basic_actions(
    message: types.Message,
    user: User | None,
) -> None:
    await message.answer(
        "Choose an action:",
        reply_markup=get_user_actions_markup(
            message.chat.username or "",
            admins,
            message.chat.id,
            user_id=user.id if user else None,
        ),
    )


# @router.message(Command("admin"))
# @admin_required(admins)
# async def send_admin_actions(message: Message) -> None:
#     await message.answer(
#         text="админские действия", reply_markup=get_admin_actions_markup()
#     )


@router.callback_query(UserAction.filter(F.action == Action.register))
async def send_register(
    query: types.CallbackQuery,
    callback_data: UserAction,
    session: AsyncSession,
    user: User | None,
) -> None:
    if not user:
        user = await UserRepository(session).create(
            chat_id=query.from_user.id,
            username=query.from_user.username,
            first_name=query.from_user.first_name,
        )
        text = f"Охайо, {query.from_user.username}!🖖"
    else:
        text = "Вы уже прошли регистрацию!"

    await query.answer(
        text,
        reply_markup=get_user_actions_markup(
            query.from_user.username or "",
            admins,
            query.from_user.id,
            user_id=user.id if user else None,
        ),
    )


# @router.message(Command("addcon"))
# async def add_connection(
#     message: types.Message,
#     session: AsyncSession,
# ) -> None:
#     api_client = get_async_client()
#     email = await api_client.add_connection(message.chat.username)
#     if not email:
#         await message.answer("Failed to create connection.")
#         return
#     connection_url = await api_client.get_connection_by_email(email)
#     con = Connection(
#         inbound=api_client.inbound_id,
#         email=email,
#         connection_url=connection_url,
#         user=user,
#         host="scvnotready.online",
#     )
#     session.add(con)
#     session.commit()
#     await message.answer(connection_url)


# @router.message(Command("conlist"))
# async def get_connections(message: Message, counter: int) -> None:
#     print(f"Counter: {counter}")
#     user = get_current_user_or_none(session, message)
#     if not user:
#         await message.answer("You need to register first!")
#         return
#     connections = (
#         session.execute(select(Connection).where(Connection.user_id == user.id))
#         .scalars()
#         .all()
#     )
#     answer = "Ваши подключения:\n" + "\n---------------\n".join(
#         [c.connection_url for c in connections]
#     )
#     await message.answer(answer)


# @router.message(Command("settingup"))
# async def send_setting_up_vpn_connection(message: Message) -> None:
#     await message.answer("Скачать nekoray, nekobox: https://matsuridayo.github.io/")
#     await message.answer_photo(photo=FSInputFile(path="img.png"), caption="")


@router.errors()
async def handle_errors(event: types.ErrorEvent) -> None:
    logger.critical("Critical error caused by %s", event.exception, exc_info=True)


# register_callback("register", lambda q: send_register(q.message))
