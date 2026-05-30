# """
# Tools for building arithmetic expressions to execute with SMC.

# Example expression:
# >>> alice_secret = Secret()
# >>> bob_secret = Secret()
# >>> expr = alice_secret * bob_secret * Scalar(2)

# MODIFY THIS FILE.
# """

# import base64
# import random
# from typing import Optional


# ID_BYTES = 4


# def gen_id() -> bytes:
#     id_bytes = bytearray(
#         random.getrandbits(8) for _ in range(ID_BYTES)
#     )
#     return base64.b64encode(id_bytes)


# class Expression:
#     """
#     Base class for an arithmetic expression.
#     """

#     def __init__(
#             self,
#             id: Optional[bytes] = None
#         ):
#         # If ID is not given, then generate one.
#         if id is None:
#             id = gen_id()
#         self.id = id

#     def __add__(self, other):
#         raise NotImplementedError("You need to implement this method.")


#     def __sub__(self, other):
#         raise NotImplementedError("You need to implement this method.")


#     def __mul__(self, other):
#         raise NotImplementedError("You need to implement this method.")


#     def __hash__(self):
#         return hash(self.id)


#     # Feel free to add as many methods as you like.


# class Scalar(Expression):
#     """Term representing a scalar finite field value."""

#     def __init__(
#             self,
#             value: int,
#             id: Optional[bytes] = None
#         ):
#         self.value = value
#         super().__init__(id)


#     def __repr__(self):
#         return f"{self.__class__.__name__}({repr(self.value)})"


#     def __hash__(self):
#         return


#     # Feel free to add as many methods as you like.


# class Secret(Expression):
#     """Term representing a secret finite field value (variable)."""

#     def __init__(
#             self,
#             id: Optional[bytes] = None
#         ):
#         super().__init__(id)


#     def __repr__(self):
#         return (
#             f"{self.__class__.__name__}({self.value if self.value is not None else ''})"
#         )


#     # Feel free to add as many methods as you like.


# # Feel free to add as many classes as you like.


######################################################################

import base64
import random
from typing import Optional


ID_BYTES = 4


def gen_id() -> bytes:
    # Make a short random id (used to tell tree nodes apart).
    id_bytes = bytearray(
        random.getrandbits(8) for _ in range(ID_BYTES)
    )
    return base64.b64encode(id_bytes)


class Expression:
    """

    The three methods below are Python's "operator overloading". They let us
    write  a + b ,  a - b , and  a * b  in normal Python, and instead of
    computing a result, they create a new tree node.
    """

    def __init__(self, id: Optional[bytes] = None):
        # If no id was given, make a freshesttt random one.
        if id is None:
            id = gen_id()
        self.id = id

    def __add__(self, other):
        # "a + b" becomes an AddOperation node.
        return AddOperation(self, other)

    def __sub__(self, other):
        # "a - b" becomes a SubOperation node.
        return SubOperation(self, other)

    def __mul__(self, other):
        # "a * b" becomes a MultOperation node.
        return MultOperation(self, other)

    def __hash__(self):
        # Letss us usee an expression as a dictionary key (the tests do this).
        return hash(self.id)


class Scalar(Expression):
    """A public constant number that everyone is allowed to know (like 5)."""

    def __init__(self, value: int, id: Optional[bytes] = None):
        self.value = value
        super().__init__(id)

    def __repr__(self):
        return f"{self.__class__.__name__}({repr(self.value)})"

    def __hash__(self):
        return hash(self.id)


class Secret(Expression):
    """
    A private number owned by uno party (a variable in the calclation).
    Its real value is only known to its owner.
    """

    def __init__(self, value: Optional[int] = None, id: Optional[bytes] = None):
        # value is normally None here, it just helps reprbelow.
        self.value = value
        super().__init__(id)

    def __repr__(self):
        if self.value is not None:
            return f"{self.__class__.__name__}({self.value})"
        return f"{self.__class__.__name__}()"


class AddOperation(Expression):
    """A tree node that means: (a + b)."""

    def __init__(self, a, b, id: Optional[bytes] = None):
        self.a = a
        self.b = b
        super().__init__(id)

    def __repr__(self):
        return f"({repr(self.a)} + {repr(self.b)})"


class SubOperation(Expression):
    """A tree node that means: (a - b)."""

    def __init__(self, a, b, id: Optional[bytes] = None):
        self.a = a
        self.b = b
        super().__init__(id)

    def __repr__(self):
        return f"({repr(self.a)} - {repr(self.b)})"


class MultOperation(Expression):
    """A tree node that means: (a * b)."""

    def __init__(self, a, b, id: Optional[bytes] = None):
        self.a = a
        self.b = b
        super().__init__(id)

    def __repr__(self):
        return f"({repr(self.a)} * {repr(self.b)})"