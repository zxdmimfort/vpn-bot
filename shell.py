import IPython

from config import get_engine, get_session
from models import Base, User

engine = get_engine()
Session = get_session(engine)

# Определяем переменные, доступные в сессии шелла
# locals_dict = globals().copy()
#
# locals_dict.update(
#     {
#         "engine": engine,
#         "Session": Session,
#         "Base": Base,
#         "User": User
#     }
# )

# IPython.start_ipython(argv=[], user_ns=locals_dict)