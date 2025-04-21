from dataclasses import dataclass

@dataclass
class Badge:
    """
    Represents a Scout badge.
    - name: badge title
    - link: URL to badge details
    - completed: whether the scout has finished it
    """
    name: str
    link: str
    completed: bool = False

@dataclass
class Session:
    """
    Represents a scheduled session.
    - date: DD-MM-YYYY
    - time: HH:MM
    - title: session description
    """
    date: str
    time: str
    title: str

@dataclass
class Preferences:
     """
    Represents preferences
    """
    date: str
    time: str
    title: str