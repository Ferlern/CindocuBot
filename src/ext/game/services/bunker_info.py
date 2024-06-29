from enum import Enum

RULES = "# Правила игры Бункер\n> - Игра является голосовой, поэтому для неё является обязательным участие в голосовом канале.\n> - Соблюдайте нормы морали и не оскорбляйте других участников.\n## Процесс игры\n1. Всем игрокам выдается карточка с их атрибутами, в которую входят:\n\n> - Имя\n> - Пол и возраст\n> - Телосложение\n> - Профессия\n> - Хобби\n> - Фобия\n> - Случайная характеристика\n> - Дополнительная информация\n> - Инвентарь\n\n2. Во время своего хода вы должны раскрыть минимум один из своих атрибутов и доказать, почему именно вас должны взять в **Бункер**.\n\n\\* Это можно делать путем грамотного описания своих характеристик, рассказывая, почему они пригодятся всем остальным участникам в бункере.\n\\* Помните, что в бункере останетесь не только вы одни и думайте наперед, что может помешать вашему успешному выживанию во время катаклизма.\n\n3. После окончания круга ходов игроки коллективно выбирают игроков для исключения, которые по их мнению точно приведут к плохим последствия для бункера.\n\n> После первого раунда голосование не проводится по правилам игры.\n\n4. Путем голосования один из игроков в конце раунда будет исключен и не сможет больше участвовать в игре.\n5. Игра продолжается до тех пор, пока выживших не останется вдвое меньше количества изначальных игроков.\n\n> При нечетном количестве игроков округление идет в меньшую сторону."
CHANNEL_ART = 'https://i.ibb.co/j6VPrFn/e3c7b7fccb6ab3b1e427d3d32df63fc4-transformed.webp'
END_GAME_ART = 'https://i.ibb.co/8zZFfmM/laughter-merriment-fill-air-as-people-gather-drink-medieval-tavern-designe-852340-6757.webp'

class SunCataclism(Enum): 
    NAME = "Солнечный Катаклизм"
    DESC = "Солнце приблизилось к поверхности Земли так близко, как никогда ранее. Остаются считанные часы до полной глобальной засухи."
    COLOR = 0xDC143C
    PHOTO = 'https://imgur.com/eYhbbYJ.jpg'

class GlobalGlasiation(Enum):
    NAME = "Глобальное Оледенение"
    DESC = "Защитный слой Земли был разрушен. Земля с каждой секундой теряет свою температуру и в ближайший час абсолютно все вокруг замерзнет навсегда."
    COLOR = 0xE0FFFF
    PHOTO = 'https://imgur.com/jNoR8Jw.jpg'

class Cataclisms(Enum):
    SUN_CATACLISM = SunCataclism
    GLOBAL_GLASIATION = GlobalGlasiation

class BunkerStuff(Enum):
    MEDICINE = "Запасы лекарств"
    CLEAN_CLOTHES = "Чистая одежда"
    CARVING_KNIFE = "Разделочный нож"
    DUMBBELLS = "Гантели"
    BEDS_FOR_PLANTING = "Грядки для посадки растений"
    BEDS_FOR_SLEEPING = "Кровати для сна"
    WATER_SUPPLY = "Экстренные запасы воды"
    LOOM = "Ткацкий станок"
    OVEN = "Духовая печь"

class MaleNames(Enum):
    ALAN = "Алан"
    BEN = "Бен"
    BRUNO = "Бруно"
    DANIEL = "Даниэль"
    DAVID = "Давид"
    EDGAR = "Эдгар"
    EDVARD = "Эдвард"
    ERIK = "Эрик"
    FELIX = "Феликс"
    JOHN = "Джон"
    GUY = "Гай"
    GARRY = "Гарри"
    IAN = "Иан"
    JACK = "Джек"
    CARL = "Карл"
    LEO = "Лео"
    LUKE = "Люк"
    MARK = "Марк"
    NIL = "Нил"
    OLIVER = "Оливер"
    OSKAR = "Оскар"
    POL = "Поль"
    RALF = "Ральф"
    SAM = "Сэм"
    TOM = "Том"

class FemaleNames(Enum):
    ANNA = "Анна"
    BELLA = "Белла"
    CLARA = "Клара"
    FAY = "Фэй"
    GRAYS = "Грейс"
    HANNA = "Ханна"
    IDA = "Ида"
    JAINE = "Джейн"
    LIA = "Лиа"
    LIZA = "Лиза"
    LILY = "Лили"
    MARIA = "Мария"
    MAYA = "Майа"
    NORA = "Нора"
    OLIVIA = "Оливия"
    PAULA = "Паула"
    ROSE = "Роза"
    SARA = "Сара"
    TINA = "Тина"
    URSULA = "Урсула"
    VERA = "Вера"
    VIKI = "Вики"
    VIVIAN = "Вивиан"
    ELZA = "Эльза"

class Sex(Enum):
    MALE = "Мужчина"
    FEMALE = "Женщина"

class MaleThumbs(Enum):
    AVATAR1 = 'https://i.ibb.co/vmhL91N/image.png'
    AVATAR2 = 'https://i.ibb.co/LCx5PSL/image2.png'
    AVATAR3 = 'https://i.ibb.co/gv9dKxq/image4.png'
    AVATAR4 = 'https://i.ibb.co/pK886L8/image5.png'
    AVATAR5 = 'https://i.ibb.co/58vfnsH/image6.png'
    AVATAR6 = 'https://i.ibb.co/10FSfNd/image8.png'

class FemaleThumbs(Enum):
    AVATAR1 = 'https://i.ibb.co/hKG3TZx/image3.png'
    AVATAR2 = 'https://i.ibb.co/pddqhHX/image7.png'
    AVATAR3 = 'https://i.ibb.co/V2HJTm6/image9.png'
    AVATAR4 = 'https://i.ibb.co/ydQCsg3/image10.png'
    AVATAR5 = 'https://i.ibb.co/D9v9VN2/image11.png'
    AVATAR6 = 'https://i.ibb.co/s117VWy/image12.png'


class BodyType(Enum):
    SPORT = "Спортивное"
    COMMON = "Обычное"
    WEIGHT_LACK = "Недостаток веса"
    OVERWEIGHT_MILD = "Слабый переизбыток веса"
    OVERWEIGHT_SEVERE = "Сильный переизбыток веса"

class Work(Enum):
    HARDWORKING = "Трудолюбивость"
    LAZY = "Ленивость"
    RESPONSIBLE = "Ответственность"
    IRRESPONSIBLE = "Безответственность"
    CONSCIENTIOUS = "Добросовестность"
    UNSCRUPULOUS = "Недобросовестноость"
    INITIATIVE = "Инициативность"
    PASSIVE = "Пассивность"

class Relationships(Enum):  
    INTROVERTED = "Замкнутость"
    SOCIABLE = "Общительность"
    HONEST = "Честность с людьми"
    DECEITFUL = "Лживость с людьми"
    INDEPENDANT = "Самостоятельность"
    COMFORMING = "Комфортность в общении"
    RUDE = "Грубость"
    POLITE = "Вежливый"

class ThingsAttitude(Enum):
    CAREFUL = "Аккуратность"
    SLOBBY = "Неряшливость"
    THRIFTY = "Бережливость"
    CARELESS = "Небрежность"
    GREEDY = "Жадность"
    GENEROUS = "Щедрость"

class SelfEsteem(Enum):
    DEMANDING = "Требовательность"
    SELF_CRITICAL = "Самокритичность"
    SELFISH = "Эгоистичность"
    SELF_CENTERED = "Эгоцентричность"
    TESTY = "Вспыльчивость"

class Intellect(Enum):
    SENSIBLE = "Рассудительность"
    TRICKY = "Хитрость"
    SAVVY = "Сообразительность"
    SILLY = "Глуповатость"
    CURIOUS = "Сообразительность"
    FRIVOLOUS = "Легкомысленность"

class Morality(Enum):
    FAIR = "Справедливость"
    RESPONSIVE = "Отзывчивость"
    KIND = "Доброта"
    TOXIC = "Токсичность"
    CRUEL = "Жестокость"

class Character(Enum):
    WORK = Work
    RELATIONSHIPS = Relationships
    THINGS_ATTITUDE = ThingsAttitude
    SELF_ESTEEM = SelfEsteem
    INTELLECT = Intellect
    MORALITY = Morality
    
class Professions(Enum):
    RECRUT = "Наёмник"
    MINER = "Шахтёр"
    FARMER = "Фермер"
    BUILDER = "Строитель"
    DOCTOR = "Лекарь"
    POTTER = "Гончар"
    JESTER = "Шут"
    WEAWER = "Ткач"
    STONEKUTTER = "Каменотёс"
    TANNER = "Кожевник"
    JEWELER = "Ювелир"
    SHOEMAKER = "Сапожник"
    BAKER = "Пекарь"
    BREWER = "Пивовар"
    BARBER = "Пирюльник"
    POACHER = "Браконьер"

class Hobby(Enum):
    HUNT = "Охотник"
    MUSIC = "Музыкант"
    DANCING = "Танцор"
    ARCHERY = "Лучник"
    TRADE = "Торговец"
    BREEDING = "Животновод"
    COOKING = "Кулинар"
    DRAWING = "Художник"
    ALPINISM = "Скалолаз"
    SINGING = "Певец"

class Professionalism(Enum):
    BEGINNER = "Начинающий" # до трех месяцев стажа
    TRAINEE = "Стажёр" # до шести месяцев стажа
    ADVANCED = "Продвинутый" # год стажа
    EXPERIENCED = "Опытный" # от 2 до 5 лет стажа
    EXPERT = "Эксперт" # от 6 до 15 лет стажа
    MASTER = "Мастер" # от 15 лет стажа

class Phobias(Enum):
    ARACHNOPHOBIA = "Арахнофобия" # страх пауков
    CLAUSTROPHOBIA = "Клаустрофобия" # страх замкнутых пространств
    MYSOPHOBIA = "Мизофобия" # страх загрязнения
    NOSOPHOBIA = "Нозофобия" # страх увечья, неизлечимой болезни, заражения
    XENOPHOBIA = "Ксенофобия" # страх перед посторонними людьми
    NYCTOPHOBIA = "Никтофобия" # страх темноты, ночи
    HEMATOPHOBIA = "Гематофобия" # страх вида крови
    PYROPHOBIA = "Пирофобия" # страх огня

class ExtraInfo(Enum):
    HAS_CHILDREN = "Есть дети"
    HAD_LOVER = "Была возлюбленная"
    SUICIDAL = "Суицидальный"
    CHILDFREE = "Чайлдфри"
    DRUNK = "Пьянчуга"
    STRONG = "Силач"

class ExtraStuff(Enum):
    SHARP_SWORD = "Острый меч"
    FLINT = "Кремень"
    BOW_WITH_ARROWS = "Лук со стрелами"
    BEER_BARREL = "Бочонок с пивом"
    GOLD_BRACELET = "Золотой браслет"
    FISHING_ROD = "Удочка"
    FIDDLE = "Гусли"
    FLUTE = "Флейта"
    BALL_OF_ROPE = "Моток веревки"
    WHEAT_SEEDS = "Семена пшеницы"
