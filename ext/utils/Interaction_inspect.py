import math
import re

from discord_components import Button, Interaction
from discord_components.component import Component, Select

from utils.custom_errors import OnlyAuthorError

PAGE_BUTTON_PATTERN = r'\(\d*?/\d*?\)'
VALUES_PATTERN = r'values->(.+)'


def inject(components: list[Component], values: dict) -> list[Component]:
    """Distribute values ​​evenly between message components\n
    The values ​​are placed at the end of the custom ids.
    Better not to change it after using this method

    Args
    ------
        components (list[Component]): List of components that you are going to pass to the message
        values (dict): Values ​​to be packed into components
        
    Return
    ------
        list[Component]: Components storing all specified values
    """
    list_of_component_type = [Button, Select]

    def unpack(components):
        list_of_components = []
        for component in components:
            if type(component) in list_of_component_type:
                list_of_components.append(component)
            elif isinstance(component, list):
                additional_list = unpack(component)
                list_of_components.extend(additional_list)
            else:
                raise TypeError('can work only with Button or Select')
        return list_of_components

    list_of_components = unpack(components)

    if not list_of_components:
        return []

    for component in list_of_components:
        component.id += "values"
    per_component = math.ceil(len(values) / len(list_of_components))

    for index, item in enumerate(values.items()):
        component = list_of_components[index // per_component]
        component.id += f"->{item[0]}:{repr(item[1])}"
        assert len(
            component.id
        ) <= 100, f'The maximum custom id length (100) has been reached. Try to pass values ​​in a list or tuple, so they take up less space\nID: {component.id}'

    return components


def get_values(interaction: Interaction) -> dict:
    """Returns the previously packed values ​​from interaction
    
    Args:
    -------
    interaction (Interaction): object obtained from a "button click" or "select" event
    """
    message = interaction.message
    action_rows = message.components

    values = {}
    for action_row in action_rows:
        for component in action_row:

            values_string = re.search(VALUES_PATTERN, component.id)

            try:
                values_string = values_string.group(1)
            except AttributeError:
                continue

            values_list = values_string.split('->')
            values_list = [obj.split(':') for obj in values_list]

            dictionary = dict(values_list)
            dictionary = {
                key: eval(value)
                for key, value in dictionary.items()
            }

            values |= dictionary

    return values


def check_page_change(interaction: Interaction, page: int):
    """Checks if the button was used to switch the page 'last' if the user wants to move to the last one. 

    Args:
    -------
        interaction (Interaction): object obtained from a "button click" or "select" event
        page (int): current page
        
    Returns
    -------
        old page number (int): if button to change page not used 
        new page number (int): if one of ⏮️◀️▶️ buttons used
        'last' (str): if ⏭️ button used
        'custom' (str): if the user wants to specify the page himself 
    """
    component = interaction.component
    if not isinstance(component, Button):
        return page

    if component.label:
        custom_change = re.search(PAGE_BUTTON_PATTERN, component.label)
        if custom_change:
            return 'custom'
        else:
            return page
    else:
        emoji = str(component.emoji)
        if emoji == str("⏮️"):
            return 0
        elif emoji == str("◀️"):
            return page - 1 if page > 0 else 0
        elif emoji == str("▶️"):
            return page + 1
        elif emoji == str("⏭️"):
            return 'last'
        else:
            return page


async def only_author(interaction):
    values = get_values(interaction)
    author = values.get('author')
    if author and author != interaction.author.id:
        await interaction.respond(
            content=
            f'Sorry, <@{author}> is the author of this message. Only he can use it'
        )
        raise OnlyAuthorError


def check_prefix(interaction: Interaction, prefix: str):
    if not interaction.component.id.startswith(prefix):
        return False
    return True
