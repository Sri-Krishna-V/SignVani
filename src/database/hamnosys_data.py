"""
HamNoSys Data for ISL Glosses

Expanded vocabulary with HamNoSys notation based on DGS (German Sign Language)
Corpus patterns. These provide syntactically valid HamNoSys that will animate
properly with CWASA avatars.

Note: These are DGS-based approximations. For authentic ISL, replace with
data from ISLRTC or ISL linguists.

Reference: https://ling.meine-dgs.de/ (Public DGS Corpus)
"""

from typing import Dict

# =============================================================================
# GLOSS TO HAMNOSYS MAPPINGS
# Organized by category for easier maintenance
# =============================================================================

# -----------------------------------------------------------------------------
# GREETINGS & COMMON PHRASES
# -----------------------------------------------------------------------------
GREETINGS = {
    'HELLO': 'hamflathand,hamextfingeru,hampalmout,hamshoulders,hammover,hamrepeat',
    'GOODBYE': 'hamflathand,hamextfingeru,hampalmout,hamshoulders,hammoved,hamrepeat',
    'GOOD': 'hamflathand,hampalmu,hamchin,hammoveo',
    'BAD': 'hamflathand,hampalmd,hamchin,hammoveo',
    'MORNING': 'hamflathand,hampalmu,hamlowerarm,hammoveu',
    'AFTERNOON': 'hamflathand,hampalmd,hamchest,hammoved',
    'EVENING': 'hamflathand,hampalmd,hamshoulders,hammoved',
    'NIGHT': 'hamflathand,hampalmd,hamchest,hammoved,hamarcd',
    'WELCOME': 'hamflathand,hampalmu,hamchest,hammovei,hamarcu',
    'THANK': 'hamflathand,hampalmu,hamchin,hammoveo,hammoved',
    'THANKS': 'hamflathand,hampalmu,hamchin,hammoveo,hammoved',
    'PLEASE': 'hamflathand,hampalml,hamchest,hamcircle',
    'SORRY': 'hamfist,hampalml,hamchest,hamcircle',
    'EXCUSE': 'hamflathand,hampalmd,hamlowerarm,hammover',
}

# -----------------------------------------------------------------------------
# PRONOUNS
# -----------------------------------------------------------------------------
PRONOUNS = {
    'I': 'hamfinger2,hamextfingeri,hampalml,hamchest',
    'ME': 'hamfinger2,hamextfingeri,hampalml,hamchest',
    'MY': 'hamflathand,hampalmi,hamchest',
    'MINE': 'hamflathand,hampalmi,hamchest,hamrepeat',
    'YOU': 'hamfinger2,hamextfingero,hampalmout,hamneutralspace',
    'YOUR': 'hamflathand,hampalmo,hamneutralspace',
    'YOURS': 'hamflathand,hampalmo,hamneutralspace,hamrepeat',
    'HE': 'hamfinger2,hamextfingerr,hampalmout,hamneutralspace',
    'SHE': 'hamfinger2,hamextfingerr,hampalmout,hamneutralspace',
    'HIS': 'hamflathand,hampalmr,hamneutralspace',
    'HER': 'hamflathand,hampalmr,hamneutralspace',
    'IT': 'hamfinger2,hamextfingero,hampalmout,hamneutralspace',
    'WE': 'hamfinger2,hamextfingeri,hampalml,hamchest,hamarco',
    'OUR': 'hamflathand,hampalmi,hamchest,hamarco',
    'THEY': 'hamfinger2,hamextfingero,hampalmout,hamneutralspace,hammover',
    'THEIR': 'hamflathand,hampalmo,hamneutralspace,hammover',
    'WHO': 'hamfinger2,hamextfingeru,hampalml,hamchin,hamcircle',
    'WHAT': 'hamflathand,hampalmu,hamneutralspace,hammover,hamrepeat',
    'WHERE': 'hamfinger2,hamextfingeru,hampalmout,hamneutralspace,hammover',
    'WHEN': 'hamfinger2,hamextfingeru,hampalml,hamwrist,hamcircle',
    'WHY': 'hamfinger2,hamextfingeru,hamforehead,hammoveo',
    'HOW': 'hamfist,hamthumboutmod,hampalmu,hamneutralspace,hamcircle',
    'THIS': 'hamfinger2,hamextfingerd,hampalmout,hamneutralspace',
    'THAT': 'hamfinger2,hamextfingero,hampalmout,hamneutralspace,hammoveo',
    'THESE': 'hamfinger2,hamextfingerd,hampalmout,hamneutralspace,hammover',
    'THOSE': 'hamfinger2,hamextfingero,hampalmout,hamneutralspace,hammover',
}

# -----------------------------------------------------------------------------
# COMMON VERBS
# -----------------------------------------------------------------------------
VERBS = {
    'BE': 'hamfinger2,hamextfingero,hampalml,hamchin,hammoveo',
    'IS': 'hamfinger2,hamextfingero,hampalml,hamchin,hammoveo',
    'AM': 'hamfinger2,hamextfingeri,hampalml,hamchest',
    'ARE': 'hamfinger2,hamextfingero,hampalmout,hamneutralspace,hamarco',
    'WAS': 'hamflathand,hampalml,hamshoulders,hammoveo',
    'WERE': 'hamflathand,hampalmout,hamneutralspace,hammoveo',
    'HAVE': 'hamflathand,hampalmi,hamchest',
    'HAS': 'hamflathand,hampalmi,hamchest',
    'HAD': 'hamflathand,hampalmi,hamchest,hammoveo',
    'DO': 'hamfist,hampalmd,hamneutralspace,hammoved',
    'DOES': 'hamfist,hampalmd,hamneutralspace,hammoved',
    'DID': 'hamfist,hampalmd,hamneutralspace,hammoveo',
    'WILL': 'hamflathand,hampalmout,hamcheek,hammoveo',
    'WOULD': 'hamflathand,hampalmout,hamcheek,hammoveo,hamrepeat',
    'CAN': 'hamfist,hampalmd,hamneutralspace,hammoved,hammoved',
    'COULD': 'hamfist,hampalmd,hamneutralspace,hammoved',
    'SHOULD': 'hamfinger2,hamextfingerd,hampalml,hamneutralspace,hammoved',
    'MUST': 'hamfinger2,hamextfingerd,hampalmout,hamneutralspace,hammoved',
    'MAY': 'hamflathand,hampalmu,hamneutralspace,hammoveu',
    'MIGHT': 'hamflathand,hampalmu,hamneutralspace,hammoveu,hamrepeat',
    'GO': 'hamfinger2,hamextfingero,hampalmout,hamneutralspace,hammoveo',
    'COME': 'hamfinger2,hamextfingeri,hampalmout,hamneutralspace,hammovei',
    'SEE': 'hamfinger2,hamextfingero,hampalml,hameyes,hammoveo',
    'LOOK': 'hamfinger2,hamextfingero,hampalml,hameyes,hammoveo',
    'WATCH': 'hamfinger23,hamextfingero,hampalmd,hameyes,hammoveo',
    'HEAR': 'hamfinger2,hamextfingeru,hampalml,hamear',
    'LISTEN': 'hamcee12,hampalml,hamear,hamrepeat',
    'SAY': 'hamfinger2,hamextfingero,hampalml,hammouth,hammoveo',
    'SPEAK': 'hamfinger2,hamextfingero,hampalml,hammouth,hammoveo,hamrepeat',
    'TALK': 'hamfinger2,hamextfingero,hampalml,hammouth,hammoveo,hamrepeat',
    'TELL': 'hamfinger2,hamextfingero,hampalml,hamchin,hammoveo',
    'THINK': 'hamfinger2,hamextfingeru,hampalml,hamforehead',
    'KNOW': 'hamflathand,hampalmd,hamforehead',
    'UNDERSTAND': 'hamfinger2,hamextfingeru,hampalml,hamforehead,hammoveu',
    'LEARN': 'hamflathand,hampalmu,hamforehead,hammoveu',
    'TEACH': 'hamflathand,hampalmo,hamforehead,hammoveo',
    'STUDY': 'hamflathand,hampalmu,hamneutralspace,hamfingerplay',
    'READ': 'hamfinger23,hamextfingerd,hampalml,hamneutralspace,hammoved',
    'WRITE': 'hampinch12,hampalmd,hamneutralspace,hammover',
    'WANT': 'hamcee12,hampalmu,hamneutralspace,hammovei',
    'NEED': 'hamfinger2,hamextfingerd,hampalml,hamneutralspace,hammoved',
    'LIKE': 'hamflathand,hampalmi,hamchest,hammoveo',
    'LOVE': 'hamfist,hampalmi,hamchest',
    'HATE': 'hamfinger23,hamextfingero,hampalmout,hamchest,hammoveo',
    'HELP': 'hamflathand,hampalmu,hamneutralspace,hammoveu',
    'GIVE': 'hamflathand,hampalmu,hamneutralspace,hammoveo',
    'GET': 'hamcee12,hampalmu,hamneutralspace,hammovei',
    'TAKE': 'hamcee12,hampalmd,hamneutralspace,hammovei',
    'MAKE': 'hamfist,hampalmd,hamneutralspace,hamrepeat',
    'USE': 'hamfist,hampalmd,hamneutralspace,hamcircle',
    'FIND': 'hampinch12open,hampalmd,hamneutralspace,hammoveu',
    'PUT': 'hamflathand,hampalmd,hamneutralspace,hammoved',
    'SHOW': 'hamfinger2,hamextfingero,hampalmout,hamneutralspace,hammoveo',
    'TRY': 'hamfist,hampalml,hamneutralspace,hammoveo',
    'CALL': 'hamcee12,hampalml,hamear,hammoveo',
    'ASK': 'hamfinger2,hamextfingeru,hampalmout,hamneutralspace,hamarci',
    'WORK': 'hamfist,hampalmd,hamneutralspace,hamrepeat',
    'PLAY': 'hamfinger2345,hampalmu,hamneutralspace,hamrepeat',
    'RUN': 'hamfinger2,hamextfingero,hampalmout,hamneutralspace,hammoveo,hamfast',
    'WALK': 'hamflathand,hampalmd,hamneutralspace,hamaltmotion',
    'STAND': 'hamfinger23,hamextfingerd,hampalmd,hamneutralspace',
    'SIT': 'hamfinger23,hamextfingerd,hampalmd,hamneutralspace,hammoved',
    'STOP': 'hamflathand,hampalml,hamneutralspace',
    'START': 'hamfinger2,hamextfingerr,hampalmd,hamneutralspace,hammover',
    'BEGIN': 'hamfinger2,hamextfingerr,hampalmd,hamneutralspace,hammover',
    'FINISH': 'hamflathand,hampalmd,hamneutralspace,hammoved,hamfast',
    'END': 'hamflathand,hampalmd,hamneutralspace,hammoved',
    'WAIT': 'hamflathand,hampalmu,hamneutralspace,hamfingerplay',
    'LIVE': 'hamflathand,hampalmi,hamchest,hammoveu',
    'DIE': 'hamflathand,hampalmu,hamneutralspace,hampalmd',
    'EAT': 'hampinchall,hampalmi,hammouth,hamrepeat',
    'DRINK': 'hamcee12,hampalml,hammouth,hammoveu',
    'SLEEP': 'hamflathand,hampalmi,hamcheek',
    'WAKE': 'hampinch12,hampalml,hameyes,hammoveo',
    'OPEN': 'hamflathand,hampalmd,hamneutralspace,hammoveo',
    'CLOSE': 'hamflathand,hampalmd,hamneutralspace,hammovei',
    'BUY': 'hamflathand,hampalmu,hamneutralspace,hammoveo',
    'SELL': 'hamflathand,hampalmd,hamneutralspace,hammoveo',
    'PAY': 'hamflathand,hampalmu,hamneutralspace,hammoveo',
    'MEET': 'hamfinger2,hamextfingeru,hampalmout,hamneutralspace,hammovei',
    'FEEL': 'hamfinger2,hamextfingeru,hampalmi,hamchest',
}

# -----------------------------------------------------------------------------
# COMMON NOUNS
# -----------------------------------------------------------------------------
NOUNS = {
    'PERSON': 'hamflathand,hampalml,hamneutralspace,hammoved',
    'PEOPLE': 'hamflathand,hampalml,hamneutralspace,hammoved,hamrepeat',
    'MAN': 'hamflathand,hampalml,hamforehead,hammoved',
    'WOMAN': 'hamflathand,hampalml,hamchin,hammoved',
    'BOY': 'hamcee12,hampalml,hamforehead',
    'GIRL': 'hamcee12,hampalml,hamcheek',
    'CHILD': 'hamflathand,hampalmd,hamneutralspace,hammoved',
    'CHILDREN': 'hamflathand,hampalmd,hamneutralspace,hammoved,hamrepeat',
    'BABY': 'hamflathand,hampalmu,hamneutralspace,hamarcu',
    'MOTHER': 'hamflathand,hamthumboutmod,hampalml,hamchin',
    'FATHER': 'hamflathand,hamthumboutmod,hampalml,hamforehead',
    'PARENT': 'hamflathand,hampalml,hamforehead,hamchin',
    'FAMILY': 'hamfinger2345,hampalmo,hamneutralspace,hamcircle',
    'FRIEND': 'hamfinger2,hamextfingeru,hampalmout,hamneutralspace,hamrepeat',
    'TEACHER': 'hamflathand,hampalmo,hamforehead,hammoveo,hamrepeat',
    'STUDENT': 'hamflathand,hampalmu,hamforehead,hammovei',
    'DOCTOR': 'hamflathand,hampalmd,hamwrist,hamrepeat',
    'NAME': 'hamfinger23,hamextfingerr,hampalmd,hamneutralspace,hamrepeat',
    'HOUSE': 'hamflathand,hampalmi,hamneutralspace,hamarcu',
    'HOME': 'hampinchall,hampalmi,hamcheek',
    'ROOM': 'hamflathand,hampalmout,hamneutralspace,hammover',
    'DOOR': 'hamflathand,hampalmo,hamneutralspace,hamarco',
    'WINDOW': 'hamflathand,hampalmi,hamneutralspace,hammoveu',
    'TABLE': 'hamflathand,hampalmd,hamneutralspace',
    'CHAIR': 'hamfinger23,hamextfingerd,hampalmd,hamneutralspace,hammoved',
    'BED': 'hamflathand,hampalml,hamcheek',
    'FOOD': 'hampinchall,hampalmd,hammouth',
    'WATER': 'hamfinger23spread,hampalml,hamchin,hamrepeat',
    'BOOK': 'hamflathand,hampalmu,hamneutralspace,hamarcu',
    'PAPER': 'hamflathand,hampalmd,hamneutralspace,hammover',
    'PEN': 'hampinch12,hampalmd,hamneutralspace,hammover',
    'PHONE': 'hamcee12,hampalml,hamear',
    'COMPUTER': 'hamfist,hampalmd,hamneutralspace,hamcircle',
    'SCHOOL': 'hamflathand,hampalmd,hamneutralspace,hamrepeat',
    'WORK': 'hamfist,hampalmd,hamneutralspace,hamrepeat',
    'JOB': 'hamfist,hampalmd,hamneutralspace,hamrepeat',
    'MONEY': 'hamflathand,hampalmu,hamneutralspace,hamrepeat',
    'TIME': 'hamfinger2,hamextfingerd,hampalml,hamwrist',
    'DAY': 'hamflathand,hampalmd,hamneutralspace,hamarcu',
    'WEEK': 'hamfinger2,hamextfingerr,hampalmd,hamneutralspace,hammover',
    'MONTH': 'hamfinger2,hamextfingerd,hampalml,hamneutralspace,hammoved',
    'YEAR': 'hamfist,hampalml,hamneutralspace,hamcircle',
    'TODAY': 'hamflathand,hampalmu,hamneutralspace,hammoved',
    'TOMORROW': 'hamflathand,hampalmout,hamcheek,hammoveo',
    'YESTERDAY': 'hamthumb,hampalml,hamcheek,hammoveo',
    'NOW': 'hamflathand,hampalmu,hamneutralspace,hammoved',
    'ALWAYS': 'hamfinger2,hamextfingero,hampalmout,hamneutralspace,hamcircle',
    'NEVER': 'hamflathand,hampalmout,hamneutralspace,hammoved,hamarcd',
    'SOMETIMES': 'hamfinger2,hamextfingeru,hampalml,hamneutralspace,hamrepeat',
    'CAR': 'hamfist,hampalml,hamneutralspace,hamrepeat',
    'BUS': 'hamflathand,hampalmout,hamneutralspace,hammoveo',
    'TRAIN': 'hamfinger23,hamextfingerr,hampalmd,hamneutralspace,hammover',
    'CITY': 'hamflathand,hampalmi,hamneutralspace,hamarcu,hamrepeat',
    'COUNTRY': 'hamflathand,hampalmd,hamelbow,hamcircle',
    'WORLD': 'hamfist,hampalml,hamneutralspace,hamcircle',
    'THING': 'hamflathand,hampalmu,hamneutralspace,hammover',
    'PLACE': 'hamflathand,hampalmd,hamneutralspace,hamcircle',
    'PROBLEM': 'hamfinger23,hamextfingerd,hampalml,hamforehead,hamrepeat',
    'QUESTION': 'hamfinger2,hamextfingero,hampalmout,hamneutralspace,hamarci',
    'ANSWER': 'hamfinger2,hamextfingero,hampalml,hamchin,hammoveo',
    'IDEA': 'hamfinger2,hamextfingeru,hampalml,hamforehead,hammoveu',
    'REASON': 'hamfinger2,hamextfingeru,hampalml,hamforehead,hammoveo',
    'WAY': 'hamflathand,hampalmout,hamneutralspace,hammoveo',
    'PART': 'hamflathand,hampalmd,hamneutralspace,hammover',
    'GROUP': 'hamcee12,hampalmo,hamneutralspace,hamcircle',
    'SIGN': 'hamfinger2,hamextfingero,hampalmout,hamneutralspace,hamaltmotion',
    'LANGUAGE': 'hamflathand,hampalmout,hamneutralspace,hammover,hamrepeat',
}

# -----------------------------------------------------------------------------
# ADJECTIVES
# -----------------------------------------------------------------------------
ADJECTIVES = {
    'BIG': 'hamflathand,hampalmout,hamneutralspace,hammoveo',
    'SMALL': 'hamflathand,hampalmi,hamneutralspace,hammovei',
    'LARGE': 'hamflathand,hampalmout,hamneutralspace,hammoveo',
    'LITTLE': 'hampinch12,hampalmd,hamneutralspace',
    'LONG': 'hamfinger2,hamextfingerr,hampalmd,hamlowerarm,hammover',
    'SHORT': 'hamfinger23,hamextfingerr,hampalmd,hamneutralspace',
    'HIGH': 'hamflathand,hampalmd,hamneutralspace,hammoveu',
    'LOW': 'hamflathand,hampalmd,hamneutralspace,hammoved',
    'NEW': 'hamflathand,hampalmu,hamneutralspace,hamarcu',
    'OLD': 'hamcee12,hampalml,hamchin,hammoved',
    'YOUNG': 'hamflathand,hampalmu,hamchest,hammoveu',
    'GOOD': 'hamflathand,hampalmu,hamchin,hammoveo',
    'BAD': 'hamflathand,hampalmd,hamchin,hammoveo',
    'BETTER': 'hamflathand,hampalmu,hamchin,hammoveu',
    'BEST': 'hamflathand,hampalmu,hamneutralspace,hammoveu',
    'WORSE': 'hamflathand,hampalmd,hamneutralspace,hammoved',
    'WORST': 'hamflathand,hampalmd,hamneutralspace,hammoved,hamfast',
    'RIGHT': 'hamfinger2,hamextfingerr,hampalmd,hamneutralspace',
    'WRONG': 'hamfinger23spread,hampalml,hamchin',
    'TRUE': 'hamfinger2,hamextfingero,hampalml,hammouth,hammoveo',
    'FALSE': 'hamfinger2,hamextfingerr,hampalml,hamnose,hammover',
    'EASY': 'hamflathand,hampalmu,hamneutralspace,hammoveu',
    'HARD': 'hamfist,hampalmd,hamneutralspace,hammoved',
    'DIFFICULT': 'hamfinger23,hamextfingerd,hampalml,hamneutralspace,hamrepeat',
    'SIMPLE': 'hamflathand,hampalmd,hamneutralspace,hammover',
    'FAST': 'hamfinger2,hamextfingerr,hampalmout,hamneutralspace,hamfast',
    'SLOW': 'hamflathand,hampalmd,hamlowerarm,hammoveu,hamslow',
    'HAPPY': 'hamflathand,hampalmi,hamchest,hammoveu,hamrepeat',
    'SAD': 'hamflathand,hampalmi,hamcheek,hammoved',
    'ANGRY': 'hamcee12,hampalmi,hamchest,hammoveu',
    'TIRED': 'hamflathand,hampalmi,hamchest,hammoved',
    'HUNGRY': 'hamcee12,hampalmi,hamchest,hammoved',
    'THIRSTY': 'hamfinger2,hamextfingerd,hampalmi,hamneck,hammoved',
    'HOT': 'hamcee12,hampalmi,hammouth,hammoveo',
    'COLD': 'hamfist,hampalmi,hamshoulders,hamrepeat',
    'WARM': 'hamcee12,hampalmi,hammouth,hammoveu',
    'COOL': 'hamflathand,hampalmi,hamchest,hamfingerplay',
    'BEAUTIFUL': 'hamflathand,hampalmi,hamcheek,hamcircle',
    'UGLY': 'hamfinger2,hamextfingerr,hampalml,hamnose,hammover',
    'CLEAN': 'hamflathand,hampalmd,hamneutralspace,hammover',
    'DIRTY': 'hamflathand,hampalmd,hamchin,hamfingerplay',
    'SAME': 'hamfinger2,hamextfingerr,hampalmd,hamneutralspace,hammover',
    'DIFFERENT': 'hamfinger23,hamextfingerr,hampalmd,hamneutralspace,hammoveo',
    'OTHER': 'hamthumb,hampalmu,hamneutralspace,hammover',
    'ANOTHER': 'hamthumb,hampalmu,hamneutralspace,hamarco',
    'MANY': 'hamfinger2345,hampalmu,hamneutralspace,hammoveo',
    'FEW': 'hamfinger23,hampalmu,hamneutralspace',
    'SOME': 'hamflathand,hampalmu,hamneutralspace,hammover',
    'ALL': 'hamflathand,hampalmout,hamneutralspace,hamcircle',
    'EVERY': 'hamfist,hamthumboutmod,hampalml,hamneutralspace,hammoved',
    'EACH': 'hamfist,hamthumboutmod,hampalmd,hamneutralspace,hammover',
    'MORE': 'hampinchall,hampalmu,hamneutralspace,hammoveu',
    'LESS': 'hamflathand,hampalmd,hamneutralspace,hammoved',
    'MOST': 'hamflathand,hampalmu,hamneutralspace,hammoveu',
    'VERY': 'hamfinger23spread,hampalmout,hamneutralspace,hammoveo',
    'ONLY': 'hamfinger2,hamextfingeru,hampalmout,hamneutralspace',
    'JUST': 'hamfinger2,hamextfingeru,hampalml,hamcheek',
    'ALSO': 'hamfinger2,hamextfingerr,hampalmd,hamneutralspace,hammover',
    'STILL': 'hamflathand,hampalmd,hamneutralspace',
    'ALREADY': 'hamflathand,hampalmout,hamchest,hammoveo',
    'READY': 'hamflathand,hampalmout,hamneutralspace,hammover',
    'SURE': 'hamfinger2,hamextfingero,hampalml,hamchin,hammoveo',
    'POSSIBLE': 'hamfist,hampalmd,hamneutralspace,hammoved,hamrepeat',
    'IMPORTANT': 'hamfinger2,hamextfingeru,hampalmout,hamneutralspace,hammoveu',
    'SPECIAL': 'hamfinger2,hamextfingeru,hampalmout,hamneutralspace,hammoveu,hamrepeat',
    'FREE': 'hamflathand,hampalmout,hamneutralspace,hammoveo,hamarco',
    'BUSY': 'hamfist,hampalmd,hamneutralspace,hammover,hamrepeat',
    'OPEN': 'hamflathand,hampalmi,hamneutralspace,hammoveo',
    'CLOSED': 'hamflathand,hampalmout,hamneutralspace,hammovei',
    'FULL': 'hamflathand,hampalmd,hamneutralspace,hammoveu',
    'EMPTY': 'hamflathand,hampalmd,hamneutralspace,hammoved',
    'ALIVE': 'hamflathand,hampalmi,hamchest,hammoveu',
    'DEAD': 'hamflathand,hampalmd,hamneutralspace,hampalmu',
}

# -----------------------------------------------------------------------------
# FINGERSPELLING ALPHABET (ISL/ASL Compatible)
# -----------------------------------------------------------------------------
FINGERSPELLING = {
    'A': 'hamfist,hamthumboutmod,hampalmout',
    'B': 'hamflathand,hamextfingeru,hampalmout,hamthumbacrossmod',
    'C': 'hamceeall,hampalmout',
    'D': 'hamfinger2,hamextfingeru,hampalmout,hampinch12',
    'E': 'hamfist,hamthumbacrossmod,hampalmout',
    'F': 'hamfinger345,hamextfingeru,hampalmout,hampinch12',
    'G': 'hamfinger2,hamextfingerr,hampalml,hamthumboutmod',
    'H': 'hamfinger23,hamextfingerr,hampalmd',
    'I': 'hamfist,hampinkyout,hampalmout',
    'J': 'hamfist,hampinkyout,hampalmout,hamarcd',
    'K': 'hamfinger23,hamextfingeru,hampalmout,hamthumboutmod',
    'L': 'hamfinger2,hamthumboutmod,hamextfingeru,hampalmout',
    'M': 'hamfist,hamthumbacrossmod,hampalmout,hamfingerstraightmod',
    'N': 'hamfist,hamthumbacrossmod,hampalmout',
    'O': 'hampinchall,hampalmout',
    'P': 'hamfinger23,hamextfingerd,hampalmout,hamthumboutmod',
    'Q': 'hamfinger2,hamextfingerd,hampalmout,hamthumboutmod',
    'R': 'hamfinger23,hamextfingeru,hampalmout,hamfingerstraightmod',
    'S': 'hamfist,hamthumbacrossmod,hampalmout',
    'T': 'hamfist,hamthumbacrossmod,hampalmout',
    'U': 'hamfinger23,hamextfingeru,hampalmout',
    'V': 'hamfinger23spread,hamextfingeru,hampalmout',
    'W': 'hamfinger234,hamextfingeru,hampalmout',
    'X': 'hamfinger2,hamextfingeru,hampalmout,hamfingerbend',
    'Y': 'hamfist,hamthumboutmod,hampinkyout,hampalmout',
    'Z': 'hamfinger2,hamextfingeru,hampalmout,hamzigzag',
}

# -----------------------------------------------------------------------------
# NUMBERS
# -----------------------------------------------------------------------------
NUMBERS = {
    'ONE': 'hamfinger2,hamextfingeru,hampalmout',
    'TWO': 'hamfinger23,hamextfingeru,hampalmout',
    'THREE': 'hamfinger23,hamthumboutmod,hamextfingeru,hampalmout',
    'FOUR': 'hamfinger2345,hamextfingeru,hampalmout',
    'FIVE': 'hamflathand,hamextfingeru,hampalmout',
    'SIX': 'hamfinger23,hamthumboutmod,hamextfingeru,hampalmout,hamfingerplay',
    'SEVEN': 'hamfinger2345,hamthumboutmod,hamextfingeru,hampalmout',
    'EIGHT': 'hamfinger2345,hamthumboutmod,hamextfingeru,hampalml',
    'NINE': 'hamfinger2,hamextfingeru,hampalml,hamfingerbend',
    'TEN': 'hamthumb,hamextfingeru,hampalmout,hamrepeat',
    'ZERO': 'hamcee12,hampalmout',
    'HUNDRED': 'hamfinger2,hamextfingerr,hampalmout,hamcircle',
    'THOUSAND': 'hamflathand,hampalmd,hamneutralspace,hammoveo',
    'FIRST': 'hamfinger2,hamextfingeru,hampalmout,hammoveu',
    'SECOND': 'hamfinger23,hamextfingeru,hampalmout',
    'THIRD': 'hamfinger23,hamthumboutmod,hamextfingeru,hampalmout',
    'LAST': 'hamfinger2,hamextfingerd,hampalmout,hammoved',
    'NEXT': 'hamflathand,hampalmout,hamneutralspace,hamarco',
}

# -----------------------------------------------------------------------------
# PREPOSITIONS & CONJUNCTIONS
# -----------------------------------------------------------------------------
PREPOSITIONS = {
    'IN': 'hamflathand,hampalmd,hamneutralspace,hammovei',
    'ON': 'hamflathand,hampalmd,hamneutralspace',
    'AT': 'hamfinger2,hamextfingerr,hampalmd,hamneutralspace',
    'TO': 'hamfinger2,hamextfingerr,hampalmout,hamneutralspace,hammoveo',
    'FROM': 'hamfinger2,hamextfingerl,hampalmout,hamneutralspace,hammovei',
    'WITH': 'hamfist,hampalml,hamneutralspace,hammovei',
    'WITHOUT': 'hamfist,hampalmout,hamneutralspace,hammoveo',
    'FOR': 'hamfinger2,hamextfingeru,hampalml,hamforehead,hammoveo',
    'ABOUT': 'hamfinger2,hamextfingerr,hampalmout,hamneutralspace,hamcircle',
    'OF': 'hamflathand,hampalmout,hamneutralspace,hammover',
    'BY': 'hamflathand,hampalml,hamneutralspace,hammover',
    'UP': 'hamfinger2,hamextfingeru,hampalmout,hamneutralspace,hammoveu',
    'DOWN': 'hamfinger2,hamextfingerd,hampalmout,hamneutralspace,hammoved',
    'OUT': 'hamcee12,hampalmi,hamneutralspace,hammoveo',
    'OVER': 'hamflathand,hampalmd,hamneutralspace,hamarco',
    'UNDER': 'hamflathand,hampalmu,hamneutralspace,hammoved',
    'BETWEEN': 'hamflathand,hampalml,hamneutralspace,hammover',
    'BEFORE': 'hamflathand,hampalmout,hamneutralspace,hammovei',
    'AFTER': 'hamflathand,hampalmout,hamneutralspace,hammoveo',
    'DURING': 'hamfinger2,hamextfingerr,hampalmd,hamneutralspace,hammover',
    'THROUGH': 'hamflathand,hampalml,hamneutralspace,hammoveo',
    'INTO': 'hamflathand,hampalmd,hamneutralspace,hammovei',
    'BEHIND': 'hamflathand,hampalmout,hamneutralspace,hammovei',
    'FRONT': 'hamflathand,hampalmi,hamneutralspace,hammoveo',
    'NEAR': 'hamflathand,hampalmout,hamneutralspace,hammovei',
    'FAR': 'hamflathand,hampalmout,hamneutralspace,hammoveo',
    'AND': 'hamflathand,hampalml,hamneutralspace,hammover',
    'OR': 'hamfinger2,hamextfingeru,hampalmout,hamneutralspace,hammover',
    'BUT': 'hamfinger23,hamextfingerr,hampalmout,hamneutralspace,hammoveo',
    'IF': 'hamfinger2,hamextfingeru,hampalml,hamneutralspace,hamrepeat',
    'THEN': 'hamflathand,hampalmout,hamneutralspace,hammoveo',
    'BECAUSE': 'hamfinger2,hamextfingeru,hampalml,hamforehead,hammoveo',
    'SO': 'hamfinger2,hamextfingerr,hampalmout,hamneutralspace',
    'NOT': 'hamthumb,hampalmout,hamchin,hammoveo',
    'NO': 'hamfinger23,hamthumboutmod,hampalmout,hamneutralspace',
    'YES': 'hamfist,hampalmout,hamneutralspace,hammoved',
}

# -----------------------------------------------------------------------------
# COLORS
# -----------------------------------------------------------------------------
COLORS = {
    'RED': 'hamfinger2,hamextfingerd,hampalml,hamlips,hammoved',
    'BLUE': 'hamflathand,hampalmout,hamneutralspace,hamfingerplay',
    'GREEN': 'hamfinger23spread,hampalmout,hamneutralspace,hamrepeat',
    'YELLOW': 'hamfinger2345,hamthumboutmod,hampalmout,hamneutralspace,hamrepeat',
    'BLACK': 'hamfinger2,hamextfingerr,hampalmd,hamforehead,hammover',
    'WHITE': 'hamflathand,hampalmi,hamchest,hammoveo',
    'ORANGE': 'hamcee12,hampalml,hamchin,hamrepeat',
    'PINK': 'hamfinger2,hamextfingerd,hampalml,hamlips,hammoved',
    'BROWN': 'hamflathand,hampalml,hamcheek,hammoved',
    'PURPLE': 'hamfinger23spread,hampalmout,hamneutralspace,hammoved',
    'GRAY': 'hamflathand,hampalmout,hamneutralspace,hamfingerplay,hammover',
}


# =============================================================================
# COMBINED GLOSSARY
# =============================================================================

def get_all_glosses() -> Dict[str, str]:
    """
    Return combined dictionary of all gloss -> HamNoSys mappings.

    Returns:
        Dict with English gloss keys and HamNoSys notation values
    """
    all_glosses = {}
    all_glosses.update(GREETINGS)
    all_glosses.update(PRONOUNS)
    all_glosses.update(VERBS)
    all_glosses.update(NOUNS)
    all_glosses.update(ADJECTIVES)
    all_glosses.update(NUMBERS)
    all_glosses.update(PREPOSITIONS)
    all_glosses.update(COLORS)
    all_glosses.update(FINGERSPELLING)
    return all_glosses


def get_category_for_gloss(gloss: str) -> str:
    """
    Get the category a gloss belongs to.

    Args:
        gloss: English gloss (uppercase)

    Returns:
        Category name or 'unknown'
    """
    gloss = gloss.upper()

    if gloss in GREETINGS:
        return 'greetings'
    elif gloss in PRONOUNS:
        return 'pronouns'
    elif gloss in VERBS:
        return 'verbs'
    elif gloss in NOUNS:
        return 'nouns'
    elif gloss in ADJECTIVES:
        return 'adjectives'
    elif gloss in NUMBERS:
        return 'numbers'
    elif gloss in PREPOSITIONS:
        return 'prepositions'
    elif gloss in COLORS:
        return 'colors'
    elif gloss in FINGERSPELLING:
        return 'fingerspelling'
    else:
        return 'unknown'


if __name__ == '__main__':
    # Test the module
    all_glosses = get_all_glosses()

    print("HamNoSys Data Module")
    print("=" * 60)
    print(f"\nTotal glosses available: {len(all_glosses)}")
    print(f"\nBy category:")
    print(f"  Greetings: {len(GREETINGS)}")
    print(f"  Pronouns: {len(PRONOUNS)}")
    print(f"  Verbs: {len(VERBS)}")
    print(f"  Nouns: {len(NOUNS)}")
    print(f"  Adjectives: {len(ADJECTIVES)}")
    print(f"  Numbers: {len(NUMBERS)}")
    print(f"  Prepositions: {len(PREPOSITIONS)}")
    print(f"  Colors: {len(COLORS)}")
    print(f"  Fingerspelling: {len(FINGERSPELLING)}")

    print(f"\nSample entries:")
    for gloss in ['HELLO', 'I', 'LOVE', 'YOU', 'THANK']:
        if gloss in all_glosses:
            print(f"  {gloss}: {all_glosses[gloss][:50]}...")
