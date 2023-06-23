class DatabaseError(Exception):
    """Base exception for all database errors"""


class DBLaunchError(DatabaseError):
    pass


class DBLaunchNotFoundError(DBLaunchError):
    pass


class DBLaunchAlreadyExistsError(DBLaunchError):
    pass


class DBPoolError(DatabaseError):
    pass


class DBPoolNotFoundError(DBPoolError):
    pass


class DBPoolAlreadyExistsError(DBPoolError):
    pass


class DBPoolCopyError(DatabaseError):
    pass


class DBPoolBackupNotFoundError(DBPoolCopyError):
    pass


class DBPoolBackupAlreadyExistsError(DBPoolCopyError):
    pass
