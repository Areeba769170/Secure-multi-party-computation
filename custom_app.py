"""
 Custom SMC Application: Private Interest Matching 

------------------------------------ MOTIVATION ------------------------------
So imagine two persons, Alice and Bob. They want to know how many hobbies they
have in common, to see if maybe they can be friends or not. But here is the big
problem: nobody wants to just shout out their whole list of hobbies to some
stranger. Maybe Alice is little bit shy about one hobby (we do not judge), and
maybe Bob also does not want to tell everything at the first day. This is very
normal, humans are like this.
 
What they actually want is only ONE number: a "compatibility score" that says
how many interests they share. They do NOT want to reveal WHICH interests they
have. Only the number. That is all. Very simple wish, but surprisingly hard!
 
In cryptography this famous problem has a fancy name: "Private Set Intersection"
(PSI). It sounds scary but it is used everywhere in real life, for example when
some app checks if you and your friend have same phone contact, WITHOUT sending
your whole contact list to the internet (thank god). Here we build a small baby
version of this idea using our own SMC system. We are basically cryptographers
now, congratulations to us.

--------------------------------- HOW IT WORKS -------------------------------
First, Alice and Bob agree on one public list of possible interests, like this:
    [sports, music, cooking, travel, gaming]
 
Then each person writes a secret "yes or no" answer for every interest:
    1 means "yes, I like this thing"
    0 means "no, not for me thank you"
 
An interest is shared only if BOTH of them said 1. And here is the small magic:
if you just multiply the two secret answers, it does exactly this for free:
    1 * 1 = 1   (both like it       -> it counts!)
    1 * 0 = 0   (only one likes it  -> sorry, no)
    0 * 0 = 0   (nobody likes it    -> obviously no)
 
So the number of shared interests is simply the sum of all these products:
    overlap = a0*b0 + a1*b1 + a2*b2 + a3*b3 + a4*b4
 
After that, we make it into a nice "compatibility score" by giving some fixed
points to every shared interest. POINTS_PER_MATCH is a public constant (so it
is allowed to be known by everybody):
    score = overlap * POINTS_PER_MATCH
 
When the score comes out, the two friends just look if it is big enough to be
called a "good match" or not. We do this last comparison in normal Python and
not inside the SMC, because comparing numbers inside SMC is a whole big drama
and we do not need that headache here.
 
This tiny circuit uses ALL the operations we implemented, very efficient:
- multiplication of two secrets (every a*b eats one Beaver triplet, yum)
- addition (we add all the products together)
- multiplication by a public constant (the POINTS_PER_MATCH)
 
Small but important decision: we did NOT subtract the threshold INSIDE the
circuit. Why? Because our finite field math is a little dramatic and wraps any
negative number around into a giant monster number. So a score that is "below
threshold" would look completely wrong and confuse everybody. To avoid this
trap we keep the score always a happy non-negative number. You are welcome.
 
------------------------------- THREAT MODEL ---------------------------------
We assume the "honest-but-curious" model. This means:
- Both parties follow the protocol correctly, like good citizens.
- BUT they are very curious, and if they could secretly peek at the other persons answers, they would 100% do it. We all know this type of person.
 
Thanks to SMC, every secret answer is cut into random pieces (shares), so no
party ever sees the other one's individual answers. They only learn the final
number that they both agreed to compute (the compatibility score). Nothing more.
 
What this nicely protects:
    - Bob never learns WHICH interests Alice has, only the shared total.
    - Alice never learns WHICH interests Bob has, only the shared total.
    - Everybody keeps their dignity. Beautiful.
 
What this does NOT protect (we must be honest here, no lying in science):
    - A cheating party. For example if naughty Bob secretly puts "1" on every
      single interest, then the overlap just becomes Alice's total number of
      interests, which leaks how many she has. Our additive scheme cannot check
      if inputs are really 0 or 1. To stop such active cheaters you would need
      extra heavy machinery (like zero-knowledge proofs), which is a story for
      another project and another sleepless night.
    - Leakage from the result itself. If the list had only ONE interest, then
      revealing the score (0 or some points) would basically reveal that exact
      interest, oops. This is why we use several interests: then the score alone
      does not tell you WHICH ones matched. Safety in numbers, like always.
=============================================================================
"""

import time
from multiprocessing import Process, Queue

from expression import Scalar, Secret
from protocol import ProtocolSpec
from server import run

from smc_party import SMCParty


# The port the local server will listen on. (Different from the test port so
# they do not clash if both happen to run.)
PORT = 62345

# The public list of interests both people choose their answers from.
INTERESTS = ["sports", "music", "cooking", "travel", "gaming"]

# Public constant: how many points each shared interest is worth.
POINTS_PER_MATCH = 10

# How many shared interests we want for a "good match".
THRESHOLD_INTERESTS = 2


# --------------------------------------------------------------------------
# The code below (smc_client, smc_server, run_processes) is the same helper
# pattern used in test_integration.py. It starts a server and one process per
# party lets them talk to each other and collects their results.
# --------------------------------------------------------------------------

def smc_client(client_id, prot, value_dict, queue):
    cli = SMCParty(
        client_id,
        "localhost",
        PORT,
        protocol_spec=prot,
        value_dict=value_dict
    )
    res = cli.run()
    queue.put(res)
    print(f"{client_id} has finished!")


def smc_server(args):
    run("localhost", PORT, args)


def run_processes(server_args, *client_args):
    queue = Queue()

    server = Process(target=smc_server, args=(server_args,))
    clients = [Process(target=smc_client, args=(*args, queue)) for args in client_args]

    server.start()
    time.sleep(3)
    for client in clients:
        client.start()

    results = list()
    for client in clients:
        client.join()

    for client in clients:
        results.append(queue.get())

    server.terminate()
    server.join()

    time.sleep(2)
    print("Server stopped.")

    return results


# Building the circuit.

def build_score_circuit(alice_secrets, bob_secrets):
    #Build the expression:
    #overlap = a0*b0 + a1*b1 + ... + a4*b4
    #score   = overlap * POINTS_PER_MATCH

    #alice_secrets and bob_secrets are lists of Secret() objects, one per
    #interest. We multiply the matching pair for each interest, add them all
    #together then multiply by the public points constant.
    
    # Start with the product of the first pair of answers.
    overlap = alice_secrets[0] * bob_secrets[0]

    # Then add the product of every other pair, one interest at a time.
    for i in range(1, len(INTERESTS)):
        overlap = overlap + (alice_secrets[i] * bob_secrets[i])

    # Multiply the whole overlap by the public points constant.
    score = overlap * Scalar(POINTS_PER_MATCH)
    return score


def make_secrets_and_values(answers):
    #Turn a list of 0/1 answers into: a list of Secret() objects (one per interest) a dictionary mapping each Secret to its 0/1 value. 
    # The dictionary is what a party gives to its SMCParty.
    secrets = []
    value_dict = {}
    for answer in answers:
        s = Secret()
        secrets.append(s)
        value_dict[s] = answer
    return secrets, value_dict


def run_matching(alice_answers, bob_answers):
   # Run the whole private matching for one pair of answer lists.
    #Returns the compatibility score that both parties compute.
    
    alice_secrets, alice_values = make_secrets_and_values(alice_answers)
    bob_secrets, bob_values = make_secrets_and_values(bob_answers)

    # Build the circuit using both partiessecret variables.
    expr = build_score_circuit(alice_secrets, bob_secrets)

    # Each party only knows its OWNnn answers.
    parties = {
        "Alice": alice_values,
        "Bob": bob_values,
    }

    participants = list(parties.keys())
    prot = ProtocolSpec(expr=expr, participant_ids=participants)
    clients = [(name, prot, value_dict) for name, value_dict in parties.items()]

    results = run_processes(participants, *clients)

    # Every party computes the same answer, just return the first.
    return results[0]


# --------------------------------------------------------------------------
# A small demo a person can run directly  python custom_app.py
# --------------------------------------------------------------------------

def main():
    # Alice likes: sports, music, travel
    # Bob   likes: sports, travel, gaming
    #            [sports, music, cooking, travel, gaming]
    alice_answers = [1,      1,     0,       1,      0]
    bob_answers   = [1,      0,     0,       1,      1]

    print("Interests:", INTERESTS)
    print("Alice's answers:", alice_answers)
    print("Bob's answers:  ", bob_answers)

    score = run_matching(alice_answers, bob_answers)

    # Turn the score back into a count of shared interests.
    overlap = score // POINTS_PER_MATCH
    threshold_points = THRESHOLD_INTERESTS * POINTS_PER_MATCH

    print(f"Compatibility score: {score}")
    print(f"Shared interests (overlap): {overlap}")
    print(f"Good match needs at least {THRESHOLD_INTERESTS} shared interests.")
    if score >= threshold_points:
        print("Result: It's a match! :)")
    else:
        print("Result: Not enough in common.")


if __name__ == "__main__":
    main()