import difflib
import io
import logging
import re

import aiohttp
import discord
import langdetect
from googletrans import Translator
from utils.custom_context import Context

SPOILER = r'\|\|.+?\|\|'
TEXT_STYLE = r'\*.+?\*'
ESCAPE = r'\\ '
LINK_OR_MENTION = r'<.+?>'
LINE_THROUGH = r'~~.+?~~'
UNDERLINE = r'__.+?__'
CODE = r'`.+?`'
MARKDOWN_PATTERN = r'(^[`\\|*<!@#&~_>]+)(.+?)([`\\|*<!@#&~_>]+?$)'
MARKDOWN_PATTERNS = (SPOILER, TEXT_STYLE, LINK_OR_MENTION, LINE_THROUGH,
                     UNDERLINE, CODE)

CODE_BLOCK = r'```.*?\n{0,1}.+?\n{0,1}```'

logger = logging.getLogger('Arctic')
translator = Translator()


def similarity(s1: str, s2: str) -> float:
    normalized1 = s1.lower()
    normalized2 = s2.lower()
    matcher = difflib.SequenceMatcher(None, normalized1, normalized2)
    return matcher.ratio()


def translation_normalizer(old_text: str, new_text: str):
    old_text_markdowns: list[str] = []
    new_text_markdowns: list[str] = []

    new_text = new_text.replace('\\ ', '\\')

    for _ in range(2):
        for pattern in MARKDOWN_PATTERNS:
            old_text_markdowns.extend(re.findall(pattern, old_text))
            new_text_markdowns.extend(re.findall(pattern, new_text))
            assert len(old_text_markdowns) == len(new_text_markdowns), f'len({old_text_markdowns}) != len({new_text_markdowns})'

        for old_markdown, new_markdown in zip(old_text_markdowns,
                                              new_text_markdowns):
            old_markdown_string = re.search(
                MARKDOWN_PATTERN,
                old_markdown
            ).group(2)
            new_markdown_string = re.search(
                MARKDOWN_PATTERN,
                new_markdown
            ).group(2)
            
            if not old_markdown_string.startswith(' ') and not old_markdown_string.endswith(' '):
                fixed_new_markdown = new_markdown.replace(
                    new_markdown_string,
                    new_markdown_string.strip(' ')
                )
                new_text = new_text.replace(new_markdown, fixed_new_markdown)

    return new_text


class CodeBlock:
    def __init__(self, text: str) -> None:
        self.text = text

    def search(self):
        self.blocks = re.findall(CODE_BLOCK, self.text)
        self.prepared_text = re.sub(CODE_BLOCK, '<code_block>', self.text)

    def get_prepared(self):
        return self.prepared_text

    def return_blocks(self, new_text: str):
        for block in self.blocks:
            new_text = re.sub('<code_block>', block, new_text, count=1)
        return new_text

    def __len__(self):
        return len(self.blocks) * 12


class MessageController:
    def __init__(self, bot) -> None:
        self.channels = bot.config['auto_translation']['channels']
        self.lang = bot.config['auto_translation']['lang']

    async def check(self, ctx: Context):
        if not ctx.guild or ctx.channel.id not in self.channels:
            return

        content: str = ctx.message.content
        codeblock = CodeBlock(content)
        codeblock.search()
        content = codeblock.get_prepared()

        if not content or content.startswith('http'): return
        attachments = ctx.message.attachments

        try:
            lang = langdetect.detect(content)
            if lang == 'en':
                return
        except langdetect.LangDetectException:
            return

        if len(content) - len(codeblock) > 10:
            await ctx.message.delete()
            translated = translator.translate(content, dest=self.lang).text
        else:
            translated = translator.translate(content, dest=self.lang).text
            if similarity(content, translated) > 0.5:
                return
            await ctx.message.delete()

        translated = translation_normalizer(content, translated)
        translated = codeblock.return_blocks(translated)
        logger.debug(f'{codeblock.text} -> {translated}')

        weebhoks = await ctx.channel.webhooks()
        weebhoks = list(
            filter(lambda weebhok: weebhok.name == 'AutoTranslate', weebhoks))
        try:
            weebhok = weebhoks[0]
        except IndexError:
            weebhok = await ctx.channel.create_webhook(
                name='AutoTranslate',
                avatar=ctx.bot.user.avatar,
                reason='Create webhook for send translated message')

        files = []
        async with aiohttp.ClientSession() as session:
            for attachment in attachments:
                async with session.get(attachment.url) as resp:
                    if resp.status != 200:
                        continue
                    data = io.BytesIO(await resp.read())
                    files.append(
                        discord.File(data, filename=attachment.filename))

        await weebhok.send(content=translated,
                           files=files,
                           username=ctx.author.name,
                           avatar_url=ctx.author.avatar_url)
