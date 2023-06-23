import functools

from pydantic import ValidationError

from pool_manager.app.settings import get_app_settings


def testing_only(func):

    """
    Provides decorator, which forbids
    calling dangerous functions in production
    """

    try:
        settings = get_app_settings()
        is_danger = settings.environment.name == "prod"

    except ValidationError:
        is_danger = True

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):

        if is_danger:
            err = f"Function '{func.__name__}' is allowed to call only in testing mode"
            help = "Please, check 'ENVIRONMENT' variable is not set to 'prod'"
            raise RuntimeError(f"{err}. {help}")

        return await func(*args, **kwargs)

    return wrapper
