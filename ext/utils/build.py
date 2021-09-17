import inspect

from discord_components import Button, Interaction
from main import SEBot
from peewee import Query

from ..utils import Interaction_inspect
from .utils import wait_for_message, wait_message_from_author


async def update_message(bot: SEBot, builder,
                         interaction: Interaction) -> None:
    values = Interaction_inspect.get_values(interaction)
    author = values.get('author')
    if author and author != interaction.author.id:
        await interaction.respond(
            content=
            f'Sorry, <@{author}> is the author of this message. Only he can use it'
        )
        return

    page = values.get('page')
    if page or page == 0:
        page = Interaction_inspect.check_page_change(interaction, page)
    if page == 'custom':
        await interaction.respond(content="Enter page number")

        if author := values.get('author'):
            new_page = await wait_message_from_author(bot, interaction, author)
        else:
            new_page = await wait_for_message(bot, interaction)
        try:
            values['page'] = int(new_page) - 1
        except Exception:
            pass

        if inspect.iscoroutinefunction(builder):
            embed, components, values = await builder(values)
        else:
            embed, components, values = builder(values)
        components = Interaction_inspect.inject(components, values)
        await interaction.message.edit(embed=embed, components=components)

    else:
        values['page'] = page
        if selected := interaction.values:
            values['selected'] = selected[0]

        if inspect.iscoroutinefunction(builder):
            embed, components, values = await builder(values)
        else:
            embed, components, values = builder(values)
        components = Interaction_inspect.inject(components, values)
        await interaction.respond(type=7, embed=embed, components=components)


def get_last_page(query: Query):
    page = (query.count() - 1) // 10
    return page if page >= 0 else 0


def cut_elements(query: Query, page):
    elements = query.paginate(page + 1, 10).dicts().execute()

    expected_last_page = get_last_page(query)

    if not elements and page != expected_last_page:
        elements = cut_elements(query, expected_last_page)

    return elements


def get_page(page, last_page):
    if page == 'last':
        page = last_page
    if page > last_page:
        page = last_page
    if page < 0:
        page = 0
    return page


def page_implementation(values: dict, query: Query):
    """
    Args:
        values (dict): values getting from inspection
        elements (Union[dict, list]): all the elements from which you need to select the ones you need by page number

    Returns:
        page (int): current page
        last_page (int): total number of pages
        elements (Union[dict, list]): elements to be displayed on the current page
    """
    last_page = get_last_page(query)
    page = values['page']
    page = get_page(page, last_page)
    values['page'] = page
    elements = cut_elements(query, page)
    return page, last_page, elements


def build_page_components(page, last_page, prefix):
    return [
        Button(
            emoji=str("⏮️"), id=prefix + 'track_previous', disabled=page == 0),
        Button(
            emoji=str("◀️"), id=prefix + 'arrow_backward', disabled=page == 0),
        Button(label=f"({page+1}/{last_page+1})",
               disabled=False,
               id=prefix + 'page_number'),
        Button(emoji=str("▶️"),
               id=prefix + 'arrow_forward',
               disabled=page == last_page),
        Button(emoji=str("⏭️"),
               id=prefix + 'track_next',
               disabled=page == last_page),
    ] if last_page != 0 else []
