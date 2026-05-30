# """
# Secret sharing scheme.
# MODIFY THIS FILE.
# """

# from __future__ import annotations

# from typing import List


# class Share:
#     """
#     A secret share in a finite field.
#     """

#     def __init__(self, *args, **kwargs):
#         # Adapt constructor arguments as you wish
#         raise NotImplementedError("You need to implement this method.")

#     def __repr__(self):
#         # Helps with debugging.
#         raise NotImplementedError("You need to implement this method.")

#     def __add__(self, other):
#         raise NotImplementedError("You need to implement this method.")

#     def __sub__(self, other):
#         raise NotImplementedError("You need to implement this method.")

#     def __mul__(self, other):
#         raise NotImplementedError("You need to implement this method.")

#     def serialize(self):
#         """Generate a representation suitable for passing in a message."""
#         raise NotImplementedError("You need to implement this method.")

#     @staticmethod
#     def deserialize(serialized) -> Share:
#         """Restore object from its serialized representation."""
#         raise NotImplementedError("You need to implement this method.")


# def share_secret(secret: int, num_shares: int) -> List[Share]:
#     """Generate secret shares."""
#     raise NotImplementedError("You need to implement this method.")


# def reconstruct_secret(shares: List[Share]) -> int:
#     """Reconstruct the secret from shares."""
#     raise NotImplementedError("You need to implement this method.")


# # Feel free to add as many methods as you want.


#####################################################################


from __future__ import annotations

import random
from typing import List


# A very large prime. The real inputs/outputs are smaller than 2**31, and this
# prime is WAY way way like alot bigger, so the answer never "wraps around" and is always exact.
PRIME = 2 ** 127 - 1


class Share:
    """
    One piece of a secret. Internally it is just one number kept inside the
    range 0 .. PRIME-1.
    """

    def __init__(self, value: int):
        # Always keep the value inside [0, PRIME) by taking it modulo PRIME.
        self.value = value % PRIME

    def __repr__(self):
        # Makes printing a Share readable while debugging.
        return f"Share({self.value})"

    def __add__(self, other):
        # We can add a Share to another Share, or to a plain number.
        # Figure out the number to add:
        if isinstance(other, Share):
            other_value = other.value
        else:
            other_value = other
        return Share(self.value + other_value)

    def __sub__(self, other):
        # Same idea as add, but subtracting.
        if isinstance(other, Share):
            other_value = other.value
        else:
            other_value = other
        return Share(self.value - other_value)

    def __mul__(self, other):
        # Multiply a share by a plain number (a public scalar).
        #  multiplying two SECRET shares cannot be done here on its own.
        # that needs the Beaver protocol, which lives in smc_party.py.
        if isinstance(other, Share):
            other_value = other.value
        else:
            other_value = other
        return Share(self.value * other_value)

    def serialize(self):
        """turn the share into text so it can be sent in a message."""
        return str(self.value)

    @staticmethod
    def deserialize(serialized) -> Share:
        """build a Share back from text (or bytes) received in a message."""
        if isinstance(serialized, bytes):
            serialized = serialized.decode("ascii")
        return Share(int(serialized))


def share_secret(secret: int, num_shares: int) -> List[Share]:
    """
    Split 'secret' into 'num_shares' pieces that add up to it.
    pick all but one piece at random, then choose the last piece so that
    everything sums back to the secret.
    """
    #  make (num_shares - 1) random pieces.
    shares = []
    for _ in range(num_shares - 1):
        random_value = random.randrange(PRIME)
        shares.append(Share(random_value))

    # add up the random pieces so far.
    total_so_far = 0
    for share in shares:
        total_so_far = total_so_far + share.value

    # the last piece makes the whole thing equal the secret.
    last_value = (secret - total_so_far) % PRIME
    shares.append(Share(last_value))

    return shares


def reconstruct_secret(shares: List[Share]) -> int:
    """Add up all the pieces to get the secret back."""
    total = 0
    for share in shares:
        total = total + share.value
    return total % PRIME