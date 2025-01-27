from asyncio import Queue
from dataclasses import dataclass
from functools import partial
from logging import getLogger

from telegram.constants import ParseMode
from telegram.ext import ContextTypes, TypeHandler

from bot.context import Context
from bot.text.lib import create_solver
from bot.text.types import Solver

from ._lib import normalize_if_url


@dataclass
class ApiTextUpdate:
    chat_id: int
    text: str


_L = getLogger(__name__)


async def _solve_api_text(
    update: ApiTextUpdate,
    context: ContextTypes.DEFAULT_TYPE,
    *,
    solve: Solver,
) -> None:
    unknown_text = update.text.strip()
    if not unknown_text:
        _L.debug("ignored empty message")
        return

    unknown_text = await normalize_if_url(unknown_text)

    answer = await solve(unknown_text)
    if not answer:
        _L.debug(f"no answer from {unknown_text}")
        return

    await context.bot.send_message(
        update.chat_id,
        f"`{answer.text}`",
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=answer.keyboard,
        link_preview_options=answer.link_preview,
    )


async def enqueue_update(*, chat_id: int, text: str, queue: Queue[object]) -> None:
    await queue.put(ApiTextUpdate(chat_id=chat_id, text=text))


def create_text_api_handler(context: Context):
    solve = create_solver(context)
    return TypeHandler(
        type=ApiTextUpdate,
        callback=partial(_solve_api_text, solve=solve),
    )
