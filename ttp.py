# """
# Trusted parameters generator.

# MODIFY THIS FILE.
# """

# import collections
# from typing import (
#     Dict,
#     Set,
#     Tuple,
# )

# from communication import Communication
# from secret_sharing import(
#     share_secret,
#     Share,
# )

# # Feel free to add as many imports as you want.


# class TrustedParamGenerator:
#     """
#     A trusted third party that generates random values for the Beaver triplet multiplication scheme.
#     """

#     def __init__(self):
#         self.participant_ids: Set[str] = set()


#     def add_participant(self, participant_id: str) -> None:
#         """
#         Add a participant.
#         """
#         self.participant_ids.add(participant_id)

#     def retrieve_share(self, client_id: str, op_id: str) -> Tuple[Share, Share, Share]:
#         """
#         Retrieve a triplet of shares for a given client_id.
#         """
#         raise NotImplementedError("You need to implement this method.")

#     # Feel free to add as many methods as you want.


#############################################################################

import collections
from typing import (
    Dict,
    Set,
    Tuple,
)

from communication import Communication
from secret_sharing import (
    share_secret,
    Share,
    PRIME,
)

import random


class TrustedParamGenerator:
    """
    Makes random Beaver triplets and hands each party its shares.
    """

    def __init__(self):
        self.participant_ids: Set[str] = set()
        # For each multiplicatio we remembereding the shares of
        # a, b and c, so every party gets the SAME triplet.
        # op_id = (sharesofa, sharesofb, sharesofc)
        self.triplets = {}

    def add_participant(self, participant_id: str) -> None:
        """Add a participant."""
        self.participant_ids.add(participant_id)

    def _make_triplet(self, op_id: str) -> None:
        """Create one new triplet for this multiplication and store it."""
        number_of_parties = len(self.participant_ids)

        a = random.randrange(PRIME)
        b = random.randrange(PRIME)
        c = (a * b) % PRIME

        # Split each of a, b, c into one piece per party.
        shares_of_a = share_secret(a, number_of_parties)
        shares_of_b = share_secret(b, number_of_parties)
        shares_of_c = share_secret(c, number_of_parties)

        self.triplets[op_id] = (shares_of_a, shares_of_b, shares_of_c)

    def retrieve_share(self, client_id: str, op_id: str) -> Tuple[Share, Share, Share]:
        if op_id not in self.triplets:
            self._make_triplet(op_id)

        shares_of_a, shares_of_b, shares_of_c = self.triplets[op_id]

        # We need to give each party a different piece. Put the party names in
        # a fixed (sorted) order, and use this partys position as its index.
        ordered_parties = sorted(self.participant_ids)
        index = ordered_parties.index(client_id)

        return (shares_of_a[index], shares_of_b[index], shares_of_c[index])