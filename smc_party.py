# """
# Implementation of an SMC client.

# MODIFY THIS FILE.
# """
# # You might want to import more classes if needed.

# import collections
# import json
# from typing import (
#     Dict,
#     Set,
#     Tuple,
#     Union
# )

# from communication import Communication
# from expression import (
#     Expression,
#     Secret
# )
# from protocol import ProtocolSpec
# from secret_sharing import(
#     reconstruct_secret,
#     share_secret,
#     Share,
# )

# # Feel free to add as many imports as you want.


# class SMCParty:
#     """
#     A client that executes an SMC protocol to collectively compute a value of an expression together
#     with other clients.

#     Attributes:
#         client_id: Identifier of this client
#         server_host: hostname of the server
#         server_port: port of the server
#         protocol_spec (ProtocolSpec): Protocol specification
#         value_dict (dict): Dictionary assigning values to secrets belonging to this client.
#     """

#     def __init__(
#             self,
#             client_id: str,
#             server_host: str,
#             server_port: int,
#             protocol_spec: ProtocolSpec,
#             value_dict: Dict[Secret, int]
#         ):
#         self.comm = Communication(server_host, server_port, client_id)

#         self.client_id = client_id
#         self.protocol_spec = protocol_spec
#         self.value_dict = value_dict


#     def run(self) -> int:
#         """
#         The method the client use to do the SMC.
#         """
#         raise NotImplementedError("You need to implement this method.")


#     # Suggestion: To process expressions, make use of the *visitor pattern* like so:
#     def process_expression(
#             self,
#             expr: Expression
#         ):
#         # if expr is an addition operation:
#         #     ...

#         # if expr is a multiplication operation:
#         #     ...

#         # if expr is a secret:
#         #     ...

#         # if expr is a scalar:
#         #     ...
#         #
#         # Call specialized methods for each expression type, and have these specialized
#         # methods in turn call `process_expression` on their sub-expressions to process
#         # further.
#         pass

#     # Feel free to add as many methods as you want.



#########################################################################

import collections
import json
from typing import (
    Dict,
    Set,
    Tuple,
    Union
)

from communication import Communication
from expression import (
    Expression,
    Secret,
    Scalar,
    AddOperation,
    SubOperation,
    MultOperation,
)
from protocol import ProtocolSpec
from secret_sharing import (
    reconstruct_secret,
    share_secret,
    Share,
)


RESULT_LABEL = "final_result"


class SMCParty:
    """
    A client that works together with the other clients to compute the value
    of an expression, without revealing its own secret numbers.
    """

    def __init__(
            self,
            client_id: str,
            server_host: str,
            server_port: int,
            protocol_spec: ProtocolSpec,
            value_dict: Dict[Secret, int]
        ):
        self.comm = Communication(server_host, server_port, client_id)

        self.client_id = client_id
        self.protocol_spec = protocol_spec
        self.value_dict = value_dict

        
        self.constant_handler = sorted(self.protocol_spec.participant_ids)[0]

        # Remember secret pieces we already received, so if the same secret is
        # used twice in the expression we only fetch it once.
        self.secret_share_cache = {}

    def run(self) -> int:
        """The main method: do the whole SMC computation and return the answer."""
        # send out the pieces of our own secrets =).
        self.send_out_my_secrets()

        # walk the tree and compute our own piece of the result.
        my_share = self.process_expression(self.protocol_spec.expr)

        # publish our piece for everyone to see.
        self.comm.publish_message(RESULT_LABEL, my_share.serialize())

        # collect everyones pieces and add them up, like you do with broken glasses.
        all_shares = []
        for party_id in self.protocol_spec.participant_ids:
            message = self.comm.retrieve_public_message(party_id, RESULT_LABEL)
            all_shares.append(Share.deserialize(message))

        return reconstruct_secret(all_shares)

    def send_out_my_secrets(self) -> None:
        parties = self.protocol_spec.participant_ids

        for secret, value in self.value_dict.items():
            pieces = share_secret(value, len(parties))
            label = self.secret_label(secret)

            # Give the first party the first piece the second party the second
            # pieceand so on.
            for i in range(len(parties)):
                party_id = parties[i]
                piece = pieces[i]
                self.comm.send_private_message(party_id, label, piece.serialize())

    def process_expression(self, expr: Expression) -> Share:
        
        if isinstance(expr, AddOperation):
            left = self.process_expression(expr.a)
            right = self.process_expression(expr.b)
            return left + right

        if isinstance(expr, SubOperation):
            left = self.process_expression(expr.a)
            right = self.process_expression(expr.b)
            return left - right

        if isinstance(expr, MultOperation):
            return self.handle_multiplication(expr)

        if isinstance(expr, Secret):
            return self.get_secret_share(expr)

        if isinstance(expr, Scalar):
            return self.scalar_as_share(expr.value)

        # If we get here, the expression is some type we do not know.
        raise Exception("Unknown expression type: " + str(type(expr)))

    def handle_multiplication(self, expr: MultOperation) -> Share:
        
        left_is_constant = self.is_constant(expr.a)
        right_is_constant = self.is_constant(expr.b)

        if left_is_constant and right_is_constant:
            # The whole thing is public, just compute the number.
            number = self.evaluate_constant(expr)
            return self.scalar_as_share(number)

        if left_is_constant:
            # constant * secret: multiply our piece of the secret by the number.
            number = self.evaluate_constant(expr.a)
            secret_share = self.process_expression(expr.b)
            return secret_share * number

        if right_is_constant:
            # secret * constant: same thing, other way round.
            number = self.evaluate_constant(expr.b)
            secret_share = self.process_expression(expr.a)
            return secret_share * number

        # secret * secret: this is the hard case.
        return self.beaver_multiply(expr)

    def is_constant(self, expr: Expression) -> bool:
        """
        Return True if this part of the tree has NO secrets in it
        (so it is a public number we are all kinda allowed to know).
        """
        if isinstance(expr, Scalar):
            return True
        if isinstance(expr, Secret):
            return False
        # For an operation, it is constant only if BOTH sides are constant.
        if isinstance(expr, (AddOperation, SubOperation, MultOperation)):
            return self.is_constant(expr.a) and self.is_constant(expr.b)
        raise Exception("Unknown expression type: " + str(type(expr)))

    def evaluate_constant(self, expr: Expression) -> int:
        """
        Compute the plain number value of a part of the tree that has nosecrets in it.
        """
        if isinstance(expr, Scalar):
            return expr.value
        if isinstance(expr, AddOperation):
            return self.evaluate_constant(expr.a) + self.evaluate_constant(expr.b)
        if isinstance(expr, SubOperation):
            return self.evaluate_constant(expr.a) - self.evaluate_constant(expr.b)
        if isinstance(expr, MultOperation):
            return self.evaluate_constant(expr.a) * self.evaluate_constant(expr.b)
        raise Exception("This expression is not a constant: " + str(type(expr)))

    def scalar_as_share(self, value: int) -> Share:
        if self.client_id == self.constant_handler:
            return Share(value)
        else:
            return Share(0)

    def get_secret_share(self, secret: Secret) -> Share:
        """Get our piece of a secret. Fetch it once then remember it, its not that hard =("""
        label = self.secret_label(secret)

        if label not in self.secret_share_cache:
            message = self.comm.retrieve_private_message(label)
            self.secret_share_cache[label] = Share.deserialize(message)

        return self.secret_share_cache[label]

    def beaver_multiply(self, expr: MultOperation) -> Share:
        
        # Our pieces of x and y.
        share_x = self.process_expression(expr.a)
        share_y = self.process_expression(expr.b)

        # Get our triplet pieces for THIS multiplication.
        op_id = self.operation_id(expr)
        share_a, share_b, share_c = self.comm.retrieve_beaver_triplet_shares(op_id)

        # Build labels so the (x - a) and (y - b) messages donot get mixed up.
        label_x_minus_a = op_id + "_x_minus_a"
        label_y_minus_b = op_id + "_y_minus_b"

        # Publish our piece of (x - a) and our piece of (y - b).
        self.comm.publish_message(label_x_minus_a, (share_x - share_a).serialize())
        self.comm.publish_message(label_y_minus_b, (share_y - share_b).serialize())

        # Rebuild the public values (x - a) and (y - b) from everyone's pieces.
        x_minus_a = self.reconstruct_public_value(label_x_minus_a)
        y_minus_b = self.reconstruct_public_value(label_y_minus_b)

        # Now compute our piece of the product z.
        share_z = share_c + (share_x * y_minus_b) + (share_y * x_minus_a)

        # The last term is a plain public numberso only one party adds it.
        if self.client_id == self.constant_handler:
            share_z = share_z - (x_minus_a * y_minus_b)

        return share_z

    def reconstruct_public_value(self, label: str) -> int:
        """Collect every partys published piece for 'label' and add them up."""
        pieces = []
        for party_id in self.protocol_spec.participant_ids:
            message = self.comm.retrieve_public_message(party_id, label)
            pieces.append(Share.deserialize(message))
        return reconstruct_secret(pieces)

    def secret_label(self, secret: Secret) -> str:
        """A unique text label for a secret, used when sending its pieces."""
        return "secret_" + secret.id.decode("ascii")

    def operation_id(self, expr: Expression) -> str:
        """A unique text id for one operation node (used for its triplet)."""
        return expr.id.decode("ascii")