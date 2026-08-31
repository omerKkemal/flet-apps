# Copyright (c) 2025 Omer Kemal
# Proprietary and confidential. All rights reserved.

import os
from datetime import datetime
import secrets
import string


class Setting:
    """
    The Setting class is responsible for storing application settings and
    providing utility methods for generating random identifiers,
    and managing configuration paths and database details.
    """

    def setting_var(self):
        # App configrations
        # for local test
        self.IP = "http://127.0.0.1"
        self.PORT = 8000
        self.BASE_URL = f"{self.IP}:{self.PORT}"

    def ID(self, n=5):
        """
        Generates a random alphanumeric ID of length n (default 5).
        This ID can be used for creating unique identifiers for entities
        in the system, such as users, events, or records.
        """
        return ''.join(
            secrets.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits)
            for _ in range(n)
        )